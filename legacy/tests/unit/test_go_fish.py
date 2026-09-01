import random

import pytest

from core.ai.base import Difficulty
from core.card import Card, Rank, Suit
from games.go_fish.game import GoFishGame, MAX_TURNS


def make_game(seed=7):
    return GoFishGame(["Ellie", "Fox"], ai_difficulties={"Fox": Difficulty.EASY}, seed=seed)


def all_cards_accounted_for(game: GoFishGame) -> bool:
    seen = list(game.stock)
    for p in game.players.values():
        seen.extend(p.hand.cards)
        seen.extend(
            c for rank in p.books for c in [Card(suit=s, rank=rank) for s in Suit]
        )
    # Books remove cards from play entirely rather than tracking exact card
    # identities, so instead just check hand+stock cards are unique and the
    # total count (hands + stock + 2*books, since a book is now a pair)
    # matches 52.
    live = list(game.stock)
    for p in game.players.values():
        live.extend(p.hand.cards)
    if len(live) != len(set(live)):
        return False
    total = len(live) + 2 * sum(len(p.books) for p in game.players.values())
    return total == 52


def test_deal_sizes_two_players():
    # With books as pairs, a 7-card initial deal can easily contain a pair
    # and auto-claim a book right away -- so the invariant has to account
    # for cards already set aside as books, not just hand+stock.
    game = make_game()
    assert all_cards_accounted_for(game)


def test_cannot_ask_out_of_turn():
    game = make_game()
    not_current = [n for n in game.order if n != game.current_player_name][0]
    with pytest.raises(ValueError):
        game.ask(not_current, game.current_player_name, Rank.ACE)


def test_cannot_ask_self():
    game = make_game()
    me = game.current_player_name
    rank = game.legal_ranks(me)[0]
    with pytest.raises(ValueError):
        game.ask(me, me, rank)


def test_cannot_ask_for_rank_not_in_hand():
    game = make_game()
    me = game.current_player_name
    other = game.other_player_names(me)[0]
    held_ranks = set(game.legal_ranks(me))
    missing_rank = next(r for r in Rank if r not in held_ranks)
    with pytest.raises(ValueError):
        game.ask(me, other, missing_rank)


def test_cannot_ask_unknown_player():
    game = make_game()
    me = game.current_player_name
    rank = game.legal_ranks(me)[0]
    with pytest.raises(ValueError):
        game.ask(me, "Nobody", rank)


def test_successful_ask_transfers_all_cards_and_goes_again():
    # p1 holds 1 seven; p2 holds 2. All 3 transfer, immediately claiming one
    # pair-book (2 of the 3) and leaving exactly 1 seven behind in hand --
    # books are pairs now, not 4-of-a-kind, so this auto-claims mid-ask.
    game = make_game()
    p1, p2 = game.order
    game.players[p1].hand.cards = [
        Card(suit=Suit.HEARTS, rank=Rank.SEVEN),
        Card(suit=Suit.CLUBS, rank=Rank.TWO),
    ]
    game.players[p2].hand.cards = [
        Card(suit=Suit.SPADES, rank=Rank.SEVEN),
        Card(suit=Suit.DIAMONDS, rank=Rank.SEVEN),
        Card(suit=Suit.CLUBS, rank=Rank.KING),
    ]
    game.turn_index = game.order.index(p1)
    game.stock = []

    result = game.ask(p1, p2, Rank.SEVEN)

    assert result.cards_transferred == 2
    assert result.went_again
    assert game.current_player_name == p1
    assert result.books_claimed_by_asker == [Rank.SEVEN]
    assert game.players[p1].hand.count_of_rank(Rank.SEVEN) == 1
    assert not game.players[p2].hand.has_rank(Rank.SEVEN)


def test_failed_ask_draws_and_passes_turn_on_non_match():
    game = make_game()
    p1, p2 = game.order
    game.players[p1].hand.cards = [Card(suit=Suit.HEARTS, rank=Rank.SEVEN)]
    game.players[p2].hand.cards = [Card(suit=Suit.CLUBS, rank=Rank.KING)]
    game.stock = [Card(suit=Suit.SPADES, rank=Rank.TWO)]
    game.turn_index = game.order.index(p1)

    result = game.ask(p1, p2, Rank.SEVEN)

    assert result.cards_transferred == 0
    assert result.asker_drew
    assert not result.asker_drew_matched
    assert not result.went_again
    assert game.current_player_name == p2
    assert game.players[p1].hand.has_rank(Rank.TWO)


def test_failed_ask_draw_matching_rank_goes_again():
    # An extra, unrelated card keeps the hand non-empty after the pair
    # auto-claims, so this specifically tests "a match keeps your turn"
    # rather than colliding with the separate empty-hand-and-no-stock case
    # (covered by test_failed_ask_draw_matching_rank_that_empties_hand_and_stock_ends_turn).
    game = make_game()
    p1, p2 = game.order
    game.players[p1].hand.cards = [
        Card(suit=Suit.HEARTS, rank=Rank.SEVEN),
        Card(suit=Suit.CLUBS, rank=Rank.TWO),
    ]
    game.players[p2].hand.cards = [Card(suit=Suit.CLUBS, rank=Rank.KING)]
    game.stock = [Card(suit=Suit.SPADES, rank=Rank.SEVEN)]
    game.turn_index = game.order.index(p1)

    result = game.ask(p1, p2, Rank.SEVEN)

    assert result.asker_drew_matched
    assert result.books_claimed_by_asker == [Rank.SEVEN]
    assert result.went_again
    assert game.current_player_name == p1
    assert game.players[p1].hand.has_rank(Rank.TWO)


def test_failed_ask_draw_matching_rank_that_empties_hand_and_stock_ends_turn():
    # Drawing the exact match completes the pair-book and empties the
    # hand; with the stock also exhausted there's nothing to redraw with,
    # so unlike the non-empty case above, the turn correctly ends here.
    game = make_game()
    p1, p2 = game.order
    game.players[p1].hand.cards = [Card(suit=Suit.HEARTS, rank=Rank.SEVEN)]
    game.players[p2].hand.cards = [Card(suit=Suit.CLUBS, rank=Rank.KING)]
    game.stock = [Card(suit=Suit.SPADES, rank=Rank.SEVEN)]
    game.turn_index = game.order.index(p1)

    result = game.ask(p1, p2, Rank.SEVEN)

    assert result.asker_drew_matched
    assert result.books_claimed_by_asker == [Rank.SEVEN]
    assert game.players[p1].hand.is_empty()
    assert not result.went_again
    assert game.current_player_name == p2


def test_book_is_claimed_automatically():
    # A book is a pair now: p1 holds 1 seven, asks p2 (who holds 1), and the
    # transfer alone completes the pair. score/books use a before/after
    # delta since the initial 7-card deal can itself contain a pair and
    # auto-claim a book before this test's setup even runs.
    game = make_game()
    p1, p2 = game.order
    score_before = game.players[p1].score
    game.players[p1].hand.cards = [Card(suit=Suit.HEARTS, rank=Rank.SEVEN)]
    game.players[p2].hand.cards = [Card(suit=Suit.SPADES, rank=Rank.SEVEN)]
    game.turn_index = game.order.index(p1)
    game.stock = []

    result = game.ask(p1, p2, Rank.SEVEN)

    assert result.books_claimed_by_asker == [Rank.SEVEN]
    assert Rank.SEVEN in game.players[p1].books
    assert not game.players[p1].hand.has_rank(Rank.SEVEN)
    assert game.players[p1].score == score_before + 1


def test_rank_with_four_copies_can_claim_two_books_at_once():
    # If all 4 copies of a rank land in one hand simultaneously (e.g. the
    # initial deal), that's 2 books claimed at once, not 1.
    game = make_game()
    p1, p2 = game.order
    score_before = game.players[p1].score
    game.players[p1].hand.cards = [
        Card(suit=Suit.HEARTS, rank=Rank.SEVEN),
        Card(suit=Suit.CLUBS, rank=Rank.SEVEN),
        Card(suit=Suit.DIAMONDS, rank=Rank.SEVEN),
    ]
    game.players[p2].hand.cards = [Card(suit=Suit.SPADES, rank=Rank.SEVEN)]
    game.turn_index = game.order.index(p1)
    game.stock = []

    result = game.ask(p1, p2, Rank.SEVEN)

    assert result.books_claimed_by_asker == [Rank.SEVEN, Rank.SEVEN]
    assert game.players[p1].books.count(Rank.SEVEN) == 2
    assert not game.players[p1].hand.has_rank(Rank.SEVEN)
    assert game.players[p1].score == score_before + 2


def test_empty_hand_gets_free_draw_on_turn_start():
    game = make_game()
    p1, p2 = game.order
    game.players[p1].hand.cards = []
    game.players[p2].hand.cards = [Card(suit=Suit.CLUBS, rank=Rank.KING)]
    game.stock = [Card(suit=Suit.SPADES, rank=Rank.TWO)]
    game.turn_index = game.order.index(p1)

    game._ensure_current_player_can_act()

    assert not game.players[p1].hand.is_empty()


def test_game_ends_when_all_26_books_claimed():
    game = make_game()
    for name in game.order:
        game.players[name].hand.cards = []
        game.players[name].books = []  # the initial deal may have already auto-claimed some
    for i, rank in enumerate(list(Rank) * 2):  # 2 books per rank x 13 ranks = 26
        game.players[game.order[i % 2]].books.append(rank)
    game.game_over = False
    game._check_game_over()
    assert game.game_over
    assert sum(len(p.books) for p in game.players.values()) == 26


def test_game_ends_stalemate_at_turn_cap():
    game = make_game()
    game.turn_count = MAX_TURNS
    game._check_game_over()
    assert game.game_over


def test_no_card_duplication_across_a_full_random_ai_vs_ai_game():
    game = GoFishGame(
        ["Fox1", "Fox2"],
        ai_difficulties={"Fox1": Difficulty.HARD, "Fox2": Difficulty.EASY},
        seed=123,
    )
    turns = 0
    while not game.game_over and turns < MAX_TURNS + 5:
        assert all_cards_accounted_for(game)
        game.take_ai_turn()
        turns += 1
    assert game.game_over
    assert all_cards_accounted_for(game)


@pytest.mark.parametrize("num_players", [3, 4])
def test_no_card_duplication_across_a_full_random_game_with_3_or_4_players(num_players):
    names = ["Fox1", "Fox2", "Fox3", "Fox4"][:num_players]
    difficulties = [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD, Difficulty.EASY]
    game = GoFishGame(
        names,
        ai_difficulties={n: d for n, d in zip(names, difficulties)},
        seed=42,
    )
    turns = 0
    while not game.game_over and turns < MAX_TURNS + 5:
        assert all_cards_accounted_for(game)
        game.take_ai_turn()
        turns += 1
    assert game.game_over
    assert all_cards_accounted_for(game)


def test_turn_count_reaches_stalemate_cap_through_real_play_without_crashing():
    # Deliberately adversarial-but-legal state: two players who can only
    # ever miss each other (disjoint held ranks) and an empty stock, so
    # nothing ever progresses toward a book or an empty hand. This should
    # run all the way to MAX_TURNS via real ask() calls and stop cleanly,
    # rather than looping forever.
    game = GoFishGame(
        ["Fox1", "Fox2"], ai_difficulties={"Fox1": Difficulty.EASY, "Fox2": Difficulty.EASY}, seed=1
    )
    game.players["Fox1"].hand.cards = [
        Card(suit=Suit.HEARTS, rank=Rank.TWO),
        Card(suit=Suit.CLUBS, rank=Rank.TWO),
    ]
    game.players["Fox2"].hand.cards = [
        Card(suit=Suit.HEARTS, rank=Rank.THREE),
        Card(suit=Suit.CLUBS, rank=Rank.THREE),
    ]
    game.stock = []
    game.turn_index = game.order.index("Fox1")
    game.game_over = False

    turns = 0
    while not game.game_over and turns < MAX_TURNS + 5:
        game.take_ai_turn()
        turns += 1

    assert game.game_over
    assert game.turn_count >= MAX_TURNS
    assert game.stalemate


def test_hit_that_empties_hand_triggers_free_redraw_and_keeps_the_turn():
    # Asker holds 3 sevens; the 4th arrives via the ask, completing both
    # pair-books at once (4 // 2 = 2) and fully emptying their hand of
    # sevens, which should trigger a free redraw from the stock so they
    # have a card to keep playing with.
    game = make_game()
    p1, p2 = game.order
    game.players[p1].hand.cards = [
        Card(suit=Suit.HEARTS, rank=Rank.SEVEN),
        Card(suit=Suit.CLUBS, rank=Rank.SEVEN),
        Card(suit=Suit.DIAMONDS, rank=Rank.SEVEN),
    ]
    game.players[p2].hand.cards = [Card(suit=Suit.SPADES, rank=Rank.SEVEN)]
    game.stock = [Card(suit=Suit.SPADES, rank=Rank.NINE)]
    game.turn_index = game.order.index(p1)

    result = game.ask(p1, p2, Rank.SEVEN)

    assert result.books_claimed_by_asker == [Rank.SEVEN, Rank.SEVEN]
    assert result.asker_drew
    assert not game.players[p1].hand.is_empty()
    assert game.players[p1].hand.has_rank(Rank.NINE)
    # Still holding a card (from the free redraw) -> they go again.
    assert result.went_again
    assert game.current_player_name == p1


def test_hit_that_empties_hand_with_empty_stock_ends_the_turn():
    game = make_game()
    p1, p2 = game.order
    game.players[p1].hand.cards = [
        Card(suit=Suit.HEARTS, rank=Rank.SEVEN),
        Card(suit=Suit.CLUBS, rank=Rank.SEVEN),
        Card(suit=Suit.DIAMONDS, rank=Rank.SEVEN),
    ]
    game.players[p2].hand.cards = [Card(suit=Suit.SPADES, rank=Rank.SEVEN)]
    game.stock = []
    game.turn_index = game.order.index(p1)

    result = game.ask(p1, p2, Rank.SEVEN)

    assert result.books_claimed_by_asker == [Rank.SEVEN, Rank.SEVEN]
    assert not result.asker_drew
    assert game.players[p1].hand.is_empty()
    assert not result.went_again


def test_turn_failed_ranks_accumulate_within_a_turn_and_reset_when_it_ends():
    game = make_game()
    p1, p2 = game.order
    game.players[p1].hand.cards = [
        Card(suit=Suit.HEARTS, rank=Rank.TWO),
        Card(suit=Suit.CLUBS, rank=Rank.THREE),
    ]
    game.players[p2].hand.cards = [Card(suit=Suit.SPADES, rank=Rank.FIVE)]
    # pop() takes from the end: TWO is drawn first (matches the first ask,
    # so the turn continues), SEVEN is drawn second (doesn't match the
    # second ask, so the turn ends).
    game.stock = [Card(suit=Suit.DIAMONDS, rank=Rank.SEVEN), Card(suit=Suit.CLUBS, rank=Rank.TWO)]
    game.turn_index = game.order.index(p1)

    first = game.ask(p1, p2, Rank.TWO)
    assert first.cards_transferred == 0
    assert first.asker_drew_matched
    assert first.went_again
    assert game._turn_failed_ranks == [Rank.TWO]
    assert game.current_player_name == p1  # still p1's turn

    second = game.ask(p1, p2, Rank.THREE)
    assert second.cards_transferred == 0
    assert not second.asker_drew_matched
    assert not second.went_again
    assert game._turn_failed_ranks == []  # reset now that the turn actually ended
    assert game.current_player_name == p2


def test_unseeded_games_produce_different_ai_play_sequences():
    # No explicit seed -> each GoFishGame draws its master RNG from OS
    # entropy, so two unseeded games (even with identical starting hands
    # forced below) should not reliably replay the same sequence of AI asks.
    def play_out(game):
        seq = []
        turns = 0
        while not game.game_over and turns < 30:
            r = game.take_ai_turn()
            seq.append((r.asker, r.target, r.rank))
            turns += 1
        return seq

    game_a = GoFishGame(
        ["Fox1", "Fox2"], ai_difficulties={"Fox1": Difficulty.EASY, "Fox2": Difficulty.EASY}
    )
    game_b = GoFishGame(
        ["Fox1", "Fox2"], ai_difficulties={"Fox1": Difficulty.EASY, "Fox2": Difficulty.EASY}
    )
    seq_a = play_out(game_a)
    seq_b = play_out(game_b)
    assert seq_a != seq_b


def test_books_claimed_by_rank_counts_across_all_players():
    game = make_game()
    p1, p2 = game.order
    game.players[p1].books = [Rank.SEVEN, Rank.SEVEN, Rank.KING]
    game.players[p2].books = [Rank.SEVEN]
    counts = game.books_claimed_by_rank()
    assert counts[Rank.SEVEN] == 3
    assert counts[Rank.KING] == 1
    assert Rank.TWO not in counts  # never claimed by anyone -> absent, not zero


def _two_ai_game(seed):
    return GoFishGame(
        ["Fox1", "Fox2"], ai_difficulties={"Fox1": Difficulty.EASY, "Fox2": Difficulty.EASY}, seed=seed
    )


def test_decide_ai_ask_is_a_pure_query_that_does_not_advance_the_turn():
    # decide_ai_ask() exists so a screen can announce the AI's request
    # (highlight + audio cue) before it actually executes -- it must not
    # itself move any cards or change whose turn it is.
    game = _two_ai_game(seed=3)
    asker = game.current_player_name
    hand_before = list(game.players[asker].hand.cards)

    target, rank = game.decide_ai_ask()

    assert game.current_player_name == asker
    assert game.players[asker].hand.cards == hand_before
    assert game.players[asker].hand.has_rank(rank)  # a legal ask: a rank it actually holds
    assert target in game.other_player_names(asker)


def test_decide_ai_ask_then_ask_matches_take_ai_turn_for_an_identical_game():
    # take_ai_turn() is just decide_ai_ask() + ask() glued together;
    # splitting them for the screen's visible-request flow must not change
    # the actual outcome for an identical game state.
    game_direct = _two_ai_game(seed=11)
    game_split = _two_ai_game(seed=11)

    result_direct = game_direct.take_ai_turn()

    asker = game_split.current_player_name
    target, rank = game_split.decide_ai_ask()
    result_split = game_split.ask(asker, target, rank)

    assert (result_direct.asker, result_direct.target, result_direct.rank) == (
        result_split.asker, result_split.target, result_split.rank,
    )
    assert result_direct.cards_transferred == result_split.cards_transferred


def test_claim_books_processes_ranks_in_sorted_order_not_set_order(monkeypatch):
    # Defense-in-depth companion to the identical fix in Old Maid's
    # _discard_pairs (which the same set-order-dependent pattern actually
    # broke, via a positional blind draw a reordered hand throws off). Go
    # Fish's own draw is positional-on-the-shared-stock rather than on a
    # hand this loop reorders, so this hasn't manifested a real bug here --
    # but it's the exact code smell the project now knows is dangerous, so
    # sorted anyway rather than trusting set iteration order.
    game = make_game()
    p1 = game.order[0]
    player = game.players[p1]
    player.hand.cards = [
        Card(suit=Suit.HEARTS, rank=Rank.KING), Card(suit=Suit.CLUBS, rank=Rank.KING),
        Card(suit=Suit.HEARTS, rank=Rank.ACE), Card(suit=Suit.CLUBS, rank=Rank.ACE),
        Card(suit=Suit.HEARTS, rank=Rank.SEVEN), Card(suit=Suit.CLUBS, rank=Rank.SEVEN),
    ]

    class AdversarialOrderSet(set):
        def __iter__(self):
            return iter([Rank.KING, Rank.ACE, Rank.SEVEN])

    monkeypatch.setattr(
        player.hand, "ranks_present",
        lambda: AdversarialOrderSet({Rank.KING, Rank.ACE, Rank.SEVEN}),
    )

    claimed = game._claim_books(p1)
    assert claimed == [Rank.ACE, Rank.SEVEN, Rank.KING]
