"""Memory/Concentration game engine: a face-down board, two-flip turns, and
a shared public reveal history that every AI strategy (and the UI, for a
human player's own recollection) can read from.
"""
from __future__ import annotations

import random
from dataclasses import dataclass

from core.ai.base import Difficulty
from core.ai.memory_ai import MemoryStrategy
from core.card import Card, Rank
from core.deck import build_memory_deck, shuffled
from core.player import Player

MAX_TURNS = 500


@dataclass
class FlipResult:
    player: str
    pos1: int
    pos2: int
    rank1: Rank
    rank2: Rank
    matched: bool
    went_again: bool


class MemoryGame:
    def __init__(
        self,
        player_names: list[str],
        num_pairs: int = 8,
        ai_difficulties: dict[str, Difficulty] | None = None,
        seed: int | None = None,
    ):
        if not 1 <= len(player_names) <= 4:
            raise ValueError("Memory supports 1-4 players")
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
            name: MemoryStrategy(diff, random.Random(self.rng.random()))
            for name, diff in ai_difficulties.items()
        }

        self.board: list[Card] = shuffled(build_memory_deck(num_pairs), self.rng)
        self.matched: set[int] = set()
        self.known_positions: dict[int, Rank] = {}

        self.turn_index = 0
        self.turn_count = 0
        self.game_over = False
        self.stalemate = False

    @property
    def current_player_name(self) -> str:
        return self.order[self.turn_index]

    def unflipped_positions(self) -> list[int]:
        return [i for i in range(len(self.board)) if i not in self.matched]

    def is_ai_turn(self) -> bool:
        return self.players[self.current_player_name].is_ai

    def take_ai_turn(self) -> FlipResult:
        name = self.current_player_name
        strategy = self.strategies.get(name)
        if strategy is None:
            raise ValueError(f"{name} is not AI-controlled")
        pos1, pos2 = strategy.decide_flips(self.known_positions, self.unflipped_positions())
        return self.flip_two(name, pos1, pos2)

    def flip_two(self, player_name: str, pos1: int, pos2: int) -> FlipResult:
        if self.game_over:
            raise RuntimeError("game is already over")
        if player_name != self.current_player_name:
            raise ValueError("it is not this player's turn")
        if pos1 == pos2:
            raise ValueError("must flip two different positions")
        for pos in (pos1, pos2):
            if not 0 <= pos < len(self.board):
                raise ValueError(f"position out of range: {pos}")
            if pos in self.matched:
                raise ValueError(f"position already matched: {pos}")

        card1, card2 = self.board[pos1], self.board[pos2]
        self.known_positions[pos1] = card1.rank
        self.known_positions[pos2] = card2.rank

        matched = card1.matches_rank(card2)
        if matched:
            self.matched.add(pos1)
            self.matched.add(pos2)
            player = self.players[player_name]
            player.books.append(card1.rank)
            player.score += 1

        result = FlipResult(
            player=player_name,
            pos1=pos1,
            pos2=pos2,
            rank1=card1.rank,
            rank2=card2.rank,
            matched=matched,
            went_again=matched,
        )

        self.turn_count += 1
        if not matched:
            self.turn_index = (self.turn_index + 1) % len(self.order)
        self._check_game_over()
        return result

    def _check_game_over(self) -> None:
        if self.game_over:
            return
        all_matched = len(self.matched) == len(self.board)
        stalemate = self.turn_count >= MAX_TURNS
        if all_matched or stalemate:
            self.game_over = True
            self.stalemate = stalemate and not all_matched
