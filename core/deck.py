"""Deck construction, shuffling, and dealing. All randomness is routed through
an explicit `random.Random` instance passed by the caller — never the global
`random` module — so games can be replayed deterministically in tests while
still being non-deterministic across real playthroughs.
"""
from __future__ import annotations

import random

from .card import Card, Rank, Suit, make_odd_card


def build_standard_deck() -> list[Card]:
    """A standard 52-card deck, unshuffled."""
    return [Card(suit=s, rank=r) for s in Suit for r in Rank]


def build_old_maid_deck() -> list[Card]:
    """Standard 52 with all four Queens removed, plus the single, permanently
    unmatched "Old Maid" card (49 total). Removing *all* Queens (rather than
    just one) keeps every remaining rank's count even (4 copies each), so
    the sentinel odd card is the only card in the deck that can never find
    a pair. Leaving an odd number of Queens in would create a second,
    accidental "loser card" once the last Queen ran out of partners.
    """
    deck = [c for c in build_standard_deck() if c.rank != Rank.QUEEN]
    deck.append(make_odd_card())
    return deck


def build_memory_deck(num_pairs: int) -> list[Card]:
    """`num_pairs` pairs of same-rank cards (distinguished by suit), for the
    Memory/Concentration board. `num_pairs` must be between 1 and 13.
    """
    if not 1 <= num_pairs <= 13:
        raise ValueError("num_pairs must be between 1 and 13")
    ranks = list(Rank)[:num_pairs]
    suits = (Suit.HEARTS, Suit.SPADES)
    return [Card(suit=s, rank=r) for r in ranks for s in suits]


def shuffled(cards: list[Card], rng: random.Random) -> list[Card]:
    """A new shuffled list; does not mutate `cards`."""
    result = list(cards)
    rng.shuffle(result)
    return result


def deal_all(cards: list[Card], num_hands: int) -> list[list[Card]]:
    """Round-robin deal every card in `cards` into `num_hands` hands. Hands may
    be uneven in size when `len(cards)` doesn't divide evenly (as with Old
    Maid's 53-card deck).
    """
    if num_hands < 1:
        raise ValueError("num_hands must be at least 1")
    hands: list[list[Card]] = [[] for _ in range(num_hands)]
    for i, card in enumerate(cards):
        hands[i % num_hands].append(card)
    return hands


def deal_count(
    cards: list[Card], num_hands: int, count_per_hand: int
) -> tuple[list[list[Card]], list[Card]]:
    """Deal exactly `count_per_hand` cards to each of `num_hands` hands,
    round-robin, returning (hands, remaining_stock).
    """
    if num_hands < 1:
        raise ValueError("num_hands must be at least 1")
    total_needed = num_hands * count_per_hand
    if total_needed > len(cards):
        raise ValueError("not enough cards to deal")
    hands: list[list[Card]] = [[] for _ in range(num_hands)]
    idx = 0
    for _ in range(count_per_hand):
        for h in range(num_hands):
            hands[h].append(cards[idx])
            idx += 1
    return hands, cards[idx:]
