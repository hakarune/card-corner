"""Tests for main.py's logical-resolution scaling helpers (compute_scale,
transform_event) -- the mechanism that lets every screen's fixed-size
layout code support fullscreen/resizable windows unmodified.
"""
from __future__ import annotations

import pygame
import pytest

from main import LOGICAL_SIZE, compute_scale, transform_event


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
