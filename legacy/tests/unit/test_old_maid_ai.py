import random

import pytest

from core.ai.base import Difficulty
from core.ai.old_maid_ai import OldMaidStrategy


def test_decide_target_raises_with_no_opponents():
    strategy = OldMaidStrategy(Difficulty.EASY, random.Random(1))
    with pytest.raises(ValueError):
        strategy.decide_target({})


def test_decide_target_only_returns_known_opponents():
    strategy = OldMaidStrategy(Difficulty.HARD, random.Random(1))
    for _ in range(50):
        target = strategy.decide_target({"Bob": 5, "Sue": 2})
        assert target in ("Bob", "Sue")


def test_non_determinism_across_many_trials():
    seen = set()
    for seed in range(100):
        strategy = OldMaidStrategy(Difficulty.EASY, random.Random(seed))
        seen.add(strategy.decide_target({"Bob": 5, "Sue": 5}))
    assert len(seen) > 1


def test_easy_is_roughly_uniform_regardless_of_hand_size():
    counts = {"Bob": 0, "Sue": 0}
    trials = 1000
    for seed in range(trials):
        strategy = OldMaidStrategy(Difficulty.EASY, random.Random(seed))
        counts[strategy.decide_target({"Bob": 20, "Sue": 2})] += 1
    ratio = counts["Bob"] / max(counts["Sue"], 1)
    assert 0.7 < ratio < 1.4


def test_hard_favors_larger_hands_more_than_medium():
    def bob_share(difficulty, trials=500):
        counts = {"Bob": 0, "Sue": 0}
        for seed in range(trials):
            strategy = OldMaidStrategy(difficulty, random.Random(seed))
            counts[strategy.decide_target({"Bob": 20, "Sue": 2})] += 1
        return counts["Bob"] / trials

    easy_share = bob_share(Difficulty.EASY)
    medium_share = bob_share(Difficulty.MEDIUM)
    hard_share = bob_share(Difficulty.HARD)

    assert easy_share < medium_share < hard_share
    assert hard_share < 1.0  # never fully deterministic, even at HARD
