"""Memory/Concentration AI strategy.

Difficulty is expressed *entirely* through how reliably the AI recalls
cards it has already seen — never through cheating. `known_positions` is
the shared public reveal history (every position any player has ever
flipped face-up, win or miss — exactly what a real opponent watching the
table would remember), and each difficulty tier applies its own recall
probability on top of that public information rather than being handed
ground truth about unseen cards.
"""
from __future__ import annotations

from ..card import Rank
from .base import Difficulty, Strategy

RECALL_CHANCE: dict[Difficulty, float] = {
    Difficulty.EASY: 0.15,
    Difficulty.MEDIUM: 0.5,
    Difficulty.HARD: 0.85,
}


class MemoryStrategy(Strategy):
    def decide_flips(
        self, known_positions: dict[int, Rank], unflipped: list[int]
    ) -> tuple[int, int]:
        """Choose two distinct positions to flip this turn. If recall turns
        up two remembered positions sharing a rank, flip exactly those for a
        guaranteed match; otherwise fall back to a random guess for
        whichever position(s) memory didn't supply.
        """
        if len(unflipped) < 2:
            raise ValueError("need at least two unflipped positions")

        remembered = self._recalled(known_positions, set(unflipped))
        by_rank: dict[Rank, list[int]] = {}
        for pos, rank in remembered.items():
            by_rank.setdefault(rank, []).append(pos)
        for positions in by_rank.values():
            if len(positions) >= 2:
                return positions[0], positions[1]

        first = self.rng.choice(unflipped)
        remaining = [p for p in unflipped if p != first]
        second = self.rng.choice(remaining)
        return first, second

    def _recalled(
        self, known_positions: dict[int, Rank], unflipped: set[int]
    ) -> dict[int, Rank]:
        chance = RECALL_CHANCE[self.difficulty]
        return {
            pos: rank
            for pos, rank in known_positions.items()
            if pos in unflipped and self.rng.random() < chance
        }
