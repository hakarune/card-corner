"""Player/Hand abstraction shared by Go Fish, Old Maid, and Memory."""
from __future__ import annotations

from dataclasses import dataclass, field

from .card import Card, Rank


@dataclass
class Hand:
    cards: list[Card] = field(default_factory=list)

    def add(self, card: Card) -> None:
        self.cards.append(card)

    def add_many(self, cards: list[Card]) -> None:
        self.cards.extend(cards)

    def remove(self, card: Card) -> None:
        self.cards.remove(card)

    def remove_all_of_rank(self, rank: Rank) -> list[Card]:
        """Remove and return every card of `rank` in this hand."""
        matched = [c for c in self.cards if not c.is_odd_one and c.rank == rank]
        for c in matched:
            self.cards.remove(c)
        return matched

    def ranks_present(self) -> set[Rank]:
        return {c.rank for c in self.cards if not c.is_odd_one}

    def count_of_rank(self, rank: Rank) -> int:
        return sum(1 for c in self.cards if not c.is_odd_one and c.rank == rank)

    def has_rank(self, rank: Rank) -> bool:
        return self.count_of_rank(rank) > 0

    def is_empty(self) -> bool:
        return len(self.cards) == 0

    def __len__(self) -> int:
        return len(self.cards)

    def __iter__(self):
        return iter(self.cards)


@dataclass
class Player:
    name: str
    is_ai: bool = False
    hand: Hand = field(default_factory=Hand)
    books: list[Rank] = field(default_factory=list)  # Go Fish: ranks scored as books
    score: int = 0
