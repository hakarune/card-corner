"""Headless AI-vs-AI self-play simulation for Old Maid (spec §7.2).

Old Maid has no "winner" in the traditional sense — only a single "loser"
(the Old Maid holder). Difficulty sanity here is framed the natural way for
this game: a stronger AI should end up as the loser *less* often than a
weaker one, but never never.
"""
from __future__ import annotations

import pytest

from core.ai.base import Difficulty
from games.old_maid.game import MAX_TURNS, OldMaidGame

from .harness import old_maid_legal_state, write_report

GAMES_PER_MATCHUP = 600
LOSS_RATE_TRIALS = 9000

MATCHUPS = [
    (Difficulty.HARD, Difficulty.EASY),
    (Difficulty.MEDIUM, Difficulty.EASY),
    (Difficulty.HARD, Difficulty.MEDIUM),
    (Difficulty.EASY, Difficulty.EASY),
]


def simulate(seed: int, d1: Difficulty, d2: Difficulty) -> OldMaidGame:
    game = OldMaidGame(["A", "B"], ai_difficulties={"A": d1, "B": d2}, seed=seed)
    turns = 0
    while not game.game_over:
        assert old_maid_legal_state(game), "illegal state reached mid-game"
        game.take_ai_turn()
        turns += 1
        assert turns <= MAX_TURNS + 10, "no hard turn-count ceiling — possible infinite loop"
    assert old_maid_legal_state(game), "illegal state at game end"
    return game


@pytest.mark.parametrize("d1,d2", MATCHUPS, ids=lambda d: d.value if hasattr(d, "value") else d)
def test_old_maid_gauntlet_no_crashes_and_legal_states(d1, d2):
    stats = {"losses_a": 0, "losses_b": 0, "stalemates": 0, "total_turns": 0}
    for seed in range(GAMES_PER_MATCHUP):
        game = simulate(seed, d1, d2)
        if game.stalemate:
            stats["stalemates"] += 1
        if game.loser == "A":
            stats["losses_a"] += 1
        elif game.loser == "B":
            stats["losses_b"] += 1
        stats["total_turns"] += game.turn_count

    stats["games"] = GAMES_PER_MATCHUP
    stats["avg_turns"] = stats["total_turns"] / GAMES_PER_MATCHUP
    stats["stalemate_rate"] = stats["stalemates"] / GAMES_PER_MATCHUP
    write_report(
        f"old_maid_{d1.value}_vs_{d2.value}", {"matchup": f"{d1.value} vs {d2.value}", **stats}
    )
    assert stats["stalemate_rate"] < 0.05


def test_old_maid_hard_loses_less_often_than_its_fair_share():
    # In a 2-player game, "who do I draw from" has only one legal answer, so
    # OldMaidStrategy's entire skill lever (preferring to draw from bigger
    # hands, since a real player can see hand sizes) is a no-op there — Old
    # Maid only has a real decision to make with 3+ players. Even then, this
    # game is fundamentally luck-dominated (the draw itself is always a
    # blind, uniformly random pick — that's the whole point of face-down
    # cards); empirically, even extreme weighting only nudges the loss rate
    # a few points below "fair share" (1/N), never close to 50/50-style
    # separation the way Memory's recall mechanic can. So this asserts the
    # real, reproducible-but-modest edge that actually exists: across many
    # 4-player games, the HARD player should end up as the loser somewhat
    # less than its 1-in-4 fair share, and clearly more than zero times.
    trials = LOSS_RATE_TRIALS
    # 0.25 itself (exact fair share) is technically the real threshold, but
    # the effect size here is small (~0.234-0.2475 measured across several
    # independent seed ranges) -- close enough to the sample's own standard
    # error at smaller trial counts to risk an unrelated RNG-order change
    # flipping the assertion. Assert against a slightly loosened bound,
    # safely inside the confirmed real effect, with a large enough sample
    # (9000 trials) that the margin below is itself robust.
    fair_share = 0.248
    hard_losses = 0
    easy_losses = 0
    for seed in range(trials):
        game = OldMaidGame(
            ["A", "B", "C", "D"],
            ai_difficulties={
                "A": Difficulty.HARD,
                "B": Difficulty.EASY,
                "C": Difficulty.EASY,
                "D": Difficulty.EASY,
            },
            seed=seed,
        )
        turns = 0
        while not game.game_over:
            game.take_ai_turn()
            turns += 1
            assert turns <= MAX_TURNS + 10, "no hard turn-count ceiling — possible infinite loop"
        if game.loser == "A":
            hard_losses += 1
        elif game.loser in ("B", "C", "D"):
            easy_losses += 1

    stats = {
        "trials": trials,
        "hard_loss_rate": hard_losses / trials,
        "easy_loss_rate_any_of_3": easy_losses / trials,
        "fair_share": fair_share,
    }
    write_report("old_maid_hard_vs_easy_lossrate_4player", stats)

    assert stats["hard_loss_rate"] < fair_share, "Hard should lose less than its 1-in-4 fair share"
    assert hard_losses > 0, "Hard must still lose sometimes -- never unbeatable"
