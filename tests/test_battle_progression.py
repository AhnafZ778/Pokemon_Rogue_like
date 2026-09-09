from __future__ import annotations

import random
import unittest

from pokemon_roguelike.battle import Battle, BattleAction, Side
from pokemon_roguelike.encounter_tiers import (
    BEGINNER_POKEMON,
    LEGENDARY_POKEMON,
    MIDGAME_POKEMON,
    PSEUDO_BASES,
    choose_opponent_names,
    trainer_party_size,
)
from pokemon_roguelike.models import (
    Move,
    Pokemon,
    Trainer,
    calculate_battle_stats,
    moves_by_name,
)


def pokemon(name: str, speed: int, move: Move) -> Pokemon:
    return Pokemon(
        name=name,
        level=5,
        base_experience=50,
        stats={
            "hp": 20,
            "attack": 12,
            "defense": 10,
            "special-attack": 10,
            "special-defense": 10,
            "speed": speed,
        },
        types=("normal",),
        moves=moves_by_name((move,)),
    )


def move(name: str, priority: int = 0) -> Move:
    return Move(name, "normal", "physical", 40, 100, 20, priority=priority)


class BattleProgressionTests(unittest.TestCase):
    def test_speed_and_move_priority_order_declared_actions(self) -> None:
        player = Trainer("Player", [pokemon("slow", 8, move("quick", priority=1))])
        opponent = Trainer("Rival", [pokemon("fast", 20, move("tackle"))])
        battle = Battle(player, opponent, rng=random.Random(3))

        ordered = battle.order_actions(
            BattleAction.move("quick"),
            BattleAction.move("tackle"),
        )
        self.assertEqual(ordered[0][0], Side.PLAYER)

        player.party[0].moves = moves_by_name((move("tackle"),))
        ordered = battle.order_actions(
            BattleAction.move("tackle"),
            BattleAction.move("tackle"),
        )
        self.assertEqual(ordered[0][0], Side.OPPONENT)

    def test_opening_encounters_only_use_beginner_pool(self) -> None:
        names = choose_opponent_names(5, 20, random.Random(11))
        self.assertTrue(set(names).issubset(BEGINNER_POKEMON))
        self.assertTrue(set(names).isdisjoint(PSEUDO_BASES + LEGENDARY_POKEMON))

    def test_powerful_tiers_have_hard_level_gates(self) -> None:
        self.assertTrue(set(MIDGAME_POKEMON).isdisjoint(PSEUDO_BASES))
        level_35 = {
            choose_opponent_names(35, 1, random.Random(seed))[0]
            for seed in range(100)
        }
        level_50 = {
            choose_opponent_names(50, 1, random.Random(seed))[0]
            for seed in range(100)
        }

        self.assertTrue(level_35.intersection(PSEUDO_BASES))
        self.assertTrue(level_35.isdisjoint(LEGENDARY_POKEMON))
        self.assertTrue(level_50.intersection(LEGENDARY_POKEMON))

    def test_trainer_parties_scale_with_level(self) -> None:
        self.assertEqual(trainer_party_size(5, 5), 1)
        self.assertEqual(trainer_party_size(35, 5), 3)
        self.assertEqual(trainer_party_size(65, 5), 5)

    def test_api_base_stats_are_scaled_to_level(self) -> None:
        stats = calculate_battle_stats({"hp": 44, "speed": 43}, level=5)
        self.assertEqual(stats, {"speed": 10, "hp": 20})


if __name__ == "__main__":
    unittest.main()
