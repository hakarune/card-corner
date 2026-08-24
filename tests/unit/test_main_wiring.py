"""Confirms main.py's screen-navigation wiring: each launcher tile leads to
the right screen type, difficulty selection leads to the right game with
the chosen difficulty, and 'back' returns to a fresh launcher.
"""
from __future__ import annotations

import pygame
import pytest

from core.ai.base import Difficulty, DIFFICULTY_LABELS
from games.go_fish.screen import GoFishScreen
from games.letter_match.screen import LetterMatchScreen
from games.memory.screen import MemoryScreen
from games.old_maid.screen import OldMaidScreen
from main import make_launcher
from ui.launcher import DifficultySelectScreen, LauncherScreen
from ui.theme import WINDOW_SIZE


def click(screen, pos):
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)
    screen.handle_event(event)


def test_letter_match_tile_goes_straight_to_the_game_no_difficulty_picker():
    launcher = make_launcher(WINDOW_SIZE)
    assert isinstance(launcher, LauncherScreen)
    letter_btn = next(
        btn for btn, label, _ in launcher._icons if label == "Letter Match"
    )
    click(launcher, letter_btn.rect.center)
    next_screen = launcher.next_screen()
    assert isinstance(next_screen, LetterMatchScreen)


@pytest.mark.parametrize(
    "label,screen_cls",
    [("Go Fish", GoFishScreen), ("Old Maid", OldMaidScreen), ("Memory", MemoryScreen)],
)
def test_adversarial_game_tiles_go_to_difficulty_select_then_the_right_screen(label, screen_cls):
    launcher = make_launcher(WINDOW_SIZE)
    btn = next(b for b, lbl, _ in launcher._icons if lbl == label)
    click(launcher, btn.rect.center)
    diff_screen = launcher.next_screen()
    assert isinstance(diff_screen, DifficultySelectScreen)

    # Look up by label rather than a fixed index: Memory's setup screen has
    # an extra leading "Play Alone" button ahead of the three difficulties.
    hard_btn = next(b for b in diff_screen.buttons if b.label == DIFFICULTY_LABELS[Difficulty.HARD])
    click(diff_screen, hard_btn.rect.center)
    game_screen = diff_screen.next_screen()
    assert isinstance(game_screen, screen_cls)
    assert game_screen.difficulty is Difficulty.HARD


def test_memory_setup_has_a_play_alone_option_that_skips_ai():
    launcher = make_launcher(WINDOW_SIZE)
    btn = next(b for b, lbl, _ in launcher._icons if lbl == "Memory")
    click(launcher, btn.rect.center)
    diff_screen = launcher.next_screen()
    assert isinstance(diff_screen, DifficultySelectScreen)

    solo_btn = next(b for b in diff_screen.buttons if b.label == "Play Alone")
    click(diff_screen, solo_btn.rect.center)
    game_screen = diff_screen.next_screen()
    assert isinstance(game_screen, MemoryScreen)
    assert game_screen.solo is True
    assert game_screen.difficulty is None


def test_memory_setup_header_mentions_playing_alone():
    # Auditor #1 finding: the shared header always said "choose a friend to
    # play with", contradicting the "Play Alone" button shown right below
    # it for Memory.
    launcher = make_launcher(WINDOW_SIZE)
    btn = next(b for b, lbl, _ in launcher._icons if lbl == "Memory")
    click(launcher, btn.rect.center)
    diff_screen = launcher.next_screen()
    assert "alone" in diff_screen.header_text.lower()


def test_other_games_setup_headers_do_not_mention_playing_alone():
    for label in ("Go Fish", "Old Maid"):
        launcher = make_launcher(WINDOW_SIZE)
        btn = next(b for b, lbl, _ in launcher._icons if lbl == label)
        click(launcher, btn.rect.center)
        diff_screen = launcher.next_screen()
        assert "alone" not in diff_screen.header_text.lower()


def test_other_games_setup_screens_have_no_play_alone_option():
    for label in ("Go Fish", "Old Maid"):
        launcher = make_launcher(WINDOW_SIZE)
        btn = next(b for b, lbl, _ in launcher._icons if lbl == label)
        click(launcher, btn.rect.center)
        diff_screen = launcher.next_screen()
        assert all(b.label != "Play Alone" for b in diff_screen.buttons)


def test_difficulty_select_back_button_returns_to_a_fresh_launcher():
    launcher = make_launcher(WINDOW_SIZE)
    btn = next(b for b, lbl, _ in launcher._icons if lbl == "Go Fish")
    click(launcher, btn.rect.center)
    diff_screen = launcher.next_screen()

    back_btn = diff_screen.buttons[-1]
    click(diff_screen, back_btn.rect.center)
    back_to_menu = diff_screen.next_screen()
    assert isinstance(back_to_menu, LauncherScreen)


def test_game_screen_menu_button_returns_to_a_fresh_launcher():
    screen = GoFishScreen(WINDOW_SIZE, Difficulty.EASY, lambda: make_launcher(WINDOW_SIZE))
    screen.game.game_over = True
    screen.game.winner = None
    screen._on_game_over()
    surface = pygame.display.get_surface()
    screen.draw(surface)
    menu_btn = screen._end_buttons[1]
    click(screen, menu_btn.rect.center)
    next_screen = screen.next_screen()
    assert isinstance(next_screen, LauncherScreen)
