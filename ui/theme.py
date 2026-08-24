"""Shared kid-friendly palette, fonts, and sizing constants (spec §6).

Bright, high-contrast, simple colors; generous touch targets (no
fine-motor-dependent tiny buttons); text kept short since some 5-year-olds
aren't fluent readers yet.
"""
from __future__ import annotations

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

_FONT_CACHE: dict[tuple[int, bool], "pygame.font.Font"] = {}


def get_font(size: int, bold: bool = False) -> "pygame.font.Font":
    pygame.font.init()
    key = (size, bold)
    if key not in _FONT_CACHE:
        font = pygame.font.SysFont("arial,dejavusans,sans", size, bold=bold)
        _FONT_CACHE[key] = font
    return _FONT_CACHE[key]
