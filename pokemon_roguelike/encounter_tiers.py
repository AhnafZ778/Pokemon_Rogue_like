"""Curated difficulty gates for trainer encounters.

PokéAPI's national Pokédex list is ordered, not difficulty-rated. These pools
make progression intentional and keep powerful species out of opening battles.
"""

from __future__ import annotations

import random

BEGINNER_POKEMON = (
    "caterpie",
    "weedle",
    "pidgey",
    "rattata",
    "spearow",
    "zubat",
    "oddish",
    "paras",
    "venonat",
    "sentret",
    "hoothoot",
    "ledyba",
    "spinarak",
    "hoppip",
    "wooper",
    "poochyena",
    "zigzagoon",
    "wurmple",
    "taillow",
    "shroomish",
    "whismur",
    "starly",
    "bidoof",
    "kricketot",
    "patrat",
    "lillipup",
    "purrloin",
    "pidove",
    "sewaddle",
    "bunnelby",
    "fletchling",
    "scatterbug",
    "pikipek",
    "yungoos",
    "grubbin",
    "skwovet",
    "rookidee",
    "blipbug",
    "lechonk",
    "tarountula",
    "nymble",
)

EARLY_POKEMON = (
    "sandshrew",
    "nidoran-f",
    "nidoran-m",
    "bellsprout",
    "geodude",
    "magnemite",
    "drowzee",
    "chinchou",
    "mareep",
    "swinub",
    "seedot",
    "lotad",
    "wingull",
    "makuhita",
    "aron",
    "electrike",
    "buizel",
    "shellos",
    "drilbur",
    "venipede",
    "sandile",
    "ducklett",
    "litleo",
    "skiddo",
    "mudbray",
    "stufful",
    "chewtle",
    "yamper",
    "pawmi",
    "smoliv",
)

MIDGAME_POKEMON = (
    "fearow",
    "golbat",
    "graveler",
    "haunter",
    "rhyhorn",
    "magmar",
    "electabuzz",
    "noctowl",
    "lanturn",
    "heracross",
    "mightyena",
    "lombre",
    "nuzleaf",
    "vibrava",
    "luxio",
    "floatzel",
    "excadrill",
    "krookodile",
    "sawsbuck",
    "talonflame",
    "hawlucha",
    "mudsdale",
    "corviknight",
    "drednaw",
    "lokix",
    "kilowattrel",
)

PSEUDO_BASES = (
    "dratini",
    "larvitar",
    "bagon",
    "beldum",
    "gible",
    "deino",
    "goomy",
    "jangmo-o",
    "dreepy",
    "frigibax",
)

PSEUDO_MIDDLES = (
    "dragonair",
    "pupitar",
    "shelgon",
    "metang",
    "gabite",
    "zweilous",
    "sliggoo",
    "hakamo-o",
    "drakloak",
    "arctibax",
)

PSEUDO_FINALS = (
    "dragonite",
    "tyranitar",
    "salamence",
    "metagross",
    "garchomp",
    "hydreigon",
    "goodra",
    "kommo-o",
    "dragapult",
    "baxcalibur",
)

LEGENDARY_POKEMON = (
    "articuno",
    "zapdos",
    "moltres",
    "raikou",
    "entei",
    "suicune",
    "regirock",
    "regice",
    "registeel",
    "uxie",
    "mesprit",
    "azelf",
    "cobalion",
    "terrakion",
    "virizion",
    "tornadus-incarnate",
    "thundurus-incarnate",
    "landorus-incarnate",
    "tapu-koko",
    "tapu-lele",
    "tapu-bulu",
    "tapu-fini",
)


def trainer_party_size(level: int, maximum: int) -> int:
    """Grow opposing parties slowly enough for the player's collection to keep up."""

    if maximum < 1:
        raise ValueError("Trainer party size must be at least one")
    suggested = 1 + (level >= 15) + (level >= 30) + (level >= 45) + (level >= 60)
    return min(maximum, suggested)


def choose_opponent_names(
    level: int,
    count: int,
    rng: random.Random,
) -> tuple[str, ...]:
    """Choose distinct opponents with pseudo and legendary level gates."""

    if level < 1:
        raise ValueError("Encounter level must be positive")
    if count < 1:
        raise ValueError("At least one opponent must be selected")

    if level < 12:
        regular_pool = BEGINNER_POKEMON
    elif level < 25:
        regular_pool = BEGINNER_POKEMON + EARLY_POKEMON
    elif level < 35:
        regular_pool = EARLY_POKEMON + MIDGAME_POKEMON
    else:
        regular_pool = MIDGAME_POKEMON

    pseudo_pool: tuple[str, ...] = ()
    if level >= 35:
        pseudo_pool += PSEUDO_BASES
    if level >= 45:
        pseudo_pool += PSEUDO_MIDDLES
    if level >= 55:
        pseudo_pool += PSEUDO_FINALS

    selected: list[str] = []
    while len(selected) < count:
        roll = rng.random()
        if level >= 50 and roll < 0.10:
            pool = LEGENDARY_POKEMON
        elif pseudo_pool and roll < 0.30:
            pool = pseudo_pool
        else:
            pool = regular_pool
        available = tuple(name for name in pool if name not in selected)
        if not available:
            available = tuple(name for name in regular_pool if name not in selected)
        selected.append(rng.choice(available))
    return tuple(selected)


def minimum_encounter_level(name: str) -> int:
    """Return the first player level at which a curated species may appear."""

    if name in BEGINNER_POKEMON:
        return 1
    if name in EARLY_POKEMON:
        return 12
    if name in MIDGAME_POKEMON:
        return 25
    if name in PSEUDO_BASES:
        return 35
    if name in PSEUDO_MIDDLES:
        return 45
    if name in LEGENDARY_POKEMON:
        return 50
    if name in PSEUDO_FINALS:
        return 55
    return 25


def is_eligible_opponent(name: str, player_level: int) -> bool:
    return player_level >= minimum_encounter_level(name)
