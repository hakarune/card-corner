"""A reusable pause overlay for the four game screens (spec: 'affects all
four games'). Triggered by Esc or a visible on-screen pause icon -- never a
keyboard-shortcut-only affordance, since the target audience can't be
assumed to know one. Owns the always-visible pause icon; the overlay panel
(Resume / Restart / Fullscreen toggle / Quit to Menu / Quit App) only shows
while paused.
"""
from __future__ import annotations

from typing import Callable

import pygame

from . import settings, theme
from .widgets import Button, draw_dim_overlay, draw_panel, draw_text

PANEL_SIZE = (440, 520)


class PauseMenu:
    def __init__(
        self,
        size: tuple[int, int],
        on_restart: Callable[[], None],
        on_quit_to_menu: Callable[[], None],
        on_quit_app: Callable[[], None],
    ):
        self.size = size
        self.visible = False
        self._on_restart = on_restart
        self._on_quit_to_menu = on_quit_to_menu
        self._on_quit_app = on_quit_app
        self.pause_icon_rect = pygame.Rect(size[0] - 74, 18, 54, 54)
        self._panel = pygame.Rect(0, 0, *PANEL_SIZE)
        self._panel.center = (size[0] // 2, size[1] // 2)
        self._buttons: list[Button] = []

    def open(self) -> None:
        self.visible = True
        self._rebuild_buttons()

    def close(self) -> None:
        self.visible = False

    def toggle(self) -> None:
        self.close() if self.visible else self.open()

    def _rebuild_buttons(self) -> None:
        w, h, gap = 360, theme.MIN_TOUCH_TARGET, 18
        x = self._panel.centerx - w // 2
        y = self._panel.top + 90
        fs_label = "Fullscreen: On" if settings.get("fullscreen") else "Fullscreen: Off"
        specs = [
            ("Resume", self.close, theme.SECONDARY, False),
            ("Restart Game", self._on_restart, theme.ACCENT, False),
            (fs_label, self._toggle_fullscreen, theme.PRIMARY, True),
            ("Quit to Menu", self._on_quit_to_menu, theme.TEXT_MUTED, False),
            ("Quit App", self._on_quit_app, (196, 90, 90), False),
        ]
        self._buttons = []
        for i, (label, action, color, keep_open) in enumerate(specs):
            rect = (x, y + i * (h + gap), w, h)
            self._buttons.append(
                Button(rect, label, self._wrap(action, keep_open), color=color, font_size=25)
            )

    def _wrap(self, action: Callable[[], None], keep_open: bool) -> Callable[[], None]:
        def run() -> None:
            action()
            if keep_open:
                self._rebuild_buttons()  # refresh e.g. the fullscreen label
            else:
                self.close()

        return run

    def _toggle_fullscreen(self) -> None:
        settings.set("fullscreen", not settings.get("fullscreen"))

    def handle_event(self, event: pygame.event.Event) -> bool:
        """Returns True if this event was consumed by the pause UI and
        should not reach the game underneath.
        """
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.toggle()
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not self.visible and self.pause_icon_rect.collidepoint(event.pos):
                self.open()
                return True
        if self.visible:
            for btn in self._buttons:
                btn.handle_event(event)
            return True  # swallow all input while paused
        return False

    def draw(self, surface: pygame.Surface) -> None:
        pygame.draw.rect(surface, theme.TEXT_MUTED, self.pause_icon_rect, border_radius=10)
        pygame.draw.rect(surface, theme.TEXT_DARK, self.pause_icon_rect, width=2, border_radius=10)
        cx, cy = self.pause_icon_rect.center
        pygame.draw.rect(surface, theme.TEXT_LIGHT, (cx - 13, cy - 13, 7, 26))
        pygame.draw.rect(surface, theme.TEXT_LIGHT, (cx + 6, cy - 13, 7, 26))

        if not self.visible:
            return
        draw_dim_overlay(surface)
        draw_panel(surface, self._panel)
        draw_text(surface, "Paused", (self._panel.centerx, self._panel.top + 44), size=34, bold=True, center=True)
        for btn in self._buttons:
            btn.draw(surface)
