"""Letter Match: a solo, non-adversarial mini-game matching uppercase
letters to their lowercase counterparts. No AI opponent, no win/lose
framing — just gentle positive reinforcement on a match and a no-penalty
retry on a miss.

Unlike the three adversarial games, `click()` deliberately never raises for
"silly but plausible" UI input — double-clicking, re-clicking an
already-matched tile, or clicking the same tile twice in a row are all just
ignored (`ClickResult(accepted=False, ...)`), matching the spec's "gentle
retry, no harsh fail state" requirement and keeping a real UI from needing
exception handling for ordinary kid-mashing-the-screen input. Only a
genuinely out-of-range index — never producible by legitimate UI code,
only by a bug — raises ValueError.
"""
from __future__ import annotations

import random
import string
from dataclasses import dataclass

DEFAULT_LETTER_COUNT = 6


@dataclass(frozen=True)
class Tile:
    letter: str  # always the uppercase identity of the letter, e.g. "B"
    is_upper: bool

    @property
    def display(self) -> str:
        return self.letter if self.is_upper else self.letter.lower()


@dataclass
class ClickResult:
    accepted: bool
    pos1: int | None = None
    pos2: int | None = None
    matched: bool = False
    reason: str | None = None


class LetterMatchGame:
    def __init__(self, letter_count: int = DEFAULT_LETTER_COUNT, seed: int | None = None):
        if not 1 <= letter_count <= 26:
            raise ValueError("letter_count must be between 1 and 26")
        self.rng = random.Random(seed)
        letters = self.rng.sample(string.ascii_uppercase, letter_count)
        tiles = [Tile(letter=l, is_upper=True) for l in letters] + [
            Tile(letter=l, is_upper=False) for l in letters
        ]
        self.rng.shuffle(tiles)
        self.board: list[Tile] = tiles
        self.matched: set[int] = set()
        self._pending_first: int | None = None

        self.attempts = 0
        self.correct = 0
        self.game_over = False

    def unflipped_positions(self) -> list[int]:
        return [i for i in range(len(self.board)) if i not in self.matched]

    @property
    def pending_first(self) -> int | None:
        return self._pending_first

    @property
    def accuracy(self) -> float:
        return self.correct / self.attempts if self.attempts else 0.0

    def click(self, pos: int) -> ClickResult:
        if not 0 <= pos < len(self.board):
            raise ValueError(f"position out of range: {pos}")
        if self.game_over:
            return ClickResult(accepted=False, reason="game already complete")
        if pos in self.matched:
            return ClickResult(accepted=False, reason="already matched")

        if self._pending_first is None:
            self._pending_first = pos
            return ClickResult(accepted=True, pos1=pos)

        if pos == self._pending_first:
            return ClickResult(accepted=False, reason="same tile as pending pick")

        first = self._pending_first
        self._pending_first = None
        self.attempts += 1

        tile1, tile2 = self.board[first], self.board[pos]
        matched = tile1.letter == tile2.letter and tile1.is_upper != tile2.is_upper
        if matched:
            self.matched.add(first)
            self.matched.add(pos)
            self.correct += 1

        if len(self.matched) == len(self.board):
            self.game_over = True

        return ClickResult(accepted=True, pos1=first, pos2=pos, matched=matched)
