import random

import pytest

from core.ai.base import Difficulty
from core.ai.go_fish_ai import AskRecord, GoFishStrategy
from core.card import Card, Rank, Suit
from core.player import Hand


def hand_of(*ranks):
    h = Hand()
    for r in ranks:
        h.add(Card(suit=Suit.CLUBS, rank=r))
    return h


def test_decide_ask_only_offers_ranks_actually_held():
    strategy = GoFishStrategy(Difficulty.EASY, random.Random(1))
    hand = hand_of(Rank.THREE, Rank.NINE)
    for _ in range(50):
        _, rank = strategy.decide_ask(hand, ["Bob"], [])
        assert rank in (Rank.THREE, Rank.NINE)


def test_decide_ask_raises_on_empty_hand():
    strategy = GoFishStrategy(Difficulty.EASY, random.Random(1))
    with pytest.raises(ValueError):
        strategy.decide_ask(Hand(), ["Bob"], [])


def test_decide_ask_raises_with_no_opponents():
    strategy = GoFishStrategy(Difficulty.EASY, random.Random(1))
    hand = hand_of(Rank.THREE)
    with pytest.raises(ValueError):
        strategy.decide_ask(hand, [], [])


def test_decide_ask_targets_only_known_opponents():
    strategy = GoFishStrategy(Difficulty.HARD, random.Random(1))
    hand = hand_of(Rank.THREE)
    for _ in range(50):
        target, _ = strategy.decide_ask(hand, ["Bob", "Sue"], [])
        assert target in ("Bob", "Sue")


def test_non_determinism_across_many_trials():
    hand = hand_of(Rank.TWO, Rank.FIVE, Rank.NINE)
    seen = set()
    for seed in range(100):
        strategy = GoFishStrategy(Difficulty.EASY, random.Random(seed))
        target, rank = strategy.decide_ask(hand, ["Bob", "Sue"], [])
        seen.add((target, rank))
    # With 3 ranks x 2 opponents = 6 possible outcomes, 100 varied-seed
    # trials should surface more than just one fixed outcome.
    assert len(seen) > 1


def test_hard_ai_deprioritizes_but_does_not_forbid_confirmed_absent_ranks():
    hand = hand_of(Rank.SEVEN)
    # Bob was already confirmed (publicly) to have none of Rank.SEVEN.
    history = [AskRecord(asker="Someone", target="Bob", rank=Rank.SEVEN, cards_transferred=0)]
    counts = {"Bob": 0, "Sue": 0}
    trials = 500
    for seed in range(trials):
        strategy = GoFishStrategy(Difficulty.HARD, random.Random(seed))
        target, _ = strategy.decide_ask(hand, ["Bob", "Sue"], history)
        counts[target] += 1
    # Deprioritized, not eliminated: still asked sometimes, but less than half.
    assert 0 < counts["Bob"] < counts["Sue"]


def test_hard_ai_favors_ranks_closer_to_a_book():
    hand = Hand()
    hand.add_many([Card(suit=Suit.CLUBS, rank=Rank.KING)] * 1)
    hand.add_many(
        [
            Card(suit=Suit.CLUBS, rank=Rank.TWO),
            Card(suit=Suit.HEARTS, rank=Rank.TWO),
            Card(suit=Suit.SPADES, rank=Rank.TWO),
        ]
    )
    counts = {Rank.KING: 0, Rank.TWO: 0}
    trials = 500
    for seed in range(trials):
        strategy = GoFishStrategy(Difficulty.HARD, random.Random(seed))
        _, rank = strategy.decide_ask(hand, ["Bob"], [])
        counts[rank] += 1
    # Rank.TWO (3 held, one away from a book) should be favored over
    # Rank.KING (1 held) at HARD difficulty, but KING should still occur.
    assert counts[Rank.TWO] > counts[Rank.KING] > 0


def test_easy_ai_is_roughly_uniform_over_ranks():
    hand = Hand()
    hand.add_many(
        [
            Card(suit=Suit.CLUBS, rank=Rank.TWO),
            Card(suit=Suit.HEARTS, rank=Rank.TWO),
            Card(suit=Suit.SPADES, rank=Rank.TWO),
        ]
    )
    hand.add(Card(suit=Suit.CLUBS, rank=Rank.KING))
    counts = {Rank.KING: 0, Rank.TWO: 0}
    trials = 1000
    for seed in range(trials):
        strategy = GoFishStrategy(Difficulty.EASY, random.Random(seed))
        _, rank = strategy.decide_ask(hand, ["Bob"], [])
        counts[rank] += 1
    ratio = counts[Rank.TWO] / max(counts[Rank.KING], 1)
    assert 0.7 < ratio < 1.4  # roughly 50/50, generous tolerance for randomness
