"""Terminal interface for a single playable trainer battle."""

from __future__ import annotations

import argparse
import asyncio
import random
from collections.abc import Sequence

from .api import PokeAPIClient, PokeAPIError
from .battle import Battle, BattleAction, BattleEvent, Side
from .factories import create_player, create_random_trainer
from .models import Move, Pokemon, StatusCondition

STARTERS = ("bulbasaur", "charmander", "squirtle")
BATTLE_ITEMS = (
    "potion",
    "antidote",
    "freeze_heal",
    "paralyze_heal",
    "burn_heal",
    "awakening",
    "revive",
)
STATUS_CURE_ITEMS = {
    StatusCondition.POISONED: "antidote",
    StatusCondition.FROZEN: "freeze_heal",
    StatusCondition.PARALYZED: "paralyze_heal",
    StatusCondition.BURNED: "burn_heal",
    StatusCondition.ASLEEP: "awakening",
}


def run() -> None:
    """Parse launcher options and run the terminal game."""

    parser = argparse.ArgumentParser(description="Play the Pokémon terminal roguelike")
    parser.add_argument(
        "--seed",
        type=int,
        help="Use a fixed random seed for a reproducible battle",
    )
    args = parser.parse_args()

    try:
        asyncio.run(play(seed=args.seed))
    except (EOFError, KeyboardInterrupt):
        print("\nGame closed.")
    except PokeAPIError as error:
        print(f"\nCould not start the game: {error}")


async def play(seed: int | None = None) -> Side:
    """Create the combatants and play one complete trainer battle."""

    rng = random.Random(seed)
    print("\n=== POKÉMON ROGUELIKE ===\n")
    player_name = input("Trainer name: ").strip() or "Player"
    starter_name = _choose_starter()

    print("\nPreparing your battle with PokéAPI data...")
    async with PokeAPIClient() as client:
        starter = await client.get_pokemon(starter_name, level=5)
        opponent = await create_random_trainer(
            client,
            level=5,
            rng=rng,
            max_party_size=3,
        )

    player = create_player(player_name, starter)
    battle = Battle(player, opponent, rng=rng)

    print(f"\nTrainer {opponent.name} challenges you!")
    print(f"{opponent.name} sent out {battle.active_pokemon(Side.OPPONENT).display_name}.")
    print(f"Go, {starter.display_name}!\n")

    while battle.winner is None:
        _replace_fainted_pokemon(battle, Side.PLAYER)
        _replace_fainted_pokemon(battle, Side.OPPONENT)
        if battle.winner is not None:
            break

        _print_battle_state(battle)
        player_action = _choose_player_action(battle)
        trainer_action = _choose_trainer_action(battle)
        for side, action in battle.order_actions(player_action, trainer_action):
            _print_events(battle.execute_action(side, action))

        if battle.winner is not None:
            break

        for side in (Side.PLAYER, Side.OPPONENT):
            _print_events(battle.apply_end_of_turn_effects(side))

    winner = battle.winner
    assert winner is not None
    if winner is Side.PLAYER:
        print(f"\n{player.name} defeated Trainer {opponent.name}!")
    else:
        print(f"\nTrainer {opponent.name} won the battle.")
    return winner


def _choose_starter() -> str:
    print("Choose your starter:")
    for index, starter in enumerate(STARTERS, start=1):
        print(f"  {index}. {starter.title()}")
    return STARTERS[_prompt_index("Starter: ", len(STARTERS))]


def _choose_player_action(battle: Battle) -> BattleAction:
    while True:
        actions = ["attack"]
        current_index = battle.player_active_index
        if battle.player.healthy_party_indices(excluding=current_index):
            actions.append("switch")
        if _available_battle_items(battle):
            actions.append("item")

        print("\nChoose an action:")
        for index, action in enumerate(actions, start=1):
            print(f"  {index}. {action.title()}")
        action = actions[_prompt_index("Action: ", len(actions))]

        try:
            if action == "attack":
                return BattleAction.move(_choose_move(battle))
            if action == "switch":
                return BattleAction.switch(_choose_switch(battle))
            item, party_index = _choose_item(battle)
            return BattleAction.item(item, party_index)
        except ValueError as error:
            print(f"That action cannot be used: {error}")


def _choose_trainer_action(battle: Battle) -> BattleAction:
    trainer = battle.opponent
    pokemon = battle.active_pokemon(Side.OPPONENT)

    cure = STATUS_CURE_ITEMS.get(pokemon.status)
    if cure and trainer.inventory.count(cure) > 0:
        return BattleAction.item(cure)

    low_health = pokemon.hp <= pokemon.max_hp * 0.2
    if low_health and trainer.inventory.count("potion") > 0:
        return BattleAction.item("potion")

    return BattleAction.move(battle.choose_trainer_move())


def _choose_move(battle: Battle) -> str:
    pokemon = battle.active_pokemon(Side.PLAYER)
    moves = [move for move in pokemon.moves.values() if move.current_pp > 0]
    if not moves:
        raise ValueError(f"{pokemon.display_name} has no usable moves")

    print("\nChoose a move:")
    for index, move in enumerate(moves, start=1):
        power = move.power if move.power is not None else "--"
        print(
            f"  {index}. {_display_move(move)} "
            f"[{move.move_type.title()} | Power {power} | PP {move.current_pp}/{move.max_pp}]"
        )
    return moves[_prompt_index("Move: ", len(moves))].name


def _choose_switch(battle: Battle) -> int:
    choices = battle.player.healthy_party_indices(excluding=battle.player_active_index)
    print("\nChoose a Pokémon:")
    for display_index, party_index in enumerate(choices, start=1):
        pokemon = battle.player.party[party_index]
        print(f"  {display_index}. {pokemon.display_name} ({pokemon.hp}/{pokemon.max_hp} HP)")
    return choices[_prompt_index("Pokémon: ", len(choices))]


def _choose_item(battle: Battle) -> tuple[str, int | None]:
    available = _available_battle_items(battle)
    print("\nChoose an item:")
    for index, item in enumerate(available, start=1):
        count = battle.player.inventory.count(item)
        print(f"  {index}. {item.replace('_', ' ').title()} x{count}")
    item = available[_prompt_index("Item: ", len(available))]

    if item != "revive":
        return item, None

    fainted_indices = tuple(
        index for index, pokemon in enumerate(battle.player.party) if pokemon.is_fainted
    )
    if not fainted_indices:
        raise ValueError("There are no fainted Pokémon to revive")

    print("\nChoose a Pokémon to revive:")
    for display_index, party_index in enumerate(fainted_indices, start=1):
        print(f"  {display_index}. {battle.player.party[party_index].display_name}")
    selected = fainted_indices[_prompt_index("Pokémon: ", len(fainted_indices))]
    return item, selected


def _available_battle_items(battle: Battle) -> tuple[str, ...]:
    return tuple(
        item
        for item in BATTLE_ITEMS
        if battle.player.inventory.count(item) > 0
    )


def _replace_fainted_pokemon(battle: Battle, side: Side) -> None:
    active = battle.active_pokemon(side)
    if not active.is_fainted or battle.combatant(side).is_defeated:
        return

    choices = battle.combatant(side).healthy_party_indices()
    if side is Side.OPPONENT:
        _print_events((battle.switch(side, battle.rng.choice(choices)),))
        return

    print(f"\n{active.display_name} cannot continue. Choose another Pokémon.")
    for display_index, party_index in enumerate(choices, start=1):
        pokemon = battle.player.party[party_index]
        print(f"  {display_index}. {pokemon.display_name} ({pokemon.hp}/{pokemon.max_hp} HP)")
    selected = choices[_prompt_index("Pokémon: ", len(choices))]
    _print_events((battle.switch(side, selected),))


def _print_battle_state(battle: Battle) -> None:
    player_pokemon = battle.active_pokemon(Side.PLAYER)
    opponent_pokemon = battle.active_pokemon(Side.OPPONENT)
    print(
        f"\n{player_pokemon.display_name}: {player_pokemon.hp}/{player_pokemon.max_hp} HP"
        f"  |  {opponent_pokemon.display_name}: "
        f"{opponent_pokemon.hp}/{opponent_pokemon.max_hp} HP"
    )


def _print_events(events: Sequence[BattleEvent]) -> None:
    for event in events:
        print(event.message)


def _prompt_index(prompt: str, option_count: int) -> int:
    while True:
        response = input(prompt).strip()
        try:
            selected = int(response) - 1
        except ValueError:
            print("Enter the number beside your choice.")
            continue
        if 0 <= selected < option_count:
            return selected
        print(f"Choose a number from 1 to {option_count}.")


def _display_move(move: Move) -> str:
    return move.name.replace("-", " ").title()
