"""Tests for ui.pause.PauseMenu, the shared pause overlay used by all four
game screens.
"""
from __future__ import annotations

import pygame
import pytest

from ui import settings
from ui.pause import PauseMenu

SIZE = (1024, 720)


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "settings.json")
    settings._settings = dict(settings.DEFAULTS)
    yield


def make_menu(**overrides):
    calls = {"restart": 0, "quit_to_menu": 0, "quit_app": 0}

    def restart():
        calls["restart"] += 1

    def quit_to_menu():
        calls["quit_to_menu"] += 1

    def quit_app():
        calls["quit_app"] += 1

    menu = PauseMenu(
        SIZE,
        on_restart=overrides.get("on_restart", restart),
        on_quit_to_menu=overrides.get("on_quit_to_menu", quit_to_menu),
        on_quit_app=overrides.get("on_quit_app", quit_app),
    )
    return menu, calls


def click(menu, pos):
    menu.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))


def press_escape(menu):
    menu.handle_event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))


def test_starts_closed():
    menu, _ = make_menu()
    assert not menu.visible


def test_escape_opens_and_closes():
    menu, _ = make_menu()
    press_escape(menu)
    assert menu.visible
    press_escape(menu)
    assert not menu.visible


def test_pause_icon_click_opens_when_closed():
    menu, _ = make_menu()
    click(menu, menu.pause_icon_rect.center)
    assert menu.visible


def test_pause_icon_click_does_nothing_extra_while_already_open():
    menu, _ = make_menu()
    menu.open()
    consumed = menu.handle_event(
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=menu.pause_icon_rect.center)
    )
    # Still open (clicking the icon area while paused just hits whatever
    # panel/buttons are there -- it doesn't toggle via the icon rect check).
    assert menu.visible
    assert consumed  # event is still swallowed since the overlay is open


def test_events_are_swallowed_while_open():
    menu, _ = make_menu()
    menu.open()
    consumed = menu.handle_event(
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(5, 5))
    )
    assert consumed


def test_events_pass_through_while_closed_and_not_on_icon():
    menu, _ = make_menu()
    consumed = menu.handle_event(
        pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(5, 5))
    )
    assert not consumed


def test_resume_button_closes_without_calling_any_callback():
    menu, calls = make_menu()
    menu.open()
    resume_btn = next(b for b in menu._buttons if b.label == "Resume")
    click(menu, resume_btn.rect.center)
    assert not menu.visible
    assert calls == {"restart": 0, "quit_to_menu": 0, "quit_app": 0}


def test_restart_button_calls_callback_and_closes():
    menu, calls = make_menu()
    menu.open()
    btn = next(b for b in menu._buttons if b.label == "Restart Game")
    click(menu, btn.rect.center)
    assert calls["restart"] == 1
    assert not menu.visible


def test_quit_to_menu_button_calls_callback_and_closes():
    menu, calls = make_menu()
    menu.open()
    btn = next(b for b in menu._buttons if b.label == "Quit to Menu")
    click(menu, btn.rect.center)
    assert calls["quit_to_menu"] == 1
    assert not menu.visible


def test_quit_app_button_calls_callback_and_closes():
    menu, calls = make_menu()
    menu.open()
    btn = next(b for b in menu._buttons if b.label == "Quit App")
    click(menu, btn.rect.center)
    assert calls["quit_app"] == 1
    assert not menu.visible


def test_fullscreen_toggle_button_flips_setting_and_stays_open():
    settings.set("fullscreen", True)
    menu, _ = make_menu()
    menu.open()
    btn = next(b for b in menu._buttons if b.label.startswith("Fullscreen"))
    assert btn.label == "Fullscreen: On"
    click(menu, btn.rect.center)
    assert settings.get("fullscreen") is False
    assert menu.visible  # keep_open=True for this one
    refreshed = next(b for b in menu._buttons if b.label.startswith("Fullscreen"))
    assert refreshed.label == "Fullscreen: Off"
