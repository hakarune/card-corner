"""Confirms main.py's screen-navigation wiring: each launcher tile leads to
the right screen type, difficulty selection leads to the right game with
the chosen difficulty, and 'back' returns to a fresh launcher.
"""
from __future__ import annotations

import pygame
import pytest

from core.ai.base import Difficulty
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

    hard_btn = diff_screen.buttons[2]  # EASY, MEDIUM, HARD, Back
    click(diff_screen, hard_btn.rect.center)
    game_screen = diff_screen.next_screen()
    assert isinstance(game_screen, screen_cls)
    assert game_screen.difficulty is Difficulty.HARD


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
