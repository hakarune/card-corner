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


def test_hard_ai_favors_ranks_with_more_copies_still_unseen():
    # A rank held only once (3 copies unseen elsewhere) is statistically a
    # better bet than one held 3 times (only 1 copy unseen) -- more unseen
    # copies means a higher chance an opponent is holding at least one, so
    # a higher hit rate. This is deliberately the opposite of "chase the
    # rank closest to a book": ask order doesn't change how many books a
    # full game nets, but hit rate changes how many turns you keep.
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
    # Rank.KING (1 held, 3 unseen elsewhere) should be favored over
    # Rank.TWO (3 held, 1 unseen) at HARD difficulty, but TWO should still occur.
    assert counts[Rank.KING] > counts[Rank.TWO] > 0


def test_hard_ai_favors_ranks_with_no_books_claimed_yet_over_ones():
    # Under the pair-based book rule, a held rank's count in-hand is always
    # 1 in real play (2 auto-claims), so it can't tell ranks apart anymore
    # -- books_claimed_by_rank is the new signal: a rank with a book
    # already claimed by *anyone* has only 2 copies left in circulation
    # instead of 4, a meaningfully worse bet.
    hand = hand_of(Rank.KING, Rank.TWO)
    books_claimed = {Rank.TWO: 1}  # someone already claimed one book of TWOs
    counts = {Rank.KING: 0, Rank.TWO: 0}
    trials = 500
    for seed in range(trials):
        strategy = GoFishStrategy(Difficulty.HARD, random.Random(seed))
        _, rank = strategy.decide_ask(hand, ["Bob"], [], books_claimed_by_rank=books_claimed)
        counts[rank] += 1
    assert counts[Rank.KING] > counts[Rank.TWO] > 0


def test_books_claimed_by_rank_defaults_to_no_signal_when_omitted():
    # Backward-compatible default: omitting the new parameter entirely
    # must not raise and must behave as if no books had been claimed.
    hand = hand_of(Rank.KING)
    strategy = GoFishStrategy(Difficulty.HARD, random.Random(1))
    target, rank = strategy.decide_ask(hand, ["Bob"], [])
    assert rank == Rank.KING


def test_easy_ai_may_repeat_a_same_turn_certain_miss():
    hand = hand_of(Rank.SEVEN)  # only one candidate rank at all
    seen_repeats = False
    for seed in range(50):
        strategy = GoFishStrategy(Difficulty.EASY, random.Random(seed))
        _, rank = strategy.decide_ask(hand, ["Bob"], [], same_turn_failed_ranks=(Rank.SEVEN,))
        assert rank == Rank.SEVEN  # forced, it's the only rank held
        seen_repeats = True
    assert seen_repeats


def test_medium_forgets_all_but_the_most_recent_same_turn_miss():
    hand = hand_of(Rank.TWO, Rank.FIVE)
    # Medium only remembers the *last* entry -> FIVE is excluded, TWO isn't,
    # even though TWO was also failed earlier this turn.
    seen = set()
    for seed in range(50):
        strategy = GoFishStrategy(Difficulty.MEDIUM, random.Random(seed))
        _, rank = strategy.decide_ask(
            hand, ["Bob"], [], same_turn_failed_ranks=(Rank.TWO, Rank.FIVE)
        )
        seen.add(rank)
    assert seen == {Rank.TWO}


def test_hard_excludes_every_same_turn_miss_not_just_the_last():
    hand = hand_of(Rank.TWO, Rank.FIVE, Rank.NINE)
    seen = set()
    for seed in range(50):
        strategy = GoFishStrategy(Difficulty.HARD, random.Random(seed))
        _, rank = strategy.decide_ask(
            hand, ["Bob"], [], same_turn_failed_ranks=(Rank.TWO, Rank.FIVE)
        )
        seen.add(rank)
    assert seen == {Rank.NINE}


def test_same_turn_exclusion_never_leaves_zero_candidates():
    # If every held rank has already failed this turn, the exclusion must
    # back off rather than leave decide_ask with nothing to choose from.
    hand = hand_of(Rank.TWO, Rank.FIVE)
    strategy = GoFishStrategy(Difficulty.HARD, random.Random(1))
    target, rank = strategy.decide_ask(
        hand, ["Bob"], [], same_turn_failed_ranks=(Rank.TWO, Rank.FIVE)
    )
    assert rank in (Rank.TWO, Rank.FIVE)


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
