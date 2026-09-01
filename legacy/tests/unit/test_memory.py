import pytest

from core.ai.base import Difficulty
from games.memory.game import MAX_TURNS, MemoryGame


def make_game(seed=7, num_pairs=6):
    return MemoryGame(
        ["Ellie", "Fox"], num_pairs=num_pairs, ai_difficulties={"Fox": Difficulty.EASY}, seed=seed
    )


def test_board_has_correct_size_and_no_positions_pre_matched():
    game = make_game(num_pairs=8)
    assert len(game.board) == 16
    assert game.matched == set()
    assert len(game.unflipped_positions()) == 16


def test_cannot_flip_out_of_turn():
    game = make_game()
    not_current = [n for n in game.order if n != game.current_player_name][0]
    with pytest.raises(ValueError):
        game.flip_two(not_current, 0, 1)


def test_cannot_flip_same_position_twice():
    game = make_game()
    with pytest.raises(ValueError):
        game.flip_two(game.current_player_name, 3, 3)


def test_cannot_flip_out_of_range_position():
    game = make_game(num_pairs=6)
    me = game.current_player_name
    with pytest.raises(ValueError):
        game.flip_two(me, 0, 99)
    with pytest.raises(ValueError):
        game.flip_two(me, -1, 2)


def test_cannot_flip_already_matched_position():
    game = make_game()
    me = game.current_player_name
    # Force a known match by finding two positions with the same rank.
    pos1 = 0
    rank1 = game.board[pos1].rank
    pos2 = next(i for i in range(1, len(game.board)) if game.board[i].rank == rank1)
    game.flip_two(me, pos1, pos2)
    assert pos1 in game.matched
    with pytest.raises(ValueError):
        game.flip_two(game.current_player_name, pos1, pos1 + 1 if pos1 + 1 != pos2 else pos1 + 2)


def test_matching_flip_scores_and_goes_again():
    game = make_game()
    me = game.current_player_name
    pos1 = 0
    rank1 = game.board[pos1].rank
    pos2 = next(i for i in range(1, len(game.board)) if game.board[i].rank == rank1)

    result = game.flip_two(me, pos1, pos2)

    assert result.matched
    assert result.went_again
    assert game.current_player_name == me
    assert game.players[me].score == 1
    assert rank1 in game.players[me].books
    assert pos1 in game.matched and pos2 in game.matched


def test_non_matching_flip_passes_turn_and_still_records_public_memory():
    game = make_game()
    me = game.current_player_name
    other = [n for n in game.order if n != me][0]
    pos1 = 0
    rank1 = game.board[pos1].rank
    pos2 = next(i for i in range(1, len(game.board)) if game.board[i].rank != rank1)

    result = game.flip_two(me, pos1, pos2)

    assert not result.matched
    assert not result.went_again
    assert game.current_player_name == other
    assert pos1 not in game.matched and pos2 not in game.matched
    assert game.known_positions[pos1] == result.rank1
    assert game.known_positions[pos2] == result.rank2


def test_game_ends_when_all_positions_matched():
    game = make_game(num_pairs=1)  # trivial 2-card board
    me = game.current_player_name
    result = game.flip_two(me, 0, 1)
    assert result.matched
    assert game.game_over
    assert not game.stalemate


def test_game_ends_stalemate_at_turn_cap():
    game = make_game()
    game.turn_count = MAX_TURNS
    game._check_game_over()
    assert game.game_over
    assert game.stalemate


def test_no_position_lost_or_duplicated_across_a_full_random_ai_vs_ai_game():
    game = MemoryGame(
        ["Fox1", "Fox2"],
        num_pairs=10,
        ai_difficulties={"Fox1": Difficulty.HARD, "Fox2": Difficulty.EASY},
        seed=17,
    )
    turns = 0
    while not game.game_over and turns < MAX_TURNS + 5:
        game.take_ai_turn()
        turns += 1
    assert game.game_over
    assert not game.stalemate
    assert len(game.matched) == len(game.board)
    total_pairs_found = sum(len(p.books) for p in game.players.values())
    assert total_pairs_found == 10


@pytest.mark.parametrize("num_players", [1, 3, 4])
def test_full_random_game_with_various_player_counts(num_players):
    names = ["Fox1", "Fox2", "Fox3", "Fox4"][:num_players]
    difficulties = [Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD, Difficulty.EASY]
    game = MemoryGame(
        names,
        num_pairs=6,
        ai_difficulties={n: d for n, d in zip(names, difficulties)},
        seed=88,
    )
    turns = 0
    while not game.game_over and turns < MAX_TURNS + 5:
        game.take_ai_turn()
        turns += 1
    assert game.game_over
    assert len(game.matched) == len(game.board)
