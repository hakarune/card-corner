"""Go Fish AI strategy.

The strategy only ever looks at (a) its own hand and (b) the shared public
`AskRecord` history — the log of "do you have any Xs?" exchanges that every
player at a real table would hear and see the outcome of. It never looks at
another player's hand or the stock's order, satisfying the no-cheating rule
in the project spec.
"""
from __future__ import annotations

from dataclasses import dataclass

from ..card import Rank
from ..player import Hand
from .base import Difficulty, Strategy


@dataclass(frozen=True)
class AskRecord:
    """Public record of one ask. `cards_transferred == 0` means a miss
    ("go fish"); otherwise the target handed over that many cards and is now
    known (at that moment) to hold zero of `rank`.
    """

    asker: str
    target: str
    rank: Rank
    cards_transferred: int


class GoFishStrategy(Strategy):
    def decide_ask(
        self,
        my_hand: Hand,
        opponent_names: list[str],
        history: list[AskRecord],
    ) -> tuple[str, Rank]:
        """Return (target_name, rank) to ask for. `my_hand` must be non-empty."""
        candidate_ranks = list(my_hand.ranks_present())
        if not candidate_ranks:
            raise ValueError("cannot ask with an empty hand")
        if not opponent_names:
            raise ValueError("no opponents to ask")

        rank_weights = self._rank_weights(my_hand, candidate_ranks)
        rank = self.weighted_choice(candidate_ranks, rank_weights)

        opponent_weights = self._opponent_weights(opponent_names, rank, history)
        target = self.weighted_choice(opponent_names, opponent_weights)
        return target, rank

    def _rank_weights(self, hand: Hand, ranks: list[Rank]) -> list[float]:
        counts = [hand.count_of_rank(r) for r in ranks]
        if self.difficulty is Difficulty.EASY:
            return [1.0 for _ in ranks]
        if self.difficulty is Difficulty.MEDIUM:
            return [1.0 + c for c in counts]
        return [1.0 + c**2 for c in counts]  # HARD: chase near-complete books

    def _opponent_weights(
        self, opponent_names: list[str], rank: Rank, history: list[AskRecord]
    ) -> list[float]:
        weights = {name: 1.0 for name in opponent_names}
        if self.difficulty is Difficulty.EASY:
            return [weights[n] for n in opponent_names]

        discount = 0.6 if self.difficulty is Difficulty.MEDIUM else 0.3
        for name in opponent_names:
            relevant = [h for h in history if h.target == name and h.rank == rank]
            if not relevant:
                continue
            # Most recent public outcome for (name, rank): a hit or a miss
            # both mean they were confirmed to hold zero of that rank at the
            # time, so deprioritize asking them again — but never rule it
            # out, since they may have drawn into the rank since.
            weights[name] *= discount
        return [weights[n] for n in opponent_names]
