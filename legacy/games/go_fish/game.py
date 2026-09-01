"""Go Fish game engine: rules, turn order, and book (pair) scoring.

A book is a *pair* (2 of the same rank), not the traditional 4-of-a-kind --
a simplified variant for this age group, per playtest feedback. Since a
standard deck holds 4 copies of every rank, each rank can yield up to 2
books over the course of a game (26 books total across 13 ranks, using all
52 cards).

Supports 2-4 players. Any subset of players may be AI-controlled via
`ai_difficulties`; the rest are assumed human-controlled and driven by the
UI calling `ask()` directly.
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from core.ai.base import Difficulty
from core.ai.go_fish_ai import AskRecord, GoFishStrategy
from core.card import Rank
from core.deck import build_standard_deck, deal_count, shuffled
from core.player import Player

MAX_TURNS = 400
TOTAL_BOOKS = 26  # 13 ranks x up to 2 pairs each


@dataclass
class AskResult:
    asker: str
    target: str
    rank: Rank
    cards_transferred: int
    asker_drew: bool = False
    asker_drew_matched: bool = False
    went_again: bool = False
    books_claimed_by_asker: list[Rank] = field(default_factory=list)


class GoFishGame:
    def __init__(
        self,
        player_names: list[str],
        ai_difficulties: dict[str, Difficulty] | None = None,
        seed: int | None = None,
    ):
        if not 2 <= len(player_names) <= 4:
            raise ValueError("Go Fish supports 2-4 players")
        if len(set(player_names)) != len(player_names):
            raise ValueError("player names must be unique")

        ai_difficulties = ai_difficulties or {}
        self.rng = random.Random(seed)
        self.order = list(player_names)
        self.players = {
            name: Player(name=name, is_ai=name in ai_difficulties)
            for name in player_names
        }
        # Each AI gets its own independent RNG instance, seeded from this
        # game's RNG, so no two strategies (or two games) share a stream.
        self.strategies = {
            name: GoFishStrategy(diff, random.Random(self.rng.random()))
            for name, diff in ai_difficulties.items()
        }

        count_per_hand = 7 if len(player_names) == 2 else 5
        deck = shuffled(build_standard_deck(), self.rng)
        hands, stock = deal_count(deck, len(player_names), count_per_hand)
        for name, hand in zip(player_names, hands):
            self.players[name].hand.add_many(hand)
        self.stock: list = stock

        self.history: list[AskRecord] = []
        self._turn_failed_ranks: list[Rank] = []
        self.turn_index = 0
        self.turn_count = 0
        self.game_over = False
        self.winner: str | None = None
        self.stalemate = False

        for name in self.order:
            self._claim_books(name)
        self._ensure_current_player_can_act()
        self._check_game_over()

    @property
    def current_player_name(self) -> str:
        return self.order[self.turn_index]

    def other_player_names(self, name: str) -> list[str]:
        return [n for n in self.order if n != name]

    def legal_ranks(self, name: str) -> list[Rank]:
        return list(self.players[name].hand.ranks_present())

    def is_ai_turn(self) -> bool:
        return self.players[self.current_player_name].is_ai

    def books_claimed_by_rank(self) -> dict[Rank, int]:
        """How many books of each rank have been claimed so far, across all
        players. Public information -- claimed books are laid face-up on
        the table in real Go Fish, visible to everyone, not a peek at
        anyone's hand.
        """
        counts: dict[Rank, int] = {}
        for player in self.players.values():
            for rank in player.books:
                counts[rank] = counts.get(rank, 0) + 1
        return counts

    def decide_ai_ask(self) -> tuple[str, Rank]:
        """What the current AI player's strategy would ask for, without
        executing it. Splitting decide from execute lets a screen show a
        visible, audible request and give the human a beat to react (or,
        when asked, a card to click to hand over) before the transfer
        actually happens, instead of the ask resolving silently and
        instantly. take_ai_turn() below still does both steps at once for
        callers (gauntlet/tests) that don't care about that distinction.
        """
        name = self.current_player_name
        strategy = self.strategies.get(name)
        if strategy is None:
            raise ValueError(f"{name} is not AI-controlled")
        opponents = self.other_player_names(name)
        return strategy.decide_ask(
            self.players[name].hand,
            opponents,
            self.history,
            tuple(self._turn_failed_ranks),
            self.books_claimed_by_rank(),
        )

    def take_ai_turn(self) -> AskResult:
        name = self.current_player_name
        target, rank = self.decide_ai_ask()
        return self.ask(name, target, rank)

    def ask(self, asker_name: str, target_name: str, rank: Rank) -> AskResult:
        if self.game_over:
            raise RuntimeError("game is already over")
        if asker_name != self.current_player_name:
            raise ValueError("it is not this player's turn")
        if target_name == asker_name:
            raise ValueError("cannot ask yourself")
        if target_name not in self.players:
            raise ValueError(f"unknown target player: {target_name}")
        asker = self.players[asker_name]
        target = self.players[target_name]
        if not asker.hand.has_rank(rank):
            raise ValueError("can only ask for a rank you hold yourself")

        transferred = target.hand.remove_all_of_rank(rank)
        result = AskResult(
            asker=asker_name, target=target_name, rank=rank, cards_transferred=len(transferred)
        )
        self.history.append(AskRecord(asker_name, target_name, rank, len(transferred)))

        hit = False
        if transferred:
            asker.hand.add_many(transferred)
            result.books_claimed_by_asker = self._claim_books(asker_name)
            hit = True
        else:
            self._turn_failed_ranks.append(rank)
            drawn = self._draw(asker_name)
            if drawn is not None:
                result.asker_drew = True
                if drawn.rank == rank:
                    result.asker_drew_matched = True
                result.books_claimed_by_asker = self._claim_books(asker_name)
                hit = result.asker_drew_matched

        if hit:
            # A pair claims a book the instant it forms, which -- unlike
            # the old 4-of-a-kind rule -- can now easily empty a hand of
            # just 1-2 cards right on the hit (either path: a successful
            # ask, or drawing the exact match after a miss). Either way,
            # give a free redraw so a "go again" turn always has a card to
            # act with, same as the original hit-branch behavior.
            if asker.hand.is_empty() and self.stock:
                self._draw(asker_name)
                result.asker_drew = True
                result.books_claimed_by_asker += self._claim_books(asker_name)
            result.went_again = not asker.hand.is_empty()

        self.turn_count += 1
        if not result.went_again:
            self._turn_failed_ranks = []
            self._advance_turn()
        self._check_game_over()
        return result

    def _draw(self, name: str):
        if not self.stock:
            return None
        card = self.stock.pop()
        self.players[name].hand.add(card)
        return card

    def _claim_books(self, name: str) -> list[Rank]:
        """Claims every complete pair currently in this hand, via floor
        division so a rank landing at count 3 or 4 (e.g. from the initial
        deal) claims 1 or 2 books at once rather than requiring a full
        4-of-a-kind, leaving at most one unpaired card of that rank behind.
        """
        player = self.players[name]
        claimed: list[Rank] = []
        # Sorted, not just list(a_set): Hand.ranks_present() returns a
        # set[Rank], and Rank is a plain Enum (identity-hashed) whose set
        # iteration order is stable within one process but can differ
        # between process runs. Doesn't currently change any outcome here
        # (every qualifying rank gets claimed regardless of order, and Go
        # Fish's stock draw is positional-on-the-shared-stock, not on a
        # hand reordered by this loop) -- sorted anyway for defense-in-
        # depth, since Old Maid's near-identical _discard_pairs loop had
        # the exact same pattern and it *did* leak into real gameplay
        # there (a positional blind draw off a hand this loop reorders).
        for rank in sorted(player.hand.ranks_present(), key=lambda r: r.value):
            count = player.hand.count_of_rank(rank)
            pairs = count // 2
            if pairs == 0:
                continue
            matched = player.hand.remove_all_of_rank(rank)
            leftover = matched[: count % 2]
            for c in leftover:
                player.hand.add(c)
            player.books.extend([rank] * pairs)
            player.score += pairs
            claimed.extend([rank] * pairs)
        return claimed

    def _advance_turn(self) -> None:
        self.turn_index = (self.turn_index + 1) % len(self.order)
        self._ensure_current_player_can_act()

    def _ensure_current_player_can_act(self) -> None:
        """If the player whose turn it is has an empty hand, give them one
        free draw from the stock so they have something to ask with; if the
        stock is also empty, skip to the next player who can act.
        """
        attempts = 0
        while attempts < len(self.order):
            player = self.players[self.current_player_name]
            if not player.hand.is_empty():
                return
            if self.stock:
                self._draw(self.current_player_name)
                self._claim_books(self.current_player_name)
                if not player.hand.is_empty():
                    return
            self.turn_index = (self.turn_index + 1) % len(self.order)
            attempts += 1

    def _check_game_over(self) -> None:
        if self.game_over:
            return
        total_books = sum(len(p.books) for p in self.players.values())
        all_hands_empty = all(p.hand.is_empty() for p in self.players.values())
        stalemate = self.turn_count >= MAX_TURNS

        if total_books == TOTAL_BOOKS or (not self.stock and all_hands_empty) or stalemate:
            self.game_over = True
            self.stalemate = stalemate and total_books != TOTAL_BOOKS and not (
                not self.stock and all_hands_empty
            )
            best_count = max(len(p.books) for p in self.players.values())
            tied = [p.name for p in self.players.values() if len(p.books) == best_count]
            self.winner = tied[0] if len(tied) == 1 else None
