# Pokémon Roguelike

A graphical Pokémon roguelike with a terminal-inspired interface, powered by
live data from [PokéAPI](https://pokeapi.co/).

This project began as a fourth-semester API and Python learning project. It is
now being modernized into a focused, replayable game while preserving the
direct, handmade character of the original terminal experience.

## Current architecture

```text
PokéAPI ──► api.py ──► models.py ◄── factories.py
                │          │
                ▼          ▼
          encounters.py    battle.py ──► gui.py ──► ascii_art.py
                           │
                           ├──► effects.py
                           └──► type_chart.py
```

- `models.py` contains game state and has no network or terminal dependencies.
- `api.py` owns HTTP communication and translates JSON into domain objects.
- `battle.py` resolves player and opponent actions through shared rules.
- `effects.py` contains item and status-condition behavior.
- `encounters.py` selects valid wild encounters from location data.
- `factories.py` creates players and randomized trainers with consistent defaults.
- `ascii_art.py` converts transparent PokéAPI sprites into colored glyph grids.
- `gui.py` presents the game through a Pygame-powered terminal-style window.

## Setup

Python 3.11 or newer is required.

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
```

## Start the game

Run the root launcher:

```bash
python3 main.py
```

The starter screen and battle now open in a graphical window. Mouse clicks and
number keys can both select commands.

The package and installed-command forms are also available:

```bash
python3 -m pokemon_roguelike
pokemon-roguelike
```

Pass `--seed 42` to any launcher for a reproducible opponent and battle.
Use `python3 main.py --terminal` to play through the original plain terminal UI.

The phased interface and gameplay roadmap is documented in
[`docs/GRAPHICAL_MIGRATION.md`](docs/GRAPHICAL_MIGRATION.md).

## Loading a Pokémon

```python
import asyncio

from pokemon_roguelike.api import PokeAPIClient


async def main() -> None:
    async with PokeAPIClient() as client:
        pokemon = await client.get_pokemon("pikachu", level=5)
        print(pokemon.display_name, pokemon.moves)


asyncio.run(main())
```

The graphical launcher currently plays one complete trainer battle. Run
progression, rewards, capture flow, and additional encounter types are the next
product-level features.

## Project history

The original prototype explored API requests, JSON parsing, object-oriented
Python, turn-based combat, and concurrent move retrieval. Moving move requests
to `asyncio` reduced startup time dramatically and remains part of the current
client design.

Pokémon and related names are trademarks of Nintendo, Game Freak, and Creatures.
This is an unofficial, non-commercial fan project.
