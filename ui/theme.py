"""Shared kid-friendly palette, fonts, and sizing constants (spec §6).

Bright, high-contrast, simple colors; generous touch targets (no
fine-motor-dependent tiny buttons); text kept short since some 5-year-olds
aren't fluent readers yet.
"""
from __future__ import annotations

from dataclasses import dataclass

import pygame

WINDOW_SIZE = (1024, 720)

# -- Palette ----------------------------------------------------------------
BACKGROUND = (255, 248, 231)  # warm cream
PANEL = (255, 255, 255)
PRIMARY = (255, 107, 107)  # coral red
PRIMARY_DARK = (222, 74, 74)
SECONDARY = (69, 191, 181)  # teal
ACCENT = (255, 195, 74)  # sunny yellow
SUCCESS = (123, 199, 88)  # grass green
TEXT_DARK = (45, 45, 65)
TEXT_LIGHT = (255, 255, 255)
TEXT_MUTED = (120, 120, 138)

CARD_BACK = (91, 134, 229)
CARD_BACK_PATTERN = (255, 255, 255)
CARD_FACE = (255, 255, 255)
CARD_BORDER = (45, 45, 65)
CARD_RED = (219, 58, 58)
CARD_BLACK = (52, 52, 66)

GAME_COLORS = {
    "go_fish": (91, 155, 213),
    "old_maid": (176, 120, 219),
    "memory": (123, 199, 88),
    "letter_match": (255, 165, 90),
}

MIN_TOUCH_TARGET = 88  # px


def _tint(color: tuple[int, int, int], amount: float = 0.82) -> tuple[int, int, int]:
    """A pale, pastel version of `color` -- used for card fronts so 'no
    plain white front' still reads as calm and legible, not a saturated
    background fighting the label/symbol printed on top of it.
    """
    return tuple(int(c + (255 - c) * amount) for c in color)


@dataclass(frozen=True)
class CardTheme:
    """A game's complete card visual identity: the label lettered across
    its back, the back's base color and small repeating pattern, and a
    matching (non-white) tint for its fronts. Passed into
    ui.widgets.draw_card_back/draw_card_face so card rendering is
    data-driven per game rather than hardcoded (spec §4).
    """

    label: str
    back_color: tuple[int, int, int]
    pattern: str  # one of PATTERN_DRAWERS' keys in ui.widgets
    front_tint: tuple[int, int, int]
    asset_key: str  # ui.asset_loader.load_card_back's key; see assets/design.md


CARD_THEMES: dict[str, CardTheme] = {
    "go_fish": CardTheme(
        label="GO FISH!",
        back_color=GAME_COLORS["go_fish"],
        pattern="fish",
        front_tint=_tint(GAME_COLORS["go_fish"]),
        asset_key="go_fish",
    ),
    "old_maid": CardTheme(
        label="OLD MAID",
        back_color=GAME_COLORS["old_maid"],
        pattern="crown",
        front_tint=_tint(GAME_COLORS["old_maid"]),
        asset_key="old_maid",
    ),
    "memory": CardTheme(
        label="MEMORY",
        back_color=GAME_COLORS["memory"],
        pattern="puzzle",
        front_tint=_tint(GAME_COLORS["memory"]),
        asset_key="memory",
    ),
}

_FONT_CACHE: dict[tuple[int, bool], "pygame.font.Font"] = {}


def get_font(size: int, bold: bool = False) -> "pygame.font.Font":
    pygame.font.init()
    key = (size, bold)
    if key not in _FONT_CACHE:
        font = pygame.font.SysFont("arial,dejavusans,sans", size, bold=bold)
        _FONT_CACHE[key] = font
    return _FONT_CACHE[key]
