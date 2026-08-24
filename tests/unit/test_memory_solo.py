"""Memory's solo "Play Alone" mode (spec §7): no AI opponent, just flipping
pairs at your own pace, with a completion time/move count shown instead of
a win/lose-vs-opponent framing.
"""
from __future__ import annotations

import pygame

from games.memory.screen import AI_NAME, HUMAN_NAME, MemoryScreen


def click(screen, pos):
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))


def make_solo_screen(surface) -> MemoryScreen:
    screen = MemoryScreen((1024, 720), None, lambda: None)
    screen.draw(surface)
    return screen


def test_solo_mode_has_a_single_player_and_no_ai_turn(surface):
    screen = make_solo_screen(surface)
    assert screen.solo is True
    assert list(screen.game.players) == [HUMAN_NAME]
    assert screen.game.is_ai_turn() is False


def test_solo_mode_never_starts_a_scheduled_ai_turn(surface):
    screen = make_solo_screen(surface)
    assert screen._locked is False
    assert screen._pending_callback is None


def test_vs_ai_mode_still_has_both_players(surface):
    from core.ai.base import Difficulty

    screen = MemoryScreen((1024, 720), Difficulty.EASY, lambda: None)
    assert screen.solo is False
    assert set(screen.game.players) == {HUMAN_NAME, AI_NAME}


def test_solo_move_count_increments_once_per_flip_pair(surface):
    screen = make_solo_screen(surface)
    assert screen._moves == 0
    first, second = 0, 1
    screen._human_click(first)
    screen._human_click(second)
    assert screen._moves == 1


def test_solo_elapsed_time_advances_while_playing(surface):
    screen = make_solo_screen(surface)
    screen.update(2.5)
    assert screen._elapsed >= 2.5


def test_solo_elapsed_time_stops_advancing_once_game_over(surface):
    screen = make_solo_screen(surface)
    screen.game.game_over = True
    screen.update(5.0)
    assert screen._elapsed == 0.0


def test_solo_stats_line_never_overlaps_the_pause_icon(surface):
    # Caught by manual screenshot QA: the stats line was originally sized
    # for the (shorter) vs-AI score line and ran into the pause icon's left
    # edge for realistic "Time MM:SS    Moves N" strings. Check the actual
    # rendered text width against the pause icon's left edge directly,
    # using the longest string this display can realistically show.
    from ui import theme

    screen = make_solo_screen(surface)
    font = theme.get_font(24, bold=True)
    worst_case = "Time 59:59    Moves 99"
    text_width, _ = font.size(worst_case)
    x = screen.size[0] - 400
    assert x + text_width < screen._pause.pause_icon_rect.left


def test_solo_game_over_message_shows_time_and_moves_not_a_score(surface):
    screen = make_solo_screen(surface)
    screen._moves = 7
    screen._elapsed = 65.0  # 1:05
    screen._on_game_over()
    assert "1:05" in screen.message
    assert "Moves: 7" in screen.message
    assert "win" not in screen.message.lower()
    assert "lose" not in screen.message.lower()
    assert AI_NAME not in screen.message
    assert len(screen._end_buttons) == 2
