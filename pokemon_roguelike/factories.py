"""Convenient constructors for player and trainer combatants."""

from __future__ import annotations

import asyncio
import random

from .api import PokeAPIClient
from .models import Inventory, Player, Pokemon, Trainer

PLAYER_ITEMS = {
    "potion": 5,
    "antidote": 2,
    "freeze_heal": 0,
    "paralyze_heal": 0,
    "burn_heal": 0,
    "awakening": 0,
    "poke_ball": 10,
    "great_ball": 0,
    "revive": 3,
}

TRAINER_ITEMS = {
    "potion": 3,
    "antidote": 2,
    "freeze_heal": 0,
    "paralyze_heal": 0,
    "burn_heal": 0,
    "awakening": 0,
    "revive": 0,
}

TRAINER_NAMES = (
    "Avery",
    "Blair",
    "Cameron",
    "Dakota",
    "Emery",
    "Finley",
    "Harper",
    "Jordan",
    "Morgan",
    "Quinn",
    "Riley",
    "Taylor",
)


def create_player(name: str, starter: Pokemon) -> Player:
    return Player(name=name, party=[starter], inventory=Inventory.with_items(PLAYER_ITEMS))


def create_trainer(name: str, party: list[Pokemon]) -> Trainer:
    return Trainer(name=name, party=party, inventory=Inventory.with_items(TRAINER_ITEMS))


async def create_random_trainer(
    client: PokeAPIClient,
    level: int,
    rng: random.Random,
    max_party_size: int = 5,
) -> Trainer:
    """Create a trainer with a random name and appropriately levelled party."""

    if max_party_size < 1:
        raise ValueError("Trainer party size must be at least one")

    pokemon_names = await client.list_pokemon_names()
    party_size = rng.randint(1, min(max_party_size, len(pokemon_names)))
    selected_names = rng.sample(pokemon_names, party_size)
    party = list(
        await asyncio.gather(
            *(client.get_pokemon(name, level=level) for name in selected_names)
        )
    )
    return create_trainer(rng.choice(TRAINER_NAMES), party)
