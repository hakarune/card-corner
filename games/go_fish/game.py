"""Go Fish game engine: rules, turn order, and book (four-of-a-kind) scoring.

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
TOTAL_BOOKS = 13


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

    def take_ai_turn(self) -> AskResult:
        name = self.current_player_name
        strategy = self.strategies.get(name)
        if strategy is None:
            raise ValueError(f"{name} is not AI-controlled")
        opponents = self.other_player_names(name)
        target, rank = strategy.decide_ask(
            self.players[name].hand, opponents, self.history, tuple(self._turn_failed_ranks)
        )
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

        if transferred:
            asker.hand.add_many(transferred)
            result.books_claimed_by_asker = self._claim_books(asker_name)
            if asker.hand.is_empty() and self.stock:
                self._draw(asker_name)
                result.asker_drew = True
                result.books_claimed_by_asker += self._claim_books(asker_name)
            result.went_again = not asker.hand.is_empty()
        else:
            self._turn_failed_ranks.append(rank)
            drawn = self._draw(asker_name)
            if drawn is not None:
                result.asker_drew = True
                if drawn.rank == rank:
                    result.asker_drew_matched = True
                result.books_claimed_by_asker = self._claim_books(asker_name)
                result.went_again = result.asker_drew_matched and not asker.hand.is_empty()

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
        player = self.players[name]
        claimed = []
        for rank in list(player.hand.ranks_present()):
            if player.hand.count_of_rank(rank) == 4:
                player.hand.remove_all_of_rank(rank)
                player.books.append(rank)
                player.score += 1
                claimed.append(rank)
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
