"""Tests for main.py's logical-resolution scaling helpers (compute_scale,
transform_event) -- the mechanism that lets every screen's fixed-size
layout code support fullscreen/resizable windows unmodified.
"""
from __future__ import annotations

import pygame
import pytest

import main as main_module
from main import LOGICAL_SIZE, compute_scale, create_window, transform_event


def test_compute_scale_exact_match_no_letterbox():
    scale, offset, render_size = compute_scale(LOGICAL_SIZE, LOGICAL_SIZE)
    assert scale == pytest.approx(1.0)
    assert offset == (0, 0)
    assert render_size == LOGICAL_SIZE


def test_compute_scale_wider_window_letterboxes_left_right():
    # Window is much wider than logical aspect ratio -> vertical fill,
    # black bars on left/right.
    window_size = (2048, 720)
    scale, offset, render_size = compute_scale(window_size, LOGICAL_SIZE)
    assert scale == pytest.approx(720 / LOGICAL_SIZE[1])
    assert render_size[1] == 720
    assert offset[0] > 0
    assert offset[1] == 0


def test_compute_scale_taller_window_letterboxes_top_bottom():
    window_size = (1024, 2000)
    scale, offset, render_size = compute_scale(window_size, LOGICAL_SIZE)
    assert scale == pytest.approx(1024 / LOGICAL_SIZE[0])
    assert render_size[0] == 1024
    assert offset[1] > 0
    assert offset[0] == 0


def test_compute_scale_smaller_window_scales_down():
    window_size = (512, 360)
    scale, offset, render_size = compute_scale(window_size, LOGICAL_SIZE)
    assert 0 < scale < 1
    assert render_size[0] <= 512 and render_size[1] <= 360


def test_compute_scale_never_divides_by_zero_on_degenerate_window():
    scale, offset, render_size = compute_scale((0, 0), LOGICAL_SIZE)
    assert scale > 0
    assert render_size[0] >= 0 and render_size[1] >= 0


def test_transform_event_maps_window_pos_to_logical_pos():
    # pygame is already initialized by the session-scoped conftest fixture;
    # deliberately not calling pygame.init()/quit() here -- doing so would
    # tear down that shared session and break get_surface() for tests that
    # run afterward (this exact bug was hit and fixed once already).
    scale, offset, _ = compute_scale((2048, 1440), LOGICAL_SIZE)  # scale=2.0, centered
    window_pos = (offset[0] + 100, offset[1] + 200)
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=window_pos)
    transformed = transform_event(event, scale, offset)
    assert transformed.pos == pytest.approx((50, 100))


def test_transform_event_leaves_non_positional_events_untouched():
    event = pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE)
    transformed = transform_event(event, 2.0, (10, 10))
    assert transformed is event


def test_transform_event_roundtrips_at_scale_one_no_offset():
    event = pygame.event.Event(pygame.MOUSEMOTION, pos=(321, 456))
    transformed = transform_event(event, 1.0, (0, 0))
    assert transformed.pos == pytest.approx((321, 456))


def test_create_window_fullscreen_requests_fullscreen_flag(monkeypatch):
    calls = []

    def fake_set_mode(size, flags=0):
        calls.append((size, flags))
        return pygame.Surface((1, 1))

    monkeypatch.setattr(main_module.pygame.display, "set_mode", fake_set_mode)
    create_window(True, (1024, 720))
    assert calls == [((0, 0), pygame.FULLSCREEN)]


def test_create_window_windowed_requests_resizable_flag_and_given_size(monkeypatch):
    calls = []

    def fake_set_mode(size, flags=0):
        calls.append((size, flags))
        return pygame.Surface((1, 1))

    monkeypatch.setattr(main_module.pygame.display, "set_mode", fake_set_mode)
    create_window(False, (800, 600))
    assert calls == [((800, 600), pygame.RESIZABLE)]


def test_main_loop_switches_window_when_fullscreen_setting_changes(monkeypatch, tmp_path):
    """Drives main()'s real loop body (not a reimplementation) through a
    scripted event sequence: one idle frame, a mid-loop fullscreen setting
    flip (as the pause menu's fullscreen button would cause), then quit.
    Confirms the settings-polling branch actually calls create_window with
    the new mode, and that main() returns cleanly afterward.
    """
    from ui import settings

    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "settings.json")
    settings._settings = dict(settings.DEFAULTS)
    settings._settings["fullscreen"] = True
    settings._settings["windowed_size"] = [800, 600]

    # main() legitimately calls pygame.quit() on its way out; the real call
    # would tear down the session-scoped display every other test in this
    # file (and beyond) relies on. No-op it here and let the shared conftest
    # fixture own the real init/quit lifecycle for the whole test session.
    monkeypatch.setattr(main_module.pygame, "quit", lambda: None)

    create_window_calls = []
    real_create_window = main_module.create_window

    def spy_create_window(fullscreen, windowed_size):
        create_window_calls.append((fullscreen, tuple(windowed_size)))
        return real_create_window(fullscreen, windowed_size)

    monkeypatch.setattr(main_module, "create_window", spy_create_window)

    # A do-nothing screen so the loop doesn't depend on real game logic;
    # flips the fullscreen setting on its second update(), then requests quit.
    class ScriptedScreen:
        def __init__(self, size):
            self.size = size
            self.quit_requested = False
            self._next = None
            self._updates = 0

        def handle_event(self, event):
            pass

        def update(self, dt):
            self._updates += 1
            if self._updates == 2:
                settings.set("fullscreen", False)
            elif self._updates >= 4:
                self.quit_requested = True

        def draw(self, surface):
            surface.fill((0, 0, 0))

        def next_screen(self):
            return None

    monkeypatch.setattr(main_module, "make_launcher", lambda size: ScriptedScreen(size))
    monkeypatch.setattr(main_module.pygame.event, "get", lambda: [])
    monkeypatch.setattr(main_module.pygame.time, "Clock", lambda: type("C", (), {"tick": lambda self, fps: 16})())

    with pytest.raises(SystemExit) as exc_info:
        main_module.main()
    assert exc_info.value.code == 0

    # First call is the initial window creation (fullscreen=True); the
    # second is the mid-loop switch to windowed after the setting flipped.
    assert create_window_calls[0][0] is True
    assert any(call[0] is False for call in create_window_calls[1:])
