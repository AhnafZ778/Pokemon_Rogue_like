"""Procedural wild-encounter selection."""

from __future__ import annotations

import random
from dataclasses import dataclass

from .api import JsonObject, PokeAPIClient
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
    ) -> WildEncounter:
        """Choose a valid location, Pokémon, and level from PokéAPI data."""

        if location_area is None:
            area_data = await self._random_populated_area()
        else:
            area_data = await self._client.get_location_area(location_area)

        encounters = area_data.get("pokemon_encounters", [])
        if not encounters:
            raise ValueError(f"{area_data['name']} has no wild Pokémon encounters")

        encounter = self._rng.choice(encounters)
        details = self._encounter_details(encounter)
        level = self._rng.randint(details["min_level"], details["max_level"])
        pokemon = await self._client.get_pokemon(encounter["pokemon"]["name"], level)
        return WildEncounter(location_name=area_data["name"], pokemon=pokemon)

    async def _random_populated_area(self) -> JsonObject:
        locations = await self._client.list_location_areas()
        attempts = self._rng.sample(locations, k=min(25, len(locations)))
        for location in attempts:
            area_data = await self._client.get_location_area(location["name"])
            if area_data.get("pokemon_encounters"):
                return area_data
        raise ValueError("Could not find a populated location area")

    def _encounter_details(self, encounter: JsonObject) -> JsonObject:
        version_details = encounter.get("version_details", [])
        all_details = [
            detail
            for version in version_details
            for detail in version.get("encounter_details", [])
        ]
        if not all_details:
            raise ValueError("Encounter data does not contain a valid level range")
        return self._rng.choice(all_details)
