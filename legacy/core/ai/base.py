"""Shared AI difficulty tiers and the abstract per-game Strategy interface.

Design rules (see project spec §4):
  * No hidden-information cheating — a strategy may only reason over
    information a real opponent would have (own hand, discard/public piles,
    public asks/matches, cards it has personally seen flipped this game).
  * Non-determinism at every tier — decisions must go through weighted
    random selection, never a fixed greedy rule, and each strategy owns its
    own `random.Random` instance rather than the global `random` module.
  * Difficulty tunes how good the weighting is, not whether randomness
    exists — Hard should win more than Easy over many games, but never be
    unbeatable.
"""
from __future__ import annotations

import random
from abc import ABC
from enum import Enum


class Difficulty(Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


DIFFICULTY_LABELS: dict[Difficulty, str] = {
    Difficulty.EASY: "Sleepy Fox",
    Difficulty.MEDIUM: "Clever Fox",
    Difficulty.HARD: "Sneaky Fox",
}


class Strategy(ABC):
    """Base class for a per-game AI strategy. Concrete subclasses (one per
    game) expose their own `decide_*` methods, since the decisions each game
    requires differ in shape (who/what to ask, which pair to flip, etc.).
    """

    def __init__(self, difficulty: Difficulty, rng: random.Random | None = None):
        self.difficulty = difficulty
        self.rng = rng if rng is not None else random.Random()

    # Subclass `decide_*` methods must only accept public state: the AI's own
    # Hand/Player, discard/public piles, and public ask/flip history. Never
    # pass an opponent's Hand or the deck/stock order — doing so would leak
    # hidden information the AI isn't entitled to (see module docstring).
    # Similarly, always draw choices through `self.rng` / `self.weighted_choice`,
    # never the global `random` module, so games stay independently random.

    @property
    def label(self) -> str:
        return DIFFICULTY_LABELS[self.difficulty]

    def weighted_choice(self, options: list, weights: list[float]):
        """Pick one of `options` using `weights` via this strategy's own RNG."""
        return self.rng.choices(options, weights=weights, k=1)[0]
