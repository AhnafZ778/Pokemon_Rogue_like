"""Async PokéAPI client and translation into game-domain models."""

from __future__ import annotations

import asyncio
from collections import defaultdict
from types import TracebackType
from typing import Any, Self

import aiohttp

from .models import Move, Pokemon, StatusCondition, calculate_battle_stats, moves_by_name

JsonObject = dict[str, Any]


class PokeAPIError(RuntimeError):
    """Raised when PokéAPI data cannot be fetched or interpreted."""


class PokeAPIClient:
    """A reusable PokéAPI session with bounded request concurrency."""

    BASE_URL = "https://pokeapi.co/api/v2/"

    def __init__(self, timeout_seconds: float = 20, max_concurrency: int = 20) -> None:
        self._timeout = aiohttp.ClientTimeout(total=timeout_seconds)
        self._semaphore = asyncio.Semaphore(max_concurrency)
        self._session: aiohttp.ClientSession | None = None

    async def __aenter__(self) -> Self:
        self._session = aiohttp.ClientSession(timeout=self._timeout)
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        if self._session is not None:
            await self._session.close()
            self._session = None

    async def get_pokemon(self, identifier: str | int, level: int = 5) -> Pokemon:
        """Build a battle-ready Pokémon from API data."""

        pokemon_data = await self._get_json(f"pokemon/{str(identifier).lower()}")
        species_data = await self._get_json(pokemon_data["species"]["url"])

        move_entries = self._level_up_move_entries(pokemon_data["moves"])
        move_data = await asyncio.gather(
            *(self._get_json(entry["url"]) for entry in move_entries.values())
        )
        parsed_moves = {
            name: self._parse_move(data)
            for name, data in zip(move_entries, move_data, strict=True)
        }

        learnset_lists: defaultdict[int, list[Move]] = defaultdict(list)
        for name, entry in move_entries.items():
            learnset_lists[entry["level"]].append(parsed_moves[name])
        learnset = {
            move_level: tuple(moves)
            for move_level, moves in sorted(learnset_lists.items())
        }

        known_moves = [
            (entry["level"], parsed_moves[name])
            for name, entry in move_entries.items()
            if entry["level"] <= level
        ]
        known_moves.sort(key=lambda item: (item[0], item[1].name))
        starting_moves = moves_by_name(move for _, move in known_moves[-4:])

        growth_data = await self._get_json(species_data["growth_rate"]["url"])
        growth_curve = {
            entry["level"]: entry["experience"]
            for entry in growth_data["levels"]
        }
        base_stats = {
            entry["stat"]["name"]: entry["base_stat"]
            for entry in pokemon_data["stats"]
        }
        types = tuple(
            entry["type"]["name"]
            for entry in sorted(pokemon_data["types"], key=lambda entry: entry["slot"])
        )
        abilities = pokemon_data.get("abilities", [])
        ability = abilities[0]["ability"]["name"] if abilities else None
        sprites = pokemon_data.get("sprites") or {}

        return Pokemon(
            name=pokemon_data["name"],
            level=level,
            base_experience=pokemon_data.get("base_experience") or 0,
            stats=calculate_battle_stats(base_stats, level),
            types=types,
            moves=starting_moves,
            base_stats=base_stats,
            learnset=learnset,
            growth_curve=growth_curve,
            ability=ability,
            front_sprite_url=sprites.get("front_default"),
            back_sprite_url=sprites.get("back_default"),
            experience=growth_curve.get(level, 0),
        )

    async def get_location_area(self, identifier: str | int) -> JsonObject:
        return await self._get_json(f"location-area/{identifier}")

    async def list_location_areas(self) -> tuple[JsonObject, ...]:
        data = await self._get_json("location-area?limit=10000")
        return tuple(data["results"])

    async def list_pokemon_names(self, limit: int = 1025) -> tuple[str, ...]:
        data = await self._get_json(f"pokemon?limit={limit}")
        return tuple(entry["name"] for entry in data["results"])

    async def get_bytes(self, resource: str) -> bytes:
        """Fetch a binary resource, such as a sprite image."""

        if self._session is None:
            raise RuntimeError("PokeAPIClient must be used as an async context manager")

        try:
            async with self._semaphore, self._session.get(resource) as response:
                response.raise_for_status()
                return await response.read()
        except (aiohttp.ClientError, asyncio.TimeoutError) as error:
            raise PokeAPIError(f"Could not retrieve {resource}: {error}") from error

    async def _get_json(self, resource: str) -> JsonObject:
        if self._session is None:
            raise RuntimeError("PokeAPIClient must be used as an async context manager")

        url = resource if resource.startswith("http") else f"{self.BASE_URL}{resource}"
        try:
            async with self._semaphore, self._session.get(url) as response:
                response.raise_for_status()
                return await response.json()
        except (aiohttp.ClientError, asyncio.TimeoutError, ValueError) as error:
            raise PokeAPIError(f"Could not retrieve {url}: {error}") from error

    @staticmethod
    def _level_up_move_entries(entries: list[JsonObject]) -> dict[str, JsonObject]:
        result: dict[str, JsonObject] = {}
        for entry in entries:
            levels = [
                detail["level_learned_at"]
                for detail in entry["version_group_details"]
                if detail["move_learn_method"]["name"] == "level-up"
                and detail["level_learned_at"] > 0
            ]
            if not levels:
                continue
            result[entry["move"]["name"]] = {
                "url": entry["move"]["url"],
                "level": min(levels),
            }
        return result

    @staticmethod
    def _parse_move(data: JsonObject) -> Move:
        meta = data.get("meta") or {}
        ailment_data = meta.get("ailment") or {}
        stat_changes = {
            entry["stat"]["name"]: entry["change"]
            for entry in data.get("stat_changes", [])
        }
        return Move(
            name=data["name"],
            move_type=data["type"]["name"],
            damage_class=data["damage_class"]["name"],
            power=data.get("power"),
            accuracy=data.get("accuracy"),
            max_pp=data.get("pp") or 0,
            priority=data.get("priority", 0),
            ailment=StatusCondition.from_api_name(ailment_data.get("name")),
            ailment_chance=meta.get("ailment_chance") or 0,
            stat_changes=stat_changes,
            drain_percent=meta.get("drain") or 0,
        )
