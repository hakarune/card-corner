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
    # total count (hands + stock + 4*books) matches 52.
    live = list(game.stock)
    for p in game.players.values():
        live.extend(p.hand.cards)
    if len(live) != len(set(live)):
        return False
    total = len(live) + 4 * sum(len(p.books) for p in game.players.values())
    return total == 52


def test_deal_sizes_two_players():
    game = make_game()
    total_hand = sum(len(p.hand) for p in game.players.values())
    assert total_hand + len(game.stock) == 52
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
    assert game.players[p1].hand.count_of_rank(Rank.SEVEN) == 3
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
    game = make_game()
    p1, p2 = game.order
    game.players[p1].hand.cards = [Card(suit=Suit.HEARTS, rank=Rank.SEVEN)]
    game.players[p2].hand.cards = [Card(suit=Suit.CLUBS, rank=Rank.KING)]
    game.stock = [Card(suit=Suit.SPADES, rank=Rank.SEVEN)]
    game.turn_index = game.order.index(p1)

    result = game.ask(p1, p2, Rank.SEVEN)

    assert result.asker_drew_matched
    assert result.went_again
    assert game.current_player_name == p1


def test_book_is_claimed_automatically():
    game = make_game()
    p1, p2 = game.order
    game.players[p1].hand.cards = [
        Card(suit=Suit.HEARTS, rank=Rank.SEVEN),
        Card(suit=Suit.CLUBS, rank=Rank.SEVEN),
        Card(suit=Suit.DIAMONDS, rank=Rank.SEVEN),
    ]
    game.players[p2].hand.cards = [Card(suit=Suit.SPADES, rank=Rank.SEVEN)]
    game.turn_index = game.order.index(p1)
    game.stock = []

    result = game.ask(p1, p2, Rank.SEVEN)

    assert Rank.SEVEN in result.books_claimed_by_asker
    assert Rank.SEVEN in game.players[p1].books
    assert not game.players[p1].hand.has_rank(Rank.SEVEN)
    assert game.players[p1].score == 1


def test_empty_hand_gets_free_draw_on_turn_start():
    game = make_game()
    p1, p2 = game.order
    game.players[p1].hand.cards = []
    game.players[p2].hand.cards = [Card(suit=Suit.CLUBS, rank=Rank.KING)]
    game.stock = [Card(suit=Suit.SPADES, rank=Rank.TWO)]
    game.turn_index = game.order.index(p1)

    game._ensure_current_player_can_act()

    assert not game.players[p1].hand.is_empty()


def test_game_ends_when_all_13_books_claimed():
    game = make_game()
    for name in game.order:
        game.players[name].hand.cards = []
    for i, rank in enumerate(list(Rank)):
        game.players[game.order[i % 2]].books.append(rank)
    game._check_game_over()
    assert game.game_over
    assert sum(len(p.books) for p in game.players.values()) == 13


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
    # Asker's whole hand is exactly the 4th card of a book; the hit claims
    # the book and empties their hand, which should trigger a free redraw
    # from the stock so they have a card to keep playing with.
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

    assert Rank.SEVEN in result.books_claimed_by_asker
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

    assert Rank.SEVEN in result.books_claimed_by_asker
    assert not result.asker_drew
    assert game.players[p1].hand.is_empty()
    assert not result.went_again


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
