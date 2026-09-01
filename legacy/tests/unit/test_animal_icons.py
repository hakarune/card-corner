"""Letter Match's "animals" mode icons (spec §8) must actually be
distinguishable from each other at real gameplay size -- a purely visual
requirement pixel/geometry assertions can't otherwise catch. Auditor #1
found Cat/Pig nearly identical (2.62% pixel difference) and Bird unreadable
as a bird at the real 125x125 tile size; this guards against that class of
regression recurring silently.
"""
from __future__ import annotations

import pygame
import pytest

from ui import theme
from ui.items import ANIMAL_ICONS
from ui.widgets import draw_animal_tile

TILE_SIZE = 125  # matches games/letter_match/screen.py's real tile size
# Every icon shares the same base head-circle size/position (the house
# style established across ui/items.py), so raw whole-tile pixel-diff
# percentages between any two icons are naturally small and compressed --
# the full measured matrix across all 7 icons ranges ~3.1%-25%, not the
# ~30%+ you'd expect from unconstrained shapes. Cat/Pig was the original
# bug Auditor #1 found (2.62% before this fix, 3.14% after -- still the
# closest pair, but now visually distinct: round ears + a visible
# high-contrast snout vs Cat's plain pointy-eared circle). This threshold
# sits just above the old broken value and just below every current pair
# (the next-closest is Cat/Dog at 4.08%), so it catches a real regression
# back toward "two icons that are basically the same shape" without being
# so tight that unrelated rendering tweaks trip it.
MIN_DISTINCT_PIXEL_FRACTION = 0.03


def render_icon(letter: str) -> pygame.Surface:
    surf = pygame.Surface((TILE_SIZE, TILE_SIZE))
    draw_animal_tile(surf, pygame.Rect(0, 0, TILE_SIZE, TILE_SIZE), letter, theme.GAME_COLORS["letter_match"])
    return surf


def pixel_diff_fraction(a: pygame.Surface, b: pygame.Surface) -> float:
    diff = 0
    for x in range(TILE_SIZE):
        for y in range(TILE_SIZE):
            if a.get_at((x, y)) != b.get_at((x, y)):
                diff += 1
    return diff / (TILE_SIZE * TILE_SIZE)


@pytest.mark.parametrize("letter", sorted(ANIMAL_ICONS.keys()))
def test_animal_icon_renders_without_error(surface, letter):
    render_icon(letter)  # just confirm it doesn't raise for any registered letter


def test_every_pair_of_animal_icons_is_visually_distinct(surface):
    letters = sorted(ANIMAL_ICONS.keys())
    rendered = {letter: render_icon(letter) for letter in letters}
    too_similar = []
    for i, a in enumerate(letters):
        for b in letters[i + 1 :]:
            frac = pixel_diff_fraction(rendered[a], rendered[b])
            if frac < MIN_DISTINCT_PIXEL_FRACTION:
                too_similar.append((a, b, frac))
    assert not too_similar, f"icon pairs too visually similar: {too_similar}"
