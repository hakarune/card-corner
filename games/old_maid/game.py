"""Old Maid game engine: dealing, pair-discarding, blind draws, and the
single-loser end state (framed positively — see ui/ for the celebration
treatment, not this module's concern).
"""
from __future__ import annotations

import random
from dataclasses import dataclass, field

from core.ai.base import Difficulty
from core.ai.old_maid_ai import OldMaidStrategy
from core.card import Card, Rank
from core.deck import build_old_maid_deck, deal_all, shuffled
from core.player import Player

MAX_TURNS = 400


@dataclass
class DrawResult:
    drawer: str
    target: str
    card: Card
    paired_ranks: list[Rank] = field(default_factory=list)
    drawer_now_empty: bool = False
    target_now_empty: bool = False


class OldMaidGame:
    def __init__(
        self,
        player_names: list[str],
        ai_difficulties: dict[str, Difficulty] | None = None,
        seed: int | None = None,
    ):
        if not 2 <= len(player_names) <= 4:
            raise ValueError("Old Maid supports 2-4 players")
        if len(set(player_names)) != len(player_names):
            raise ValueError("player names must be unique")

        ai_difficulties = ai_difficulties or {}
        self.rng = random.Random(seed)
        self.order = list(player_names)
        self.players = {
            name: Player(name=name, is_ai=name in ai_difficulties)
            for name in player_names
        }
        self.strategies = {
            name: OldMaidStrategy(diff, random.Random(self.rng.random()))
            for name, diff in ai_difficulties.items()
        }

        deck = shuffled(build_old_maid_deck(), self.rng)
        hands = deal_all(deck, len(player_names))
        for name, hand in zip(player_names, hands):
            self.players[name].hand.add_many(hand)

        self.turn_index = 0
        self.turn_count = 0
        self.game_over = False
        self.loser: str | None = None
        self.stalemate = False

        for name in self.order:
            self._discard_pairs(name)
        self._advance_to_next_active(allow_same=True)
        self._check_game_over()

    @property
    def current_player_name(self) -> str:
        return self.order[self.turn_index]

    def active_player_names(self) -> list[str]:
        return [n for n in self.order if not self.players[n].hand.is_empty()]

    def other_active_names(self, name: str) -> list[str]:
        return [n for n in self.active_player_names() if n != name]

    def is_ai_turn(self) -> bool:
        return self.players[self.current_player_name].is_ai

    def take_ai_turn(self) -> DrawResult:
        name = self.current_player_name
        strategy = self.strategies.get(name)
        if strategy is None:
            raise ValueError(f"{name} is not AI-controlled")
        opponents = self.other_active_names(name)
        sizes = {n: len(self.players[n].hand) for n in opponents}
        target = strategy.decide_target(sizes)
        return self.draw(name, target)

    def draw(self, drawer_name: str, target_name: str) -> DrawResult:
        if self.game_over:
            raise RuntimeError("game is already over")
        if drawer_name != self.current_player_name:
            raise ValueError("it is not this player's turn")
        if target_name == drawer_name:
            raise ValueError("cannot draw from yourself")
        if target_name not in self.players:
            raise ValueError(f"unknown target player: {target_name}")
        target_hand = self.players[target_name].hand
        if target_hand.is_empty():
            raise ValueError("target has no cards to draw")

        # Blind draw: a uniformly random card position, since the cards are
        # face-down. This is ordinary game randomness (like a shuffle), not
        # an AI "decision" — it uses the game's own RNG at every difficulty.
        index = self.rng.randrange(len(target_hand.cards))
        card = target_hand.cards.pop(index)
        drawer = self.players[drawer_name]
        drawer.hand.add(card)

        paired = self._discard_pairs(drawer_name)
        result = DrawResult(
            drawer=drawer_name,
            target=target_name,
            card=card,
            paired_ranks=paired,
            drawer_now_empty=drawer.hand.is_empty(),
            target_now_empty=target_hand.is_empty(),
        )

        self.turn_count += 1
        self._advance_turn()
        self._check_game_over()
        return result

    def _discard_pairs(self, name: str) -> list[Rank]:
        """Discard every complete pair (2 cards of the same rank) currently
        in this hand, via floor division so any count (e.g. 3 or 4 of a
        rank landing in one hand straight off the initial deal) is handled
        correctly, leaving at most one unpaired card of that rank behind.
        """
        player = self.players[name]
        cleared: list[Rank] = []
        for rank in list(player.hand.ranks_present()):
            count = player.hand.count_of_rank(rank)
            pairs = count // 2
            if pairs == 0:
                continue
            matched = player.hand.remove_all_of_rank(rank)
            leftover = matched[: count % 2]
            for c in leftover:
                player.hand.add(c)
            cleared.extend([rank] * pairs)
            player.books.extend([rank] * pairs)
        return cleared

    def _advance_turn(self) -> None:
        self._advance_to_next_active(allow_same=False)

    def _advance_to_next_active(self, allow_same: bool) -> None:
        n = len(self.order)
        start = 0 if allow_same else 1
        for step in range(start, n + 1):
            idx = (self.turn_index + step) % n
            if not self.players[self.order[idx]].hand.is_empty():
                self.turn_index = idx
                return
        # No active players remain; game_over is set by _check_game_over.

    def _check_game_over(self) -> None:
        if self.game_over:
            return
        active = self.active_player_names()
        stalemate = self.turn_count >= MAX_TURNS
        if len(active) <= 1 or stalemate:
            self.game_over = True
            self.stalemate = stalemate and len(active) > 1
            self.loser = active[0] if len(active) == 1 else None
