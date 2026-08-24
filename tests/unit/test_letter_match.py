import random

import pytest

from games.letter_match.game import LetterMatchGame


def make_game(seed=7, letter_count=6):
    return LetterMatchGame(letter_count=letter_count, seed=seed)


def test_tile_display_reflects_case():
    from games.letter_match.game import Tile

    assert Tile(letter="B", is_upper=True).display == "B"
    assert Tile(letter="B", is_upper=False).display == "b"


def test_letter_count_max_boundary():
    game = make_game(letter_count=26)
    assert len(game.board) == 52
    assert len({t.letter for t in game.board}) == 26


def test_board_has_one_upper_and_one_lower_tile_per_letter():
    game = make_game(letter_count=8)
    assert len(game.board) == 16
    uppers = {t.letter for t in game.board if t.is_upper}
    lowers = {t.letter for t in game.board if not t.is_upper}
    assert uppers == lowers
    assert len(uppers) == 8


@pytest.mark.parametrize("bad", [0, 27, -1])
def test_rejects_out_of_range_letter_count(bad):
    with pytest.raises(ValueError):
        LetterMatchGame(letter_count=bad)


def test_out_of_range_click_raises():
    game = make_game()
    with pytest.raises(ValueError):
        game.click(-1)
    with pytest.raises(ValueError):
        game.click(len(game.board))


def find_matching_pair(game):
    first = game.board[0]
    partner_idx = next(
        i
        for i in range(1, len(game.board))
        if game.board[i].letter == first.letter and game.board[i].is_upper != first.is_upper
    )
    return 0, partner_idx


def find_non_matching_pair(game):
    first = game.board[0]
    other_idx = next(
        i for i in range(1, len(game.board)) if game.board[i].letter != first.letter
    )
    return 0, other_idx


def test_matching_click_pair_is_recorded_and_counted():
    game = make_game()
    a, b = find_matching_pair(game)
    game.click(a)
    result = game.click(b)
    assert result.accepted
    assert result.matched
    assert a in game.matched and b in game.matched
    assert game.correct == 1
    assert game.attempts == 1


def test_non_matching_click_pair_leaves_tiles_unmatched():
    game = make_game()
    a, b = find_non_matching_pair(game)
    game.click(a)
    result = game.click(b)
    assert result.accepted
    assert not result.matched
    assert a not in game.matched and b not in game.matched
    assert game.correct == 0
    assert game.attempts == 1


def test_reclicking_pending_tile_is_gently_ignored_not_an_error():
    game = make_game()
    game.click(0)
    result = game.click(0)
    assert not result.accepted
    assert result.reason == "same tile as pending pick"
    assert game.pending_first == 0  # first pick is still live


def test_reclicking_already_matched_tile_is_gently_ignored():
    game = make_game()
    a, b = find_matching_pair(game)
    game.click(a)
    game.click(b)
    result = game.click(a)
    assert not result.accepted
    assert result.reason == "already matched"


def test_clicking_after_game_over_is_gently_ignored():
    game = make_game(letter_count=1)  # trivial 2-tile board
    a, b = find_matching_pair(game)
    game.click(a)
    game.click(b)
    assert game.game_over
    result = game.click(a)
    assert not result.accepted
    assert result.reason == "game already complete"


def test_accuracy_reflects_correct_over_attempts():
    game = make_game()
    assert game.accuracy == 0.0
    a, b = find_non_matching_pair(game)
    game.click(a)
    game.click(b)
    assert game.accuracy == 0.0
    a2, b2 = find_matching_pair(game)
    game.click(a2)
    game.click(b2)
    assert game.attempts == 2
    assert game.correct == 1
    assert game.accuracy == 0.5


def test_full_game_completes_and_ends():
    game = make_game(letter_count=5)
    while not game.game_over:
        unflipped = game.unflipped_positions()
        # naive but always-correct-eventually strategy: brute force by
        # scanning for a real pair each round
        first = unflipped[0]
        partner = next(
            i
            for i in unflipped
            if i != first
            and game.board[i].letter == game.board[first].letter
            and game.board[i].is_upper != game.board[first].is_upper
        )
        game.click(first)
        game.click(partner)
    assert game.game_over
    assert len(game.matched) == len(game.board)
    assert game.accuracy == 1.0


def test_full_game_with_mixed_misses_and_matches_yields_fractional_accuracy():
    game = make_game(letter_count=5)
    while not game.game_over:
        unflipped = game.unflipped_positions()
        first = unflipped[0]
        miss = next(
            (i for i in unflipped if i != first and game.board[i].letter != game.board[first].letter),
            None,
        )
        if miss is not None:
            game.click(first)
            game.click(miss)  # deliberate miss before the real pair
        partner = next(
            i
            for i in game.unflipped_positions()
            if i != first
            and game.board[i].letter == game.board[first].letter
            and game.board[i].is_upper != game.board[first].is_upper
        )
        game.click(first)
        game.click(partner)
    assert game.game_over
    assert len(game.matched) == len(game.board)
    assert 0.0 < game.accuracy < 1.0


def test_input_fuzzing_never_crashes_or_gets_stuck():
    """Simulate a burst of rapid, mostly-nonsensical clicks: repeats,
    already-matched tiles, alternating pending picks, and the occasional
    deliberate out-of-range click (a real bug, expected to raise). The game
    must never crash on legitimate input, never end up in a state where
    `matched` exceeds the board, and must still be able to reach completion
    afterward with clean play.
    """
    game = make_game(letter_count=8, seed=99)
    rng = random.Random(1234)
    n = len(game.board)

    for _ in range(2000):
        pos = rng.randrange(-2, n + 2)  # occasionally out of range on purpose
        if pos < 0 or pos >= n:
            with pytest.raises(ValueError):
                game.click(pos)
            continue
        game.click(pos)  # must never raise for any in-range position
        assert len(game.matched) <= n
        assert game.correct <= game.attempts

    # Finish the game off with legitimate play to confirm the state is
    # still sane and completable after the fuzzing.
    guard = 0
    while not game.game_over and guard < 1000:
        unflipped = game.unflipped_positions()
        if len(unflipped) < 2:
            break
        first = unflipped[0]
        partner = next(
            (
                i
                for i in unflipped
                if i != first
                and game.board[i].letter == game.board[first].letter
                and game.board[i].is_upper != game.board[first].is_upper
            ),
            None,
        )
        if partner is None:
            # first's partner was already matched earlier by fuzzing luck;
            # just clear the pending pick with a harmless miss and retry.
            game.click(first)
            game.click(unflipped[1])
            guard += 1
            continue
        game.click(first)
        game.click(partner)
        guard += 1

    assert game.game_over
    assert len(game.matched) == n
