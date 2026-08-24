"""Tests for spec §4: each game gets a unique, thematic card back (pattern
+ game name) and no plain white/blank card fronts anywhere.
"""
from __future__ import annotations

import pygame

from ui import theme
from ui.widgets import draw_card_back, draw_card_face, draw_letter_tile, draw_old_maid_illustration


def test_every_adversarial_game_has_a_card_theme():
    for key in ("go_fish", "old_maid", "memory"):
        assert key in theme.CARD_THEMES


def test_each_card_theme_has_a_distinct_label_and_color():
    themes = theme.CARD_THEMES
    labels = {t.label for t in themes.values()}
    colors = {t.back_color for t in themes.values()}
    assert len(labels) == len(themes)  # no two games share a back label
    assert len(colors) == len(themes)  # no two games share a back color


def test_card_backs_are_visually_distinct_between_games(surface):
    rect = pygame.Rect(0, 0, 120, 170)
    rendered = {}
    for key, card_theme in theme.CARD_THEMES.items():
        surf = pygame.Surface(rect.size)
        draw_card_back(surf, pygame.Rect(0, 0, 120, 170), card_theme)
        rendered[key] = pygame.image.tostring(surf, "RGB")
    values = list(rendered.values())
    assert len(set(values)) == len(values)


def test_card_back_without_theme_falls_back_to_generic_pattern(surface):
    # Sampled well inside the rounded-rect fill (border_radius=12, 3px
    # border stroke) -- a pixel too close to the corner falls outside the
    # rounded shape entirely and reads as the surface's unpainted default.
    rect = pygame.Rect(0, 0, 90, 130)
    surf = pygame.Surface(rect.size)
    draw_card_back(surf, rect)  # no theme argument -- must not raise
    assert surf.get_at((20, 20))[:3] == theme.CARD_BACK


def test_card_front_with_theme_is_not_plain_white(surface):
    rect = pygame.Rect(0, 0, 90, 130)
    surf = pygame.Surface(rect.size)
    card_theme = theme.CARD_THEMES["go_fish"]
    draw_card_face(surf, rect, "A", "♠", False, card_theme)
    # Bottom-left corner area: clear of both the rounded-corner clip and
    # the top-left rank label / centered suit symbol.
    fill_pixel = surf.get_at((20, 110))[:3]
    assert fill_pixel != (255, 255, 255)
    assert fill_pixel == card_theme.front_tint


def test_card_front_without_theme_still_falls_back_to_white_for_untouched_callers(surface):
    rect = pygame.Rect(0, 0, 90, 130)
    surf = pygame.Surface(rect.size)
    draw_card_face(surf, rect, "A", "♠", False)  # no theme -- back-compat path
    assert surf.get_at((20, 110))[:3] == theme.CARD_FACE


def test_letter_tile_background_is_not_plain_white(surface):
    rect = pygame.Rect(0, 0, 100, 100)
    surf = pygame.Surface(rect.size)
    draw_letter_tile(surf, rect, "A", theme.GAME_COLORS["letter_match"])
    fill_pixel = surf.get_at((25, 25))[:3]
    assert fill_pixel != (255, 255, 255)


def test_narrow_card_back_skips_pattern_but_keeps_label_and_color(surface):
    # A compact opponent-hand back (< 85px) drops the corner pattern (it
    # would collide with the label at that size) but must still carry the
    # theme color and not crash.
    rect = pygame.Rect(0, 0, 70, 100)
    surf = pygame.Surface(rect.size)
    card_theme = theme.CARD_THEMES["old_maid"]
    draw_card_back(surf, rect, card_theme)
    assert surf.get_at((20, 20))[:3] == card_theme.back_color


def test_old_maid_illustration_is_distinct_from_a_normal_card_face(surface):
    rect = pygame.Rect(0, 0, 90, 130)
    illustration = pygame.Surface(rect.size)
    draw_old_maid_illustration(illustration, rect)

    normal = pygame.Surface(rect.size)
    draw_card_face(normal, rect, "Q", "♣", False, theme.CARD_THEMES["old_maid"])

    assert pygame.image.tostring(illustration, "RGB") != pygame.image.tostring(normal, "RGB")


def test_old_maid_illustration_does_not_raise_at_small_sizes(surface):
    for size in [(40, 60), (70, 100), (90, 130), (125, 125)]:
        surf = pygame.Surface(size)
        draw_old_maid_illustration(surf, pygame.Rect(0, 0, *size))  # must not raise
