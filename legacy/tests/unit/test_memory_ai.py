import random

import pytest

from core.ai.base import Difficulty
from core.ai.memory_ai import MemoryStrategy
from core.card import Rank


def test_decide_flips_raises_with_fewer_than_two_unflipped():
    strategy = MemoryStrategy(Difficulty.EASY, random.Random(1))
    with pytest.raises(ValueError):
        strategy.decide_flips({}, [0])


def test_decide_flips_returns_two_distinct_valid_positions():
    strategy = MemoryStrategy(Difficulty.EASY, random.Random(1))
    unflipped = list(range(8))
    for _ in range(50):
        p1, p2 = strategy.decide_flips({}, unflipped)
        assert p1 != p2
        assert p1 in unflipped and p2 in unflipped


def test_hard_finds_known_pair_more_often_than_easy():
    known = {0: Rank.FIVE, 5: Rank.FIVE}
    unflipped = list(range(8))

    def hit_rate(difficulty, trials=300):
        hits = 0
        for seed in range(trials):
            strategy = MemoryStrategy(difficulty, random.Random(seed))
            p1, p2 = strategy.decide_flips(known, unflipped)
            if {p1, p2} == {0, 5}:
                hits += 1
        return hits / trials

    easy_rate = hit_rate(Difficulty.EASY)
    hard_rate = hit_rate(Difficulty.HARD)
    assert hard_rate > easy_rate
    assert hard_rate < 1.0  # never a guaranteed lock, even at HARD


def test_non_determinism_across_many_trials():
    unflipped = list(range(10))
    seen = set()
    for seed in range(100):
        strategy = MemoryStrategy(Difficulty.EASY, random.Random(seed))
        seen.add(strategy.decide_flips({}, unflipped))
    assert len(seen) > 1


def test_never_returns_a_matched_or_out_of_range_position():
    strategy = MemoryStrategy(Difficulty.HARD, random.Random(3))
    known = {0: Rank.FIVE, 5: Rank.FIVE, 1: Rank.NINE, 2: Rank.NINE}
    unflipped = [3, 4, 6, 7]  # 0,1,2,5 already matched/removed
    for _ in range(50):
        p1, p2 = strategy.decide_flips(known, unflipped)
        assert p1 in unflipped and p2 in unflipped
