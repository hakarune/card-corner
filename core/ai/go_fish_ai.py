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
        same_turn_failed_ranks: tuple[Rank, ...] = (),
        books_claimed_by_rank: dict[Rank, int] | None = None,
    ) -> tuple[str, Rank]:
        """Return (target_name, rank) to ask for. `my_hand` must be non-empty.

        `same_turn_failed_ranks` lists (oldest-first) the ranks this player
        has already asked and missed on earlier in this same continuous "go
        again" turn — re-asking one of those is a *guaranteed* miss, since a
        target's hand cannot change mid-turn while it isn't their turn. How
        much of that list a tier actually remembers is itself a difficulty
        lever: EASY ignores it entirely (may repeat itself); MEDIUM only
        remembers its single most recent miss (a short attention span);
        HARD remembers every miss so far this turn.

        `books_claimed_by_rank` is how many books of each rank have already
        been claimed by *any* player (books are laid face-up on the table
        in real Go Fish, so this is public information, not a peek at
        anyone's hand) — see `_base_weight` for why this matters under the
        pair-based book rule.
        """
        candidate_ranks = list(my_hand.ranks_present())
        if not candidate_ranks:
            raise ValueError("cannot ask with an empty hand")
        if not opponent_names:
            raise ValueError("no opponents to ask")
        books_claimed_by_rank = books_claimed_by_rank or {}

        exclude = self._same_turn_exclusions(same_turn_failed_ranks)
        smarter = [r for r in candidate_ranks if r not in exclude]
        if smarter:
            candidate_ranks = smarter

        rank_weights = self._rank_weights(
            my_hand, candidate_ranks, opponent_names, history, books_claimed_by_rank
        )
        rank = self.weighted_choice(candidate_ranks, rank_weights)

        opponent_weights = self._opponent_weights(opponent_names, rank, history)
        target = self.weighted_choice(opponent_names, opponent_weights)
        return target, rank

    def _same_turn_exclusions(self, same_turn_failed_ranks: tuple[Rank, ...]) -> set[Rank]:
        if self.difficulty is Difficulty.EASY:
            return set()
        if self.difficulty is Difficulty.MEDIUM:
            return {same_turn_failed_ranks[-1]} if same_turn_failed_ranks else set()
        return set(same_turn_failed_ranks)  # HARD: remembers every miss this turn

    def _rank_weights(
        self,
        hand: Hand,
        ranks: list[Rank],
        opponent_names: list[str],
        history: list[AskRecord],
        books_claimed_by_rank: dict[Rank, int],
    ) -> list[float]:
        weights = []
        for rank in ranks:
            count = hand.count_of_rank(rank)
            claimed = books_claimed_by_rank.get(rank, 0)
            weights.append(
                self._base_weight(count, claimed) * self._best_opponent_multiplier(rank, opponent_names, history)
            )
        return weights

    def _base_weight(self, count: int, books_claimed: int) -> float:
        """Weight a candidate rank by how many copies are still unseen:
        neither in this hand nor already paired off into a claimed book by
        anyone (4 - count - 2*books_claimed). More copies still out there
        (in an opponent's hand or the stock) means a higher chance an
        opponent is holding at least one, i.e. a higher hit rate.

        Under the pair-based book rule, a rank you're holding always has
        count == 1 in practice (2 auto-claims the instant it forms, so a
        hand can never sit on 2+ of a rank) -- so count alone can't tell
        candidate ranks apart anymore, unlike the old 4-of-a-kind rule
        where it was the main signal. `books_claimed` recovers a real
        signal: once a rank's first book has been claimed (by anyone --
        books are laid face-up on the table, this is public), only 2
        copies of that rank remain in circulation instead of 4, so it's a
        meaningfully worse bet than a rank nobody's touched yet.
        """
        if self.difficulty is Difficulty.EASY:
            return 1.0
        remaining_unseen = max(0, 4 - count - 2 * books_claimed)
        if self.difficulty is Difficulty.MEDIUM:
            return 1.0 + remaining_unseen
        return 1.0 + remaining_unseen**2  # HARD leans into it harder

    def _best_opponent_multiplier(
        self, rank: Rank, opponent_names: list[str], history: list[AskRecord]
    ) -> float:
        """How promising is this rank, at best, across all opponents? Folding
        this into rank selection (rather than only opponent selection)
        matters most in 2-player games, where there's only ever one
        opponent to pick from and opponent-weighting alone would otherwise
        never actually influence a decision.
        """
        if self.difficulty is Difficulty.EASY:
            return 1.0
        discount = 0.6 if self.difficulty is Difficulty.MEDIUM else 0.3
        best = 0.0
        for name in opponent_names:
            confirmed_absent = any(h.target == name and h.rank == rank for h in history)
            best = max(best, discount if confirmed_absent else 1.0)
        return best if best > 0 else 1.0

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
