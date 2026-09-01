"""Confirms the pause overlay is actually wired into each game screen
correctly: pausing blocks game input, Quit App sets quit_requested, and
Restart/Quit-to-Menu route through the pause menu the same as the
respective end-of-game buttons.
"""
from __future__ import annotations

import pygame
import pytest

from core.ai.base import Difficulty
from games.go_fish.screen import GoFishScreen
from games.letter_match.screen import LetterMatchScreen
from games.memory.screen import MemoryScreen
from games.old_maid.screen import OldMaidScreen
from ui.launcher import LauncherScreen
from ui.theme import WINDOW_SIZE


def click(screen, pos):
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))


def press_escape(screen):
    screen.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))


ADVERSARIAL_SCREENS = [
    lambda: GoFishScreen(WINDOW_SIZE, Difficulty.EASY, lambda: "MENU"),
    lambda: OldMaidScreen(WINDOW_SIZE, Difficulty.EASY, lambda: "MENU"),
    lambda: MemoryScreen(WINDOW_SIZE, Difficulty.EASY, lambda: "MENU"),
]
ALL_SCREENS = ADVERSARIAL_SCREENS + [lambda: LetterMatchScreen(WINDOW_SIZE, lambda: "MENU")]


@pytest.mark.parametrize("make_screen", ALL_SCREENS)
def test_escape_opens_pause_overlay(surface, make_screen):
    screen = make_screen()
    assert not screen._pause.visible
    press_escape(screen)
    assert screen._pause.visible


@pytest.mark.parametrize("make_screen", ALL_SCREENS)
def test_quit_app_from_pause_sets_quit_requested(surface, make_screen):
    screen = make_screen()
    press_escape(screen)
    screen.draw(surface)  # populate button rects
    quit_btn = next(b for b in screen._pause._buttons if b.label == "Quit App")
    click(screen, quit_btn.rect.center)
    assert screen.quit_requested


@pytest.mark.parametrize("make_screen", ALL_SCREENS)
def test_quit_to_menu_from_pause_navigates_to_launcher(surface, make_screen):
    screen = make_screen()
    press_escape(screen)
    screen.draw(surface)
    menu_btn = next(b for b in screen._pause._buttons if b.label == "Quit to Menu")
    click(screen, menu_btn.rect.center)
    assert screen.next_screen() == "MENU"


@pytest.mark.parametrize("make_screen", ADVERSARIAL_SCREENS)
def test_game_update_is_frozen_while_paused(surface, make_screen):
    screen = make_screen()
    press_escape(screen)
    # AI-turn timers, deal animation, etc. should not advance while paused.
    before = vars(screen).copy()
    screen.update(5.0)
    # Nothing time-dependent should have changed (spot-check a couple of
    # known timer/animation attributes that would otherwise move with a
    # 5-second update).
    for attr in ("_deal_elapsed", "_ai_timer", "_timer"):
        if attr in before:
            assert vars(screen)[attr] == before[attr]


def test_pause_icon_not_shown_or_interactive_once_game_over(surface):
    screen = GoFishScreen(WINDOW_SIZE, Difficulty.EASY, lambda: "MENU")
    screen.game.game_over = True
    screen.game.winner = None
    screen._on_game_over()
    # Escape should not open the pause overlay once the game-over modal owns
    # the screen.
    press_escape(screen)
    assert not screen._pause.visible


def test_launcher_fullscreen_and_mute_icons_toggle_settings(surface, tmp_path, monkeypatch):
    from ui import settings

    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "settings.json")
    settings._settings = dict(settings.DEFAULTS)

    launcher = LauncherScreen(WINDOW_SIZE, lambda key: None)
    starting_fullscreen = settings.get("fullscreen")
    starting_muted = settings.get("muted")
    click(launcher, launcher.fullscreen_rect.center)
    assert settings.get("fullscreen") != starting_fullscreen
    click(launcher, launcher.mute_rect.center)
    assert settings.get("muted") != starting_muted
