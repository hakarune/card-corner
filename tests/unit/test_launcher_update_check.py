"""Tests for the 'Check for Updates' UI on the main menu. Network access is
mocked via ui.update_check's urlopen (never a real HTTP call), and
webbrowser.open is mocked so a test run never tries to actually spawn a
browser.
"""
from __future__ import annotations

import json
import time

import pygame
import pytest

from ui import launcher as launcher_module
from ui import update_check
from ui.launcher import LauncherScreen
from ui.theme import WINDOW_SIZE


class FakeResponse:
    def __init__(self, payload: dict):
        self._body = json.dumps(payload).encode("utf-8")

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def click(screen, pos):
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))


def wait_for_check(screen, timeout=2.0):
    deadline = time.monotonic() + timeout
    while screen._update_checker.checking and time.monotonic() < deadline:
        time.sleep(0.01)


def test_initial_state_shows_no_result_yet(surface):
    screen = LauncherScreen(WINDOW_SIZE, lambda key: None)
    assert screen._update_checker.result is None
    screen.draw(surface)  # must not crash with no result yet


def test_clicking_triggers_a_check(monkeypatch, surface):
    monkeypatch.setattr(
        update_check.urllib.request,
        "urlopen",
        lambda req, timeout=None: FakeResponse({"tag_name": "v0.0.1"}),
    )
    screen = LauncherScreen(WINDOW_SIZE, lambda key: None)
    click(screen, screen.update_check_rect.center)
    wait_for_check(screen)
    assert screen._update_checker.result is not None
    assert screen._update_checker.result.ok


def test_up_to_date_result_renders_without_crashing(monkeypatch, surface):
    from version import __version__

    monkeypatch.setattr(
        update_check.urllib.request,
        "urlopen",
        lambda req, timeout=None: FakeResponse({"tag_name": f"v{__version__}"}),
    )
    screen = LauncherScreen(WINDOW_SIZE, lambda key: None)
    click(screen, screen.update_check_rect.center)
    wait_for_check(screen)
    screen.draw(surface)
    assert not screen._update_checker.result.update_available


def test_update_available_click_opens_release_page(monkeypatch, surface):
    monkeypatch.setattr(
        update_check.urllib.request,
        "urlopen",
        lambda req, timeout=None: FakeResponse(
            {"tag_name": "v99.0.0", "html_url": "https://example.invalid/release"}
        ),
    )
    opened = []
    monkeypatch.setattr(launcher_module.webbrowser, "open", lambda url: opened.append(url))

    screen = LauncherScreen(WINDOW_SIZE, lambda key: None)
    click(screen, screen.update_check_rect.center)
    wait_for_check(screen)
    screen.draw(surface)

    # Second click, now that a result showing an available update is ready,
    # should open the release page rather than re-triggering a check.
    click(screen, screen.update_check_rect.center)
    assert opened == ["https://example.invalid/release"]


def test_offline_failure_does_not_crash_and_shows_a_message(monkeypatch, surface):
    def raise_it(req, timeout=None):
        raise OSError("network unreachable")

    monkeypatch.setattr(update_check.urllib.request, "urlopen", raise_it)
    screen = LauncherScreen(WINDOW_SIZE, lambda key: None)
    click(screen, screen.update_check_rect.center)
    wait_for_check(screen)
    screen.draw(surface)  # must not crash
    assert not screen._update_checker.result.ok


def test_clicking_while_already_checking_does_not_spawn_a_second_check(monkeypatch, surface):
    calls = []

    def slow_urlopen(req, timeout=None):
        calls.append(1)
        time.sleep(0.3)
        return FakeResponse({"tag_name": "v0.0.1"})

    monkeypatch.setattr(update_check.urllib.request, "urlopen", slow_urlopen)
    screen = LauncherScreen(WINDOW_SIZE, lambda key: None)
    click(screen, screen.update_check_rect.center)
    click(screen, screen.update_check_rect.center)  # while first check in flight
    screen.draw(surface)  # "Checking..." state must render fine
    wait_for_check(screen)
    assert len(calls) == 1
