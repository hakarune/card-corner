"""Headless AI-vs-AI self-play simulation for Go Fish (spec §7.2)."""
from __future__ import annotations

import pytest

from core.ai.base import Difficulty
from games.go_fish.game import MAX_TURNS, GoFishGame

from .harness import go_fish_legal_state, write_report

GAMES_PER_MATCHUP = 600
WINRATE_TRIALS = 1200

MATCHUPS = [
    (Difficulty.HARD, Difficulty.EASY),
    (Difficulty.MEDIUM, Difficulty.EASY),
    (Difficulty.HARD, Difficulty.MEDIUM),
    (Difficulty.EASY, Difficulty.EASY),
]


def simulate(seed: int, d1: Difficulty, d2: Difficulty) -> GoFishGame:
    game = GoFishGame(["A", "B"], ai_difficulties={"A": d1, "B": d2}, seed=seed)
    turns = 0
    while not game.game_over:
        assert go_fish_legal_state(game), "illegal state reached mid-game"
        game.take_ai_turn()
        turns += 1
        # Hard ceiling independent of the engine's own MAX_TURNS: if this
        # ever trips, the engine's internal stalemate detection itself is
        # broken (it should have already set game_over by MAX_TURNS).
        assert turns <= MAX_TURNS + 10, "no hard turn-count ceiling — possible infinite loop"
    assert go_fish_legal_state(game), "illegal state at game end"
    return game


@pytest.mark.parametrize("d1,d2", MATCHUPS, ids=lambda d: d.value if hasattr(d, "value") else d)
def test_go_fish_gauntlet_no_crashes_and_legal_states(d1, d2):
    stats = {"wins_a": 0, "wins_b": 0, "ties": 0, "stalemates": 0, "total_turns": 0}
    for seed in range(GAMES_PER_MATCHUP):
        game = simulate(seed, d1, d2)
        if game.stalemate:
            stats["stalemates"] += 1
        if game.winner == "A":
            stats["wins_a"] += 1
        elif game.winner == "B":
            stats["wins_b"] += 1
        else:
            stats["ties"] += 1
        stats["total_turns"] += game.turn_count

    stats["games"] = GAMES_PER_MATCHUP
    stats["avg_turns"] = stats["total_turns"] / GAMES_PER_MATCHUP
    stats["stalemate_rate"] = stats["stalemates"] / GAMES_PER_MATCHUP
    write_report(f"go_fish_{d1.value}_vs_{d2.value}", {"matchup": f"{d1.value} vs {d2.value}", **stats})

    # Convergence sanity: real Go Fish games between reasonable AIs should
    # essentially never hit the stalemate ceiling.
    assert stats["stalemate_rate"] < 0.05


def test_go_fish_hard_beats_easy_more_often_but_is_still_beatable():
    stats = {"wins_hard": 0, "wins_easy": 0, "ties": 0}
    for seed in range(WINRATE_TRIALS):
        game = simulate(seed, Difficulty.HARD, Difficulty.EASY)
        if game.winner == "A":
            stats["wins_hard"] += 1
        elif game.winner == "B":
            stats["wins_easy"] += 1
        else:
            stats["ties"] += 1

    stats["trials"] = WINRATE_TRIALS
    stats["hard_winrate"] = stats["wins_hard"] / WINRATE_TRIALS
    stats["easy_winrate"] = stats["wins_easy"] / WINRATE_TRIALS
    write_report("go_fish_hard_vs_easy_winrate", stats)

    assert stats["wins_hard"] > stats["wins_easy"], "Hard should beat Easy more often than chance"
    assert stats["wins_easy"] > 0, "Easy must still win sometimes -- Hard must not be unbeatable"


def test_go_fish_medium_beats_easy_on_average():
    # MEDIUM's real edge over EASY comes from GoFishStrategy._base_weight:
    # preferring to ask about ranks with *more* copies still unseen
    # elsewhere (a higher hit rate), plus never repeating a same-turn
    # certain miss. Both effects are real and measurable here. HARD vs
    # MEDIUM specifically is *not* asserted: they share the same qualitative
    # heuristics, just at different exponents/discounts, and empirically
    # (checked across several independent seed ranges, including with
    # deliberately extreme tuning) that magnitude difference doesn't produce
    # a reliable separation in a 2-player game -- both clearly and
    # consistently beat EASY, which is what the spec actually requires.
    wins = 0
    for seed in range(WINRATE_TRIALS):
        game = simulate(seed, Difficulty.MEDIUM, Difficulty.EASY)
        if game.winner == "A":
            wins += 1
    medium_vs_easy = wins / WINRATE_TRIALS
    write_report("go_fish_difficulty_ordering", {"medium_vs_easy_winrate": medium_vs_easy})
    assert medium_vs_easy > 0.5


def test_go_fish_hard_beats_easy_with_3_players_too():
    # With a genuine choice of opponent, HARD's opponent-avoidance weighting
    # (folded into rank selection via _best_opponent_multiplier, and into
    # target selection via _opponent_weights) gets to actually do something,
    # unlike the 2-player case.
    wins_hard = 0
    wins_easy_total = 0
    trials = WINRATE_TRIALS
    for seed in range(trials):
        game = GoFishGame(
            ["A", "B", "C"],
            ai_difficulties={"A": Difficulty.HARD, "B": Difficulty.EASY, "C": Difficulty.EASY},
            seed=seed,
        )
        turns = 0
        while not game.game_over:
            game.take_ai_turn()
            turns += 1
            assert turns <= MAX_TURNS + 10
        if game.winner == "A":
            wins_hard += 1
        elif game.winner in ("B", "C"):
            wins_easy_total += 1

    stats = {"trials": trials, "hard_winrate": wins_hard / trials, "easy_winrate": wins_easy_total / trials}
    write_report("go_fish_hard_vs_two_easy_3player", stats)
    assert stats["hard_winrate"] > 1 / 3  # beats its "fair share" against 2 weaker opponents
    assert wins_easy_total > 0  # still beatable
