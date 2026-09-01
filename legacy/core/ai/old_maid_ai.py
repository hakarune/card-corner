"""Old Maid AI strategy.

The only decision an Old Maid player makes is *who to blind-draw a card
from* when more than one opponent still has cards. Which card comes out is
inherently random (a face-down draw) and is handled by the game engine
itself, not the strategy. The strategy only sees public information — each
active opponent's current hand *size* (visible at a real table) — never
their actual cards.
"""
from __future__ import annotations

from .base import Difficulty, Strategy


class OldMaidStrategy(Strategy):
    def decide_target(self, opponent_hand_sizes: dict[str, int]) -> str:
        """`opponent_hand_sizes` maps each still-active opponent's name to
        their current hand size. Returns the chosen opponent's name.
        """
        if not opponent_hand_sizes:
            raise ValueError("no opponents to draw from")
        names = list(opponent_hand_sizes.keys())
        weights = self._weights(opponent_hand_sizes, names)
        return self.weighted_choice(names, weights)

    def _weights(self, opponent_hand_sizes: dict[str, int], names: list[str]) -> list[float]:
        if self.difficulty is Difficulty.EASY:
            return [1.0 for _ in names]
        exponent = 1.0 if self.difficulty is Difficulty.MEDIUM else 1.8
        # Bigger hands get proportionally more of the "who do I draw from"
        # weight — a mild, non-cheating heuristic (larger hands are public
        # information at any real table), not a guarantee of anything.
        return [max(opponent_hand_sizes[n], 1) ** exponent for n in names]
