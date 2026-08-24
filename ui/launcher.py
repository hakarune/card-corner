"""Main menu: pick one of the four games. Icons + color coding lead, with a
short label underneath — not reading-dependent for a 5-year-old to navigate
(spec §6).
"""
from __future__ import annotations

from typing import Callable

import pygame

from core.ai.base import Difficulty, DIFFICULTY_LABELS
from . import theme
from .screen import Screen
from .widgets import Button, draw_text


def _draw_go_fish_icon(surface: pygame.Surface, rect: pygame.Rect) -> None:
    cx, cy = rect.center
    w, h = rect.width * 0.5, rect.height * 0.3
    body = pygame.Rect(0, 0, w, h)
    body.center = (cx - rect.width * 0.05, cy)
    pygame.draw.ellipse(surface, theme.TEXT_LIGHT, body)
    tail = [
        (body.left + 6, body.centery),
        (body.left - w * 0.35, body.centery - h * 0.5),
        (body.left - w * 0.35, body.centery + h * 0.5),
    ]
    pygame.draw.polygon(surface, theme.TEXT_LIGHT, tail)
    pygame.draw.circle(surface, theme.GAME_COLORS["go_fish"], (int(body.right - 14), int(body.centery - 4)), 5)


def _draw_old_maid_icon(surface: pygame.Surface, rect: pygame.Rect) -> None:
    cx, cy = rect.center
    w, h = rect.width * 0.5, rect.height * 0.3
    base = pygame.Rect(0, 0, w, h * 0.5)
    base.center = (cx, cy + h * 0.3)
    points = [
        (base.left, base.top),
        (base.left, base.top - h * 0.5),
        (base.left + w * 0.25, base.top - h * 0.15),
        (base.centerx, base.top - h * 0.9),
        (base.right - w * 0.25, base.top - h * 0.15),
        (base.right, base.top - h * 0.5),
        (base.right, base.top),
    ]
    pygame.draw.polygon(surface, theme.TEXT_LIGHT, points)


def _draw_memory_icon(surface: pygame.Surface, rect: pygame.Rect) -> None:
    cx, cy = rect.center
    w, h = rect.width * 0.24, rect.height * 0.34
    left = pygame.Rect(0, 0, w, h)
    left.center = (cx - w * 0.45, cy)
    right = pygame.Rect(0, 0, w, h)
    right.center = (cx + w * 0.45, cy)
    pygame.draw.rect(surface, theme.GAME_COLORS["memory"], left, border_radius=6)
    pygame.draw.rect(surface, theme.TEXT_LIGHT, left, width=3, border_radius=6)
    pygame.draw.rect(surface, theme.TEXT_LIGHT, right, border_radius=6)
    pygame.draw.rect(surface, theme.GAME_COLORS["memory"], right, width=3, border_radius=6)


def _draw_letter_match_icon(surface: pygame.Surface, rect: pygame.Rect) -> None:
    draw_text(surface, "Aa", rect.center, size=int(rect.height * 0.4), color=theme.TEXT_LIGHT, bold=True, center=True)


GAME_TILES = [
    ("go_fish", "Go Fish", _draw_go_fish_icon),
    ("old_maid", "Old Maid", _draw_old_maid_icon),
    ("memory", "Memory", _draw_memory_icon),
    ("letter_match", "Letter Match", _draw_letter_match_icon),
]


class LauncherScreen(Screen):
    def __init__(self, size: tuple[int, int], on_select: Callable[[str], "Screen"]):
        super().__init__(size)
        self.on_select = on_select
        self.buttons: list[tuple[Button, str, Callable]] = []

        tile_w, tile_h = 420, 220
        gap = 40
        cols = 2
        grid_w = cols * tile_w + gap
        start_x = (size[0] - grid_w) // 2
        start_y = 190

        self._icons = []
        for i, (key, label, icon_fn) in enumerate(GAME_TILES):
            col, row = i % cols, i // cols
            x = start_x + col * (tile_w + gap)
            y = start_y + row * (tile_h + gap)
            rect = (x, y, tile_w, tile_h)
            color = theme.GAME_COLORS[key]

            def make_click(k=key):
                return lambda: self.go_to(self.on_select(k))

            btn = Button(rect, "", make_click(), color=color, font_size=1)
            self.buttons.append(btn)
            self._icons.append((btn, label, icon_fn))

    def handle_event(self, event: pygame.event.Event) -> None:
        for btn in self.buttons:
            btn.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(theme.BACKGROUND)
        draw_text(
            surface, "Card Corner", (self.size[0] // 2, 90), size=64, bold=True, center=True
        )
        draw_text(
            surface,
            "Pick a game to play!",
            (self.size[0] // 2, 145),
            size=28,
            color=theme.TEXT_MUTED,
            center=True,
        )
        for btn, label, icon_fn in self._icons:
            btn.draw(surface)
            icon_area = btn.rect.inflate(-40, -90)
            icon_area.top = btn.rect.top + 10
            icon_fn(surface, icon_area)
            draw_text(
                surface,
                label,
                (btn.rect.centerx, btn.rect.bottom - 32),
                size=34,
                color=theme.TEXT_LIGHT,
                bold=True,
                center=True,
            )


class DifficultySelectScreen(Screen):
    """Shared difficulty picker used by Go Fish, Old Maid, and Memory."""

    def __init__(
        self,
        size: tuple[int, int],
        game_label: str,
        game_color,
        on_pick: Callable[[Difficulty], "Screen"],
        on_back: Callable[[], "Screen"],
    ):
        super().__init__(size)
        self.game_label = game_label
        self.buttons: list[Button] = []

        cx = size[0] // 2
        btn_w, btn_h, gap = 420, 100, 30
        start_y = 260
        for i, difficulty in enumerate([Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD]):
            rect = (cx - btn_w // 2, start_y + i * (btn_h + gap), btn_w, btn_h)

            def make_click(d=difficulty):
                return lambda: self.go_to(on_pick(d))

            self.buttons.append(
                Button(rect, DIFFICULTY_LABELS[difficulty], make_click(), color=game_color, font_size=36)
            )

        back_rect = (40, size[1] - 100, 200, 64)
        self.buttons.append(
            Button(back_rect, "Back", lambda: self.go_to(on_back()), color=theme.TEXT_MUTED, font_size=28)
        )

    def handle_event(self, event: pygame.event.Event) -> None:
        for btn in self.buttons:
            btn.handle_event(event)

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(theme.BACKGROUND)
        draw_text(
            surface,
            f"{self.game_label}: choose a friend to play with",
            (self.size[0] // 2, 140),
            size=40,
            bold=True,
            center=True,
        )
        for btn in self.buttons:
            btn.draw(surface)
