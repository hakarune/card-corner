"""Card, Suit, and Rank primitives shared by Go Fish, Old Maid, and Memory."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class Suit(Enum):
    CLUBS = "clubs"
    DIAMONDS = "diamonds"
    HEARTS = "hearts"
    SPADES = "spades"


class Rank(Enum):
    ACE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13


RANK_LABELS: dict[Rank, str] = {
    Rank.ACE: "A",
    Rank.TWO: "2",
    Rank.THREE: "3",
    Rank.FOUR: "4",
    Rank.FIVE: "5",
    Rank.SIX: "6",
    Rank.SEVEN: "7",
    Rank.EIGHT: "8",
    Rank.NINE: "9",
    Rank.TEN: "10",
    Rank.JACK: "J",
    Rank.QUEEN: "Q",
    Rank.KING: "K",
}

SUIT_SYMBOLS: dict[Suit, str] = {
    Suit.CLUBS: "♣",
    Suit.DIAMONDS: "♦",
    Suit.HEARTS: "♥",
    Suit.SPADES: "♠",
}

RED_SUITS = {Suit.DIAMONDS, Suit.HEARTS}


@dataclass(frozen=True)
class Card:
    """A single playing card.

    `suit` and `rank` are ``None`` only for the special unmatched "odd" card
    used by Old Maid — a themed card that by design has no pair.
    """

    suit: Suit | None
    rank: Rank | None
    is_odd_one: bool = False

    def __post_init__(self) -> None:
        if self.is_odd_one:
            if self.suit is not None or self.rank is not None:
                raise ValueError("the odd card must have suit=None and rank=None")
        else:
            if self.suit is None or self.rank is None:
                raise ValueError("non-odd cards must have both suit and rank")

    @property
    def label(self) -> str:
        if self.is_odd_one:
            return "OM"
        return RANK_LABELS[self.rank]

    @property
    def symbol(self) -> str:
        if self.is_odd_one:
            return "\U0001F638"  # cat face — stand-in art for the "Old Maid" card
        return SUIT_SYMBOLS[self.suit]

    @property
    def is_red(self) -> bool:
        return not self.is_odd_one and self.suit in RED_SUITS

    def matches_rank(self, other: "Card") -> bool:
        """True if both cards share a rank. The odd card never matches anything."""
        if self.is_odd_one or other.is_odd_one:
            return False
        return self.rank == other.rank

    def __str__(self) -> str:
        return f"{self.label}{self.symbol}"


def make_odd_card() -> Card:
    """The single unmatched "Old Maid" card."""
    return Card(suit=None, rank=None, is_odd_one=True)
