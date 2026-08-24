"""Main menu: pick one of the four games. Icons + color coding lead, with a
short label underneath — not reading-dependent for a 5-year-old to navigate
(spec §6).
"""
from __future__ import annotations

from typing import Callable

import pygame

import webbrowser

from core.ai.base import Difficulty, DIFFICULTY_LABELS
from . import settings, theme
from .screen import Screen
from .update_check import UpdateChecker
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

        # Top-right settings icons: visible, always-available toggles for
        # fullscreen and mute -- no keyboard shortcut a 5-year-old wouldn't
        # know about.
        icon_size = theme.MIN_TOUCH_TARGET
        self.fullscreen_rect = pygame.Rect(size[0] - icon_size - 24, 24, icon_size, icon_size)
        self.mute_rect = pygame.Rect(size[0] - 2 * icon_size - 40, 24, icon_size, icon_size)

        # A quiet, manual, parent-facing action -- not automatic, not
        # nagging. Small text link tucked in a corner rather than a
        # prominent button.
        self._update_checker = UpdateChecker()
        self.update_check_rect = pygame.Rect(size[0] - 220, size[1] - 44, 200, 34)

    def _check_for_updates(self) -> None:
        self._update_checker.start()

    def _open_release_page(self) -> None:
        result = self._update_checker.result
        if result is not None and result.ok:
            webbrowser.open(result.release_url)

    def _toggle_fullscreen(self) -> None:
        settings.set("fullscreen", not settings.get("fullscreen"))

    def _toggle_mute(self) -> None:
        settings.set("muted", not settings.get("muted"))

    def handle_event(self, event: pygame.event.Event) -> None:
        for btn in self.buttons:
            btn.handle_event(event)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.fullscreen_rect.collidepoint(event.pos):
                self._toggle_fullscreen()
            elif self.mute_rect.collidepoint(event.pos):
                self._toggle_mute()
            elif self.update_check_rect.collidepoint(event.pos):
                result = self._update_checker.result
                if result is not None and result.ok and result.update_available:
                    self._open_release_page()
                elif not self._update_checker.checking:
                    self._check_for_updates()

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(theme.BACKGROUND)
        self._draw_icon_buttons(surface)
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
        self._draw_update_check(surface)

    def _draw_update_check(self, surface: pygame.Surface) -> None:
        result = self._update_checker.result
        if self._update_checker.checking:
            label, color = "Checking for updates...", theme.TEXT_MUTED
        elif result is None:
            label, color = "Check for Updates", theme.TEXT_MUTED
        elif not result.ok:
            label, color = "Couldn't check for updates", theme.TEXT_MUTED
        elif result.update_available:
            label, color = f"Update available ({result.latest_version}) →", theme.SECONDARY
        else:
            label, color = "You're up to date!", theme.SUCCESS
        draw_text(surface, label, self.update_check_rect.center, size=18, color=color, center=True)

    def _draw_icon_buttons(self, surface: pygame.Surface) -> None:
        for rect in (self.fullscreen_rect, self.mute_rect):
            pygame.draw.rect(surface, theme.PANEL, rect, border_radius=10)
            pygame.draw.rect(surface, theme.TEXT_DARK, rect, width=2, border_radius=10)

        # Fullscreen glyph: four corner brackets, or an inward-pointing
        # variant when already fullscreen (windowed target).
        r = self.fullscreen_rect
        pad, arm = 10, 8
        corners = [(r.left + pad, r.top + pad, 1, 1), (r.right - pad, r.top + pad, -1, 1),
                   (r.left + pad, r.bottom - pad, 1, -1), (r.right - pad, r.bottom - pad, -1, -1)]
        for x, y, dx, dy in corners:
            pygame.draw.line(surface, theme.TEXT_DARK, (x, y), (x + arm * dx, y), 3)
            pygame.draw.line(surface, theme.TEXT_DARK, (x, y), (x, y + arm * dy), 3)

        # Mute glyph: a speaker shape, with an X overlaid when muted.
        r = self.mute_rect
        cx, cy = r.center
        body = [(cx - 14, cy - 6), (cx - 6, cy - 6), (cx + 4, cy - 14), (cx + 4, cy + 14), (cx - 6, cy + 6), (cx - 14, cy + 6)]
        pygame.draw.polygon(surface, theme.TEXT_DARK, body)
        if settings.get("muted"):
            pygame.draw.line(surface, (196, 90, 90), (cx + 8, cy - 10), (cx + 18, cy + 10), 3)
            pygame.draw.line(surface, (196, 90, 90), (cx + 18, cy - 10), (cx + 8, cy + 10), 3)
        else:
            pygame.draw.arc(surface, theme.TEXT_DARK, (cx + 6, cy - 10, 16, 20), -0.9, 0.9, 2)


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

        back_rect = (40, size[1] - 100, 200, theme.MIN_TOUCH_TARGET)
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
