"""Procedural wild-encounter selection."""

from __future__ import annotations

import random
from dataclasses import dataclass

from .api import JsonObject, PokeAPIClient
from .encounter_tiers import is_eligible_opponent
from .models import Pokemon


@dataclass(frozen=True, slots=True)
class WildEncounter:
    location_name: str
    pokemon: Pokemon


class EncounterGenerator:
    def __init__(self, client: PokeAPIClient, rng: random.Random | None = None) -> None:
        self._client = client
        self._rng = rng or random.Random()

    async def random_wild_encounter(
        self,
        location_area: str | int | None = None,
        player_level: int = 5,
    ) -> WildEncounter:
        """Choose a valid wild Pokémon close to the player's current level."""

        if location_area is None:
            area_data = await self._random_populated_area(player_level)
        else:
            area_data = await self._client.get_location_area(location_area)

        encounters = [
            encounter
            for encounter in area_data.get("pokemon_encounters", [])
            if is_eligible_opponent(encounter["pokemon"]["name"], player_level)
        ]
        if not encounters:
            raise ValueError(
                f"{area_data['name']} has no encounters suitable for level {player_level}"
            )

        encounter = self._rng.choice(encounters)
        level = self._rng.randint(max(1, player_level - 2), min(100, player_level + 2))
        pokemon = await self._client.get_pokemon(encounter["pokemon"]["name"], level)
        return WildEncounter(location_name=area_data["name"], pokemon=pokemon)

    async def _random_populated_area(self, player_level: int) -> JsonObject:
        locations = await self._client.list_location_areas()
        attempts = self._rng.sample(locations, k=min(25, len(locations)))
        for location in attempts:
            area_data = await self._client.get_location_area(location["name"])
            if any(
                is_eligible_opponent(encounter["pokemon"]["name"], player_level)
                for encounter in area_data.get("pokemon_encounters", [])
            ):
                return area_data
        raise ValueError("Could not find a populated location area")
