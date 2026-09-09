"""Reusable turn-based battle rules with no terminal input or network access."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import StrEnum

from .effects import apply_residual_status, apply_status, process_start_of_turn, use_item
from .models import Combatant, Move, Pokemon, StatusCondition
from .type_chart import effectiveness


class Side(StrEnum):
    PLAYER = "player"
    OPPONENT = "opponent"

    @property
    def other(self) -> Side:
        return Side.OPPONENT if self is Side.PLAYER else Side.PLAYER


@dataclass(frozen=True, slots=True)
class BattleEvent:
    """A presentation-neutral description of something that happened."""

    kind: str
    message: str
    amount: int = 0


@dataclass(slots=True)
class Battle:
    """Coordinates a battle while delegating all attacks to one rule path."""

    player: Combatant
    opponent: Combatant
    rng: random.Random = field(default_factory=random.Random)
    player_active_index: int = 0
    opponent_active_index: int = 0

    def __post_init__(self) -> None:
        if self.player.party[0].is_fainted or self.opponent.party[0].is_fainted:
            raise ValueError("The first Pokémon in each party must be able to battle")

    def combatant(self, side: Side) -> Combatant:
        return self.player if side is Side.PLAYER else self.opponent

    def active_pokemon(self, side: Side) -> Pokemon:
        index = (
            self.player_active_index
            if side is Side.PLAYER
            else self.opponent_active_index
        )
        return self.combatant(side).party[index]

    @property
    def winner(self) -> Side | None:
        if self.player.is_defeated:
            return Side.OPPONENT
        if self.opponent.is_defeated:
            return Side.PLAYER
        return None

    def switch(self, side: Side, party_index: int) -> BattleEvent:
        combatant = self.combatant(side)
        current_index = (
            self.player_active_index
            if side is Side.PLAYER
            else self.opponent_active_index
        )
        valid_indices = combatant.healthy_party_indices(excluding=current_index)
        if party_index not in valid_indices:
            raise ValueError("That Pokémon cannot be switched in")

        if side is Side.PLAYER:
            self.player_active_index = party_index
        else:
            self.opponent_active_index = party_index

        pokemon = combatant.party[party_index]
        return BattleEvent("switch", f"{combatant.name} sent out {pokemon.display_name}.")

    def use_item(self, side: Side, item: str, party_index: int | None = None) -> BattleEvent:
        combatant = self.combatant(side)
        if party_index is None:
            target = self.active_pokemon(side)
        else:
            if not 0 <= party_index < len(combatant.party):
                raise ValueError("No Pokémon exists at that party position")
            target = combatant.party[party_index]

        result = use_item(combatant.inventory, item, target)
        return BattleEvent("item", f"{combatant.name} used {item}. {result.message}", result.amount)

    def attack(self, side: Side, move_name: str) -> tuple[BattleEvent, ...]:
        """Resolve an attack for either side using the same game rules."""

        if self.winner is not None:
            raise ValueError("The battle has already ended")

        attacker = self.active_pokemon(side)
        defender = self.active_pokemon(side.other)
        if attacker.is_fainted:
            raise ValueError("A fainted Pokémon must be switched out")
        if move_name not in attacker.moves:
            raise ValueError(f"{attacker.display_name} does not know {move_name}")

        events: list[BattleEvent] = []
        status_turn = process_start_of_turn(attacker, self.rng)
        if status_turn.message:
            events.append(BattleEvent("status", status_turn.message))
        if not status_turn.can_act:
            if status_turn.hurts_self:
                damage = self._confusion_damage(attacker)
                attacker.receive_damage(damage)
                events.append(BattleEvent("damage", f"It dealt {damage} damage.", damage))
                self._append_faint_event(events, attacker)
            return tuple(events)

        move = attacker.moves[move_name]
        move.consume_pp()
        events.append(
            BattleEvent(
                "attack",
                f"{attacker.display_name} used {move.name.replace('-', ' ').title()}.",
            )
        )

        if move.accuracy is not None and self.rng.randint(1, 100) > move.accuracy:
            events.append(BattleEvent("miss", "The attack missed."))
            return tuple(events)

        damage = 0
        if move.is_damaging:
            damage, multiplier, critical = self._calculate_damage(attacker, defender, move)
            defender.receive_damage(damage)
            events.extend(self._damage_events(defender, damage, multiplier, critical))
            self._apply_drain(events, attacker, move, damage)

        self._apply_secondary_effects(events, attacker, defender, move)
        self._append_faint_event(events, defender)
        self._append_faint_event(events, attacker)
        return tuple(events)

    def choose_trainer_move(self) -> str:
        """Choose a usable move without duplicating the attack implementation."""

        pokemon = self.active_pokemon(Side.OPPONENT)
        usable_moves = [move.name for move in pokemon.moves.values() if move.current_pp > 0]
        if not usable_moves:
            raise ValueError(f"{pokemon.display_name} has no usable moves")
        return self.rng.choice(usable_moves)

    def apply_end_of_turn_effects(self, side: Side) -> tuple[BattleEvent, ...]:
        pokemon = self.active_pokemon(side)
        if pokemon.is_fainted:
            return ()
        damage = apply_residual_status(pokemon)
        if damage == 0:
            return ()

        status_name = pokemon.status.value if pokemon.status else "status"
        events = [
            BattleEvent(
                "status_damage",
                f"{pokemon.display_name} took {damage} damage from {status_name}.",
                damage,
            )
        ]
        self._append_faint_event(events, pokemon)
        return tuple(events)

    def _calculate_damage(
        self,
        attacker: Pokemon,
        defender: Pokemon,
        move: Move,
    ) -> tuple[int, float, bool]:
        if not move.is_damaging:
            return 0, 1.0, False

        physical = move.damage_class == "physical"
        attack_stat = "attack" if physical else "special-attack"
        defense_stat = "defense" if physical else "special-defense"
        attack = attacker.effective_stat(attack_stat)
        defense = max(1, defender.effective_stat(defense_stat))

        if physical and attacker.status is StatusCondition.BURNED:
            attack *= 0.5

        critical = self.rng.random() < 0.05
        critical_multiplier = 1.5 if critical else 1.0
        same_type_bonus = 1.5 if move.move_type in attacker.types else 1.0
        type_multiplier = effectiveness(move.move_type, defender.types)
        random_factor = self.rng.uniform(0.85, 1.0)
        base_damage = (((2 * attacker.level / 5 + 2) * move.power * attack / defense) / 50) + 2
        damage = round(
            base_damage
            * critical_multiplier
            * same_type_bonus
            * type_multiplier
            * random_factor
        )
        return max(0, damage), type_multiplier, critical

    def _confusion_damage(self, pokemon: Pokemon) -> int:
        attack = pokemon.effective_stat("attack")
        defense = max(1, pokemon.effective_stat("defense"))
        damage = (((2 * pokemon.level / 5 + 2) * 40 * attack / defense) / 50) + 2
        return max(1, round(damage))

    @staticmethod
    def _damage_events(
        defender: Pokemon,
        damage: int,
        multiplier: float,
        critical: bool,
    ) -> list[BattleEvent]:
        events: list[BattleEvent] = []
        if multiplier == 0:
            events.append(BattleEvent("immune", f"It does not affect {defender.display_name}."))
            return events
        if multiplier > 1:
            events.append(BattleEvent("effectiveness", "It is super effective!"))
        elif multiplier < 1:
            events.append(BattleEvent("effectiveness", "It is not very effective."))
        if critical:
            events.append(BattleEvent("critical", "A critical hit!"))
        events.append(BattleEvent("damage", f"It dealt {damage} damage.", damage))
        return events

    def _apply_secondary_effects(
        self,
        events: list[BattleEvent],
        attacker: Pokemon,
        defender: Pokemon,
        move: Move,
    ) -> None:
        if move.ailment is not None:
            chance = move.ailment_chance or (100 if not move.is_damaging else 0)
            if chance and self.rng.randint(1, 100) <= chance:
                if apply_status(defender, move.ailment, self.rng):
                    events.append(
                        BattleEvent(
                            "status",
                            f"{defender.display_name} became {move.ailment.value}.",
                        )
                    )

        for stat, stages in move.stat_changes.items():
            target = attacker if stages > 0 else defender
            target.change_stat_stage(stat, stages)
            direction = "rose" if stages > 0 else "fell"
            events.append(BattleEvent("stat", f"{target.display_name}'s {stat} {direction}."))

    @staticmethod
    def _apply_drain(
        events: list[BattleEvent],
        attacker: Pokemon,
        move: Move,
        damage: int,
    ) -> None:
        if move.drain_percent > 0:
            healed = attacker.heal(damage * move.drain_percent / 100)
            if healed:
                events.append(
                    BattleEvent("heal", f"{attacker.display_name} restored {healed} HP.", healed)
                )
        elif move.drain_percent < 0:
            recoil = attacker.receive_damage(damage * abs(move.drain_percent) / 100)
            events.append(
                BattleEvent(
                    "recoil",
                    f"{attacker.display_name} took {recoil} recoil damage.",
                    recoil,
                )
            )

    @staticmethod
    def _append_faint_event(events: list[BattleEvent], pokemon: Pokemon) -> None:
        if pokemon.is_fainted:
            events.append(BattleEvent("faint", f"{pokemon.display_name} fainted."))
