"""Domain models used by the game engine.

These classes intentionally contain no terminal input and perform no network
requests. That keeps game state predictable and lets other interfaces reuse the
same rules later.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass, field
from enum import StrEnum


class StatusCondition(StrEnum):
    """Status conditions currently supported by the battle engine."""

    PARALYZED = "paralyzed"
    POISONED = "poisoned"
    FROZEN = "frozen"
    BURNED = "burned"
    ASLEEP = "asleep"
    CONFUSED = "confused"

    @classmethod
    def from_api_name(cls, name: str | None) -> StatusCondition | None:
        aliases = {
            "paralysis": cls.PARALYZED,
            "poison": cls.POISONED,
            "freeze": cls.FROZEN,
            "burn": cls.BURNED,
            "sleep": cls.ASLEEP,
            "confusion": cls.CONFUSED,
        }
        return aliases.get(name or "")


@dataclass(slots=True)
class Move:
    """A move known by a Pokémon, including its mutable PP."""

    name: str
    move_type: str
    damage_class: str
    power: int | None
    accuracy: int | None
    max_pp: int
    priority: int = 0
    ailment: StatusCondition | None = None
    ailment_chance: int = 0
    stat_changes: dict[str, int] = field(default_factory=dict)
    drain_percent: int = 0
    current_pp: int = field(init=False)

    def __post_init__(self) -> None:
        self.current_pp = self.max_pp

    @property
    def is_damaging(self) -> bool:
        return self.power is not None and self.power > 0

    def consume_pp(self) -> None:
        if self.current_pp <= 0:
            raise ValueError(f"{self.name} has no PP remaining")
        self.current_pp -= 1


@dataclass(slots=True)
class Pokemon:
    """Runtime state for one Pokémon."""

    name: str
    level: int
    base_experience: int
    stats: dict[str, int]
    types: tuple[str, ...]
    moves: dict[str, Move]
    learnset: dict[int, tuple[Move, ...]] = field(default_factory=dict)
    growth_curve: dict[int, int] = field(default_factory=dict)
    ability: str | None = None
    front_sprite_url: str | None = None
    back_sprite_url: str | None = None
    experience: int = 0
    status: StatusCondition | None = None
    status_turns: int = 0
    stat_stages: dict[str, int] = field(default_factory=dict)
    hp: int = field(init=False)

    def __post_init__(self) -> None:
        if not 1 <= self.level <= 100:
            raise ValueError("Pokémon level must be between 1 and 100")
        if "hp" not in self.stats:
            raise ValueError("Pokémon stats must include hp")
        if not self.types:
            raise ValueError("Pokémon must have at least one type")
        self.hp = self.max_hp

    @property
    def display_name(self) -> str:
        return self.name.replace("-", " ").title()

    @property
    def max_hp(self) -> int:
        return self.stats["hp"]

    @property
    def is_fainted(self) -> bool:
        return self.hp <= 0

    def receive_damage(self, amount: float) -> int:
        damage = max(0, round(amount))
        self.hp = max(0, self.hp - damage)
        return damage

    def heal(self, amount: float) -> int:
        if self.is_fainted:
            return 0
        previous_hp = self.hp
        self.hp = min(self.max_hp, self.hp + max(0, round(amount)))
        return self.hp - previous_hp

    def revive(self, health_fraction: float = 0.5) -> int:
        if not self.is_fainted:
            return 0
        self.hp = max(1, round(self.max_hp * health_fraction))
        self.status = None
        self.status_turns = 0
        return self.hp

    def change_stat_stage(self, stat: str, stages: int) -> int:
        current = self.stat_stages.get(stat, 0)
        updated = max(-6, min(6, current + stages))
        self.stat_stages[stat] = updated
        return updated

    def effective_stat(self, stat: str) -> float:
        base_value = self.stats[stat]
        stage = self.stat_stages.get(stat, 0)
        multiplier = (2 + stage) / 2 if stage >= 0 else 2 / (2 - stage)
        return base_value * multiplier

    def gain_experience(self, amount: int) -> tuple[Move, ...]:
        """Apply experience and return moves unlocked by any gained levels."""

        if amount < 0:
            raise ValueError("Experience gained cannot be negative")

        self.experience += amount
        unlocked: list[Move] = []
        while self.level < 100:
            next_level = self.level + 1
            threshold = self.growth_curve.get(next_level)
            if threshold is None or self.experience < threshold:
                break
            self.level = next_level
            unlocked.extend(self.learnset.get(next_level, ()))
        return tuple(unlocked)

    def learn_move(self, move: Move, replace: str | None = None) -> None:
        if move.name in self.moves:
            return
        if len(self.moves) >= 4:
            if replace is None or replace not in self.moves:
                raise ValueError("A known move must be selected for replacement")
            del self.moves[replace]
        self.moves[move.name] = move


@dataclass(slots=True)
class Inventory:
    """Counted collection of item identifiers."""

    quantities: dict[str, int] = field(default_factory=dict)

    @classmethod
    def with_items(cls, items: Mapping[str, int]) -> Inventory:
        return cls(dict(items))

    def count(self, item: str) -> int:
        return self.quantities.get(item, 0)

    def available_items(self) -> tuple[str, ...]:
        return tuple(item for item, count in self.quantities.items() if count > 0)

    def consume(self, item: str) -> None:
        if self.count(item) <= 0:
            raise ValueError(f"No {item} remaining")
        self.quantities[item] -= 1


@dataclass(slots=True)
class Combatant:
    """Something that owns a party and can participate in battle."""

    name: str
    party: list[Pokemon]
    inventory: Inventory = field(default_factory=Inventory)

    def __post_init__(self) -> None:
        if not self.party:
            raise ValueError("A combatant must have at least one Pokémon")

    @property
    def available_pokemon(self) -> tuple[Pokemon, ...]:
        return tuple(pokemon for pokemon in self.party if not pokemon.is_fainted)

    @property
    def is_defeated(self) -> bool:
        return not self.available_pokemon

    def healthy_party_indices(self, excluding: int | None = None) -> tuple[int, ...]:
        return tuple(
            index
            for index, pokemon in enumerate(self.party)
            if index != excluding and not pokemon.is_fainted
        )


@dataclass(slots=True)
class Player(Combatant):
    """A human-controlled combatant."""


@dataclass(slots=True)
class Trainer(Combatant):
    """A computer-controlled combatant."""


def moves_by_name(moves: Iterable[Move]) -> dict[str, Move]:
    """Create the mapping used by a Pokémon while rejecting duplicates."""

    result: dict[str, Move] = {}
    for move in moves:
        if move.name in result:
            raise ValueError(f"Duplicate move: {move.name}")
        result[move.name] = move
    return result
