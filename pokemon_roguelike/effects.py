"""Status-condition and item effects.

The battle engine calls these functions but does not need to know how an item
or status works internally.
"""

from __future__ import annotations

import random
from dataclasses import dataclass

from .models import Inventory, Pokemon, StatusCondition


@dataclass(frozen=True, slots=True)
class StatusTurn:
    can_act: bool
    message: str | None = None
    hurts_self: bool = False


@dataclass(frozen=True, slots=True)
class ItemResult:
    item: str
    message: str
    amount: int = 0


STATUS_CURES: dict[str, StatusCondition] = {
    "antidote": StatusCondition.POISONED,
    "paralyze_heal": StatusCondition.PARALYZED,
    "freeze_heal": StatusCondition.FROZEN,
    "burn_heal": StatusCondition.BURNED,
    "awakening": StatusCondition.ASLEEP,
}


def apply_status(
    pokemon: Pokemon,
    status: StatusCondition,
    rng: random.Random,
) -> bool:
    """Apply a status if the target does not already have one."""

    if pokemon.status is not None or pokemon.is_fainted:
        return False

    pokemon.status = status
    if status is StatusCondition.ASLEEP:
        pokemon.status_turns = rng.randint(1, 3)
    elif status is StatusCondition.CONFUSED:
        pokemon.status_turns = rng.randint(2, 5)
    return True


def process_start_of_turn(pokemon: Pokemon, rng: random.Random) -> StatusTurn:
    """Resolve conditions that may prevent a Pokémon from acting."""

    status = pokemon.status
    if status is None:
        return StatusTurn(can_act=True)

    if status is StatusCondition.PARALYZED and rng.random() < 0.25:
        return StatusTurn(False, f"{pokemon.display_name} is fully paralyzed.")

    if status is StatusCondition.FROZEN:
        if rng.random() < 0.20:
            pokemon.status = None
            return StatusTurn(True, f"{pokemon.display_name} thawed out.")
        return StatusTurn(False, f"{pokemon.display_name} is frozen solid.")

    if status is StatusCondition.ASLEEP:
        pokemon.status_turns -= 1
        if pokemon.status_turns <= 0:
            pokemon.status = None
            return StatusTurn(True, f"{pokemon.display_name} woke up.")
        return StatusTurn(False, f"{pokemon.display_name} is asleep.")

    if status is StatusCondition.CONFUSED:
        pokemon.status_turns -= 1
        if pokemon.status_turns <= 0:
            pokemon.status = None
            return StatusTurn(True, f"{pokemon.display_name} snapped out of confusion.")
        if rng.random() < 1 / 3:
            return StatusTurn(
                False,
                f"{pokemon.display_name} hurt itself in confusion.",
                hurts_self=True,
            )

    return StatusTurn(can_act=True)


def apply_residual_status(pokemon: Pokemon) -> int:
    """Apply end-of-turn poison or burn damage and return the damage dealt."""

    divisor = {
        StatusCondition.POISONED: 8,
        StatusCondition.BURNED: 16,
    }.get(pokemon.status)
    if divisor is None:
        return 0
    return pokemon.receive_damage(max(1, pokemon.max_hp // divisor))


def use_item(inventory: Inventory, item: str, target: Pokemon) -> ItemResult:
    """Use one item, consuming it only when it has an effect."""

    if inventory.count(item) <= 0:
        raise ValueError(f"No {item} remaining")

    if item == "potion":
        healed = target.heal(20)
        if healed == 0:
            raise ValueError("Potion would have no effect")
        result = ItemResult(item, f"{target.display_name} recovered {healed} HP.", healed)
    elif item == "revive":
        restored = target.revive()
        if restored == 0:
            raise ValueError("Revive can only be used on a fainted Pokémon")
        result = ItemResult(
            item,
            f"{target.display_name} was revived with {restored} HP.",
            restored,
        )
    elif item in STATUS_CURES:
        if target.status is not STATUS_CURES[item]:
            raise ValueError(f"{item} would have no effect")
        target.status = None
        target.status_turns = 0
        result = ItemResult(item, f"{target.display_name}'s status was cured.")
    else:
        raise ValueError(f"Unsupported battle item: {item}")

    inventory.consume(item)
    return result
