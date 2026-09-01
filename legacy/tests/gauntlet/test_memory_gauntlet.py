"""Headless AI-vs-AI self-play simulation for Memory/Concentration (spec §7.2)."""
from __future__ import annotations

import pytest

from core.ai.base import Difficulty
from games.memory.game import MAX_TURNS, MemoryGame

from .harness import memory_legal_state, write_report

GAMES_PER_MATCHUP = 600
WINRATE_TRIALS = 1200
NUM_PAIRS = 8

MATCHUPS = [
    (Difficulty.HARD, Difficulty.EASY),
    (Difficulty.MEDIUM, Difficulty.EASY),
    (Difficulty.HARD, Difficulty.MEDIUM),
    (Difficulty.EASY, Difficulty.EASY),
]


def simulate(seed: int, d1: Difficulty, d2: Difficulty) -> MemoryGame:
    game = MemoryGame(
        ["A", "B"], num_pairs=NUM_PAIRS, ai_difficulties={"A": d1, "B": d2}, seed=seed
    )
    turns = 0
    while not game.game_over:
        assert memory_legal_state(game), "illegal state reached mid-game"
        game.take_ai_turn()
        turns += 1
        assert turns <= MAX_TURNS + 10, "no hard turn-count ceiling — possible infinite loop"
    assert memory_legal_state(game), "illegal state at game end"
    return game


@pytest.mark.parametrize("d1,d2", MATCHUPS, ids=lambda d: d.value if hasattr(d, "value") else d)
def test_memory_gauntlet_no_crashes_and_legal_states(d1, d2):
    stats = {"wins_a": 0, "wins_b": 0, "ties": 0, "stalemates": 0, "total_turns": 0}
    for seed in range(GAMES_PER_MATCHUP):
        game = simulate(seed, d1, d2)
        assert len(game.matched) == len(game.board) or game.stalemate
        if game.stalemate:
            stats["stalemates"] += 1
        score_a = game.players["A"].score
        score_b = game.players["B"].score
        if score_a > score_b:
            stats["wins_a"] += 1
        elif score_b > score_a:
            stats["wins_b"] += 1
        else:
            stats["ties"] += 1
        stats["total_turns"] += game.turn_count

    stats["games"] = GAMES_PER_MATCHUP
    stats["avg_turns"] = stats["total_turns"] / GAMES_PER_MATCHUP
    stats["stalemate_rate"] = stats["stalemates"] / GAMES_PER_MATCHUP
    write_report(f"memory_{d1.value}_vs_{d2.value}", {"matchup": f"{d1.value} vs {d2.value}", **stats})
    assert stats["stalemate_rate"] < 0.05


def test_memory_hard_beats_easy_more_often_but_is_still_beatable():
    stats = {"wins_hard": 0, "wins_easy": 0, "ties": 0}
    for seed in range(WINRATE_TRIALS):
        game = simulate(seed, Difficulty.HARD, Difficulty.EASY)
        score_hard = game.players["A"].score
        score_easy = game.players["B"].score
        if score_hard > score_easy:
            stats["wins_hard"] += 1
        elif score_easy > score_hard:
            stats["wins_easy"] += 1
        else:
            stats["ties"] += 1

    stats["trials"] = WINRATE_TRIALS
    stats["hard_winrate"] = stats["wins_hard"] / WINRATE_TRIALS
    stats["easy_winrate"] = stats["wins_easy"] / WINRATE_TRIALS
    write_report("memory_hard_vs_easy_winrate", stats)

    assert stats["wins_hard"] > stats["wins_easy"], "Hard should beat Easy more often than chance"
    assert stats["wins_easy"] > 0, "Easy must still win sometimes -- Hard must not be unbeatable"
