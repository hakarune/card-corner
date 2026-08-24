import pytest

from core.ai.base import Difficulty
from core.card import Card, Rank, Suit, make_odd_card
from games.old_maid.game import MAX_TURNS, OldMaidGame


def make_game(seed=7, players=("Ellie", "Fox")):
    return OldMaidGame(
        list(players),
        ai_difficulties={n: Difficulty.EASY for n in players if n != players[0]},
        seed=seed,
    )


def all_cards_accounted_for(game: OldMaidGame) -> bool:
    live = []
    for p in game.players.values():
        live.extend(p.hand.cards)
    if len(live) != len(set(live)):
        return False
    total = len(live) + 2 * sum(len(p.books) for p in game.players.values())
    return total == 49


def test_deal_and_initial_pairing_accounts_for_all_cards():
    game = make_game()
    assert all_cards_accounted_for(game)


def test_odd_card_is_never_paired_off():
    game = make_game()
    for p in game.players.values():
        assert p.hand.cards.count(make_odd_card()) <= 1
    holders = [p for p in game.players.values() if make_odd_card() in p.hand.cards]
    assert len(holders) == 1


def test_cannot_draw_out_of_turn():
    game = make_game()
    not_current = [n for n in game.order if n != game.current_player_name][0]
    with pytest.raises(ValueError):
        game.draw(not_current, game.current_player_name)


def test_cannot_draw_from_self():
    game = make_game()
    me = game.current_player_name
    with pytest.raises(ValueError):
        game.draw(me, me)


def test_cannot_draw_from_unknown_player():
    game = make_game()
    me = game.current_player_name
    with pytest.raises(ValueError):
        game.draw(me, "Nobody")


def test_cannot_draw_from_empty_handed_player():
    game = make_game()
    p1, p2 = game.order
    game.players[p2].hand.cards = []
    game.turn_index = game.order.index(p1)
    with pytest.raises(ValueError):
        game.draw(p1, p2)


def test_drawing_a_matching_rank_pairs_and_discards():
    game = make_game()
    p1, p2 = game.order
    game.players[p1].hand.cards = [Card(suit=Suit.HEARTS, rank=Rank.FIVE)]
    game.players[p2].hand.cards = [Card(suit=Suit.CLUBS, rank=Rank.FIVE)]
    game.turn_index = game.order.index(p1)

    result = game.draw(p1, p2)

    assert result.paired_ranks == [Rank.FIVE]
    assert game.players[p1].hand.is_empty()
    assert Rank.FIVE in game.players[p1].books


def test_drawing_a_non_matching_rank_keeps_both_cards():
    game = make_game()
    p1, p2 = game.order
    game.players[p1].hand.cards = [Card(suit=Suit.HEARTS, rank=Rank.FIVE)]
    game.players[p2].hand.cards = [Card(suit=Suit.CLUBS, rank=Rank.NINE)]
    game.turn_index = game.order.index(p1)

    result = game.draw(p1, p2)

    assert result.paired_ranks == []
    assert len(game.players[p1].hand) == 2


def test_multiple_of_same_rank_discards_only_complete_pairs():
    game = make_game()
    p1, p2 = game.order
    game.players[p1].hand.cards = [
        Card(suit=Suit.HEARTS, rank=Rank.FIVE),
        Card(suit=Suit.CLUBS, rank=Rank.FIVE),
    ]
    game.players[p2].hand.cards = [Card(suit=Suit.SPADES, rank=Rank.FIVE)]
    game.turn_index = game.order.index(p1)

    result = game.draw(p1, p2)

    # 3 fives briefly -> one pair discarded, one five left over.
    assert result.paired_ranks == [Rank.FIVE]
    assert len(game.players[p1].hand) == 1
    assert game.players[p1].hand.has_rank(Rank.FIVE)


def test_turn_passes_to_next_active_player():
    game = make_game(players=("A", "B", "C"))
    # B keeps a card after the draw (2 held, non-matching), so B stays active
    # and turn order simply advances one seat, A -> B.
    game.players["B"].hand.cards = [
        Card(suit=Suit.HEARTS, rank=Rank.FIVE),
        Card(suit=Suit.CLUBS, rank=Rank.JACK),
    ]
    game.players["C"].hand.cards = [Card(suit=Suit.CLUBS, rank=Rank.NINE)]
    game.players["A"].hand.cards = [Card(suit=Suit.SPADES, rank=Rank.TWO)]
    game.turn_index = game.order.index("A")

    game.draw("A", "B")

    assert game.current_player_name == "B"


def test_turn_skips_players_with_empty_hands():
    game = make_game(players=("A", "B", "C"))
    game.players["A"].hand.cards = [Card(suit=Suit.SPADES, rank=Rank.TWO)]
    game.players["B"].hand.cards = []  # already out
    # C keeps a card after the draw so it remains active and B is skipped.
    game.players["C"].hand.cards = [
        Card(suit=Suit.CLUBS, rank=Rank.NINE),
        Card(suit=Suit.HEARTS, rank=Rank.JACK),
    ]
    game.turn_index = game.order.index("A")

    game.draw("A", "C")

    assert game.current_player_name == "C"


def test_the_player_left_holding_the_odd_card_is_recorded_as_the_loser():
    # Spec §9's explicit ask: being left holding Old Maid is a LOSS, not a
    # win. p1 is the only active player left and is the one still holding
    # the odd (Old Maid) card -- everyone else has already emptied their
    # hand via pairing -- so p1 must be the loser, not the winner.
    game = make_game()
    p1, p2 = game.order
    game.players[p1].hand.cards = [make_odd_card()]
    game.players[p2].hand.cards = []
    game._check_game_over()
    assert game.game_over
    assert game.loser == p1
    assert game.players[game.loser].hand.cards == [make_odd_card()]


def test_game_ends_stalemate_at_turn_cap():
    game = make_game()
    game.turn_count = MAX_TURNS
    game._check_game_over()
    assert game.game_over


def test_initial_deal_with_four_of_a_kind_discards_both_pairs_at_once():
    game = make_game()
    p1 = game.order[0]
    game.players[p1].books = []  # ignore whatever the real initial deal happened to pair
    game.players[p1].hand.cards = [
        Card(suit=Suit.HEARTS, rank=Rank.FIVE),
        Card(suit=Suit.CLUBS, rank=Rank.FIVE),
        Card(suit=Suit.SPADES, rank=Rank.FIVE),
        Card(suit=Suit.DIAMONDS, rank=Rank.FIVE),
    ]
    cleared = game._discard_pairs(p1)
    assert cleared == [Rank.FIVE, Rank.FIVE]
    assert game.players[p1].hand.is_empty()
    assert game.players[p1].books.count(Rank.FIVE) == 2


def test_stalemate_reached_through_real_play_without_crashing():
    # Two players who can never end up holding a matching rank together, so
    # nothing ever progresses toward a pair or an empty hand: real draw()
    # calls should still run cleanly all the way to MAX_TURNS.
    game = make_game()
    p1, p2 = game.order
    game.players[p1].hand.cards = [
        Card(suit=Suit.HEARTS, rank=Rank.TWO),
        Card(suit=Suit.CLUBS, rank=Rank.THREE),
    ]
    game.players[p2].hand.cards = [
        Card(suit=Suit.HEARTS, rank=Rank.FOUR),
        Card(suit=Suit.CLUBS, rank=Rank.FIVE),
    ]
    game.turn_index = game.order.index(p1)
    game.game_over = False

    turns = 0
    while not game.game_over and turns < MAX_TURNS + 5:
        target = game.other_active_names(game.current_player_name)[0]
        game.draw(game.current_player_name, target)
        turns += 1

    assert game.game_over
    assert game.turn_count >= MAX_TURNS
    assert game.stalemate


def test_three_player_simultaneous_double_empty_leaves_sentinel_holder_as_sole_survivor():
    # P and Q are each down to a single, non-matching-with-each-other card;
    # the sentinel-holding third player R is untouched. A draw that empties
    # both P and Q's hands at once should still correctly land on exactly
    # one active player: R.
    game = make_game(players=("P", "Q", "R"))
    game.players["P"].hand.cards = [Card(suit=Suit.HEARTS, rank=Rank.SIX)]
    game.players["Q"].hand.cards = [Card(suit=Suit.CLUBS, rank=Rank.SIX)]
    game.players["R"].hand.cards = [make_odd_card(), Card(suit=Suit.SPADES, rank=Rank.EIGHT)]
    game.turn_index = game.order.index("P")

    result = game.draw("P", "Q")

    assert result.paired_ranks == [Rank.SIX]
    assert game.players["P"].hand.is_empty()
    assert game.players["Q"].hand.is_empty()
    assert game.active_player_names() == ["R"]


def test_no_card_loss_or_duplication_across_a_full_random_ai_vs_ai_game():
    game = OldMaidGame(
        ["Fox1", "Fox2"],
        ai_difficulties={"Fox1": Difficulty.HARD, "Fox2": Difficulty.EASY},
        seed=321,
    )
    turns = 0
    while not game.game_over and turns < MAX_TURNS + 5:
        assert all_cards_accounted_for(game)
        game.take_ai_turn()
        turns += 1
    assert game.game_over
    assert all_cards_accounted_for(game)
    assert game.loser is not None
    assert game.players[game.loser].hand.cards == [make_odd_card()]


@pytest.mark.parametrize("num_players", [3, 4])
def test_no_card_loss_or_duplication_with_3_or_4_players(num_players):
    names = ["Fox1", "Fox2", "Fox3", "Fox4"][:num_players]
    difficulties = [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD, Difficulty.EASY]
    game = OldMaidGame(
        names, ai_difficulties={n: d for n, d in zip(names, difficulties)}, seed=55
    )
    turns = 0
    while not game.game_over and turns < MAX_TURNS + 5:
        assert all_cards_accounted_for(game)
        game.take_ai_turn()
        turns += 1
    assert game.game_over
    assert all_cards_accounted_for(game)
    assert game.players[game.loser].hand.cards == [make_odd_card()]
