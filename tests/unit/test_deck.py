import random

import pytest

from core.card import Rank, Suit
from core.deck import (
    build_memory_deck,
    build_old_maid_deck,
    build_standard_deck,
    deal_all,
    deal_count,
    shuffled,
)


def test_standard_deck_has_52_unique_cards():
    deck = build_standard_deck()
    assert len(deck) == 52
    assert len(set(deck)) == 52
    for suit in Suit:
        assert sum(1 for c in deck if c.suit == suit) == 13
    for rank in Rank:
        assert sum(1 for c in deck if c.rank == rank) == 4


def test_old_maid_deck_has_49_cards_with_exactly_one_unmatched():
    # 52 standard - 4 Queens (all removed, keeps every rank's count even) + 1
    # sentinel odd card = 49. This guarantees exactly one permanently
    # unmatched card in the whole deck.
    deck = build_old_maid_deck()
    assert len(deck) == 49
    odd_cards = [c for c in deck if c.is_odd_one]
    assert len(odd_cards) == 1
    queens = [c for c in deck if not c.is_odd_one and c.rank == Rank.QUEEN]
    assert len(queens) == 0
    assert len(set(deck)) == 49
    # every remaining rank still has its full, even count of 4
    for rank in Rank:
        if rank == Rank.QUEEN:
            continue
        assert sum(1 for c in deck if not c.is_odd_one and c.rank == rank) == 4


@pytest.mark.parametrize("num_pairs", [1, 6, 13])
def test_memory_deck_has_matching_pairs(num_pairs):
    deck = build_memory_deck(num_pairs)
    assert len(deck) == num_pairs * 2
    ranks = [c.rank for c in deck]
    for rank in set(ranks):
        assert ranks.count(rank) == 2


@pytest.mark.parametrize("bad", [0, 14, -1])
def test_memory_deck_rejects_out_of_range(bad):
    with pytest.raises(ValueError):
        build_memory_deck(bad)


def test_shuffled_does_not_mutate_input_and_preserves_multiset():
    deck = build_standard_deck()
    original = list(deck)
    result = shuffled(deck, random.Random(42))
    assert deck == original
    assert sorted(result, key=lambda c: (c.suit.value, c.rank.value)) == sorted(
        original, key=lambda c: (c.suit.value, c.rank.value)
    )


def test_shuffled_is_seed_reproducible_but_seed_dependent():
    deck = build_standard_deck()
    a = shuffled(deck, random.Random(1))
    b = shuffled(deck, random.Random(1))
    c = shuffled(deck, random.Random(2))
    assert a == b
    assert a != c


def test_deal_all_round_robins_uneven_deck():
    deck = build_old_maid_deck()  # 49 cards
    hands = deal_all(deck, 3)  # doesn't divide evenly by 3
    assert sum(len(h) for h in hands) == 49
    sizes = sorted(len(h) for h in hands)
    assert sizes == [16, 16, 17]
    # no duplicates/missing cards across hands
    all_cards = [c for h in hands for c in h]
    assert len(set(all_cards)) == 49


def test_deal_count_leaves_correct_stock():
    deck = build_standard_deck()
    hands, stock = deal_count(deck, 4, 7)
    assert all(len(h) == 7 for h in hands)
    assert len(stock) == 52 - 4 * 7
    all_dealt = [c for h in hands for c in h] + stock
    assert len(set(all_dealt)) == 52


def test_deal_count_rejects_insufficient_cards():
    deck = build_standard_deck()
    with pytest.raises(ValueError):
        deal_count(deck, 10, 10)


def test_deal_count_zero_per_hand_leaves_full_stock():
    deck = build_standard_deck()
    hands, stock = deal_count(deck, 4, 0)
    assert all(len(h) == 0 for h in hands)
    assert len(stock) == 52


@pytest.mark.parametrize("num_hands", [0, -1])
def test_deal_all_rejects_invalid_num_hands(num_hands):
    with pytest.raises(ValueError):
        deal_all(build_standard_deck(), num_hands)


@pytest.mark.parametrize("num_hands", [0, -1])
def test_deal_count_rejects_invalid_num_hands(num_hands):
    with pytest.raises(ValueError):
        deal_count(build_standard_deck(), num_hands, 1)


def test_memory_deck_pairs_use_hearts_and_spades():
    deck = build_memory_deck(5)
    suits = {c.suit for c in deck}
    assert suits == {Suit.HEARTS, Suit.SPADES}

