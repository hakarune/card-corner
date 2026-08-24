"""Letter Match Pygame screen: solo, no AI opponent, no win/lose framing —
just gentle positive reinforcement on a match and a no-penalty retry on a
miss (spec §5.4).
"""
from __future__ import annotations

from typing import Callable, Optional

import pygame

from audio.manager import audio
from ui import theme
from ui.pause import PauseMenu
from ui.screen import Screen
from ui.widgets import (
    Button,
    Confetti,
    draw_game_over_modal,
    draw_letter_tile,
    draw_panel,
    draw_text,
    modal_button_rects,
)

from .game import DEFAULT_LETTER_COUNT, LetterMatchGame

RESOLVE_PAUSE = 0.7
GRID_COLS = 4


class LetterMatchScreen(Screen):
    def __init__(self, size: tuple[int, int], on_menu):
        super().__init__(size)
        self.on_menu = on_menu
        self.game = LetterMatchGame(letter_count=DEFAULT_LETTER_COUNT, seed=None)
        self.message = "Match each big letter to its little letter!"
        self._locked = False
        self._timer = 0.0
        self._pending_callback: Optional[Callable[[], None]] = None
        self._elapsed = 0.0
        self._confetti: Confetti | None = None
        self._end_buttons: list[Button] = []
        self._tile_rects: list[tuple[int, pygame.Rect]] = []
        self._pause = PauseMenu(
            size,
            on_restart=self._restart,
            on_quit_to_menu=lambda: self.go_to(self.on_menu()),
            on_quit_app=self._quit_app,
        )

    def _quit_app(self) -> None:
        self.quit_requested = True

    def _schedule(self, delay: float, callback: Callable[[], None]) -> None:
        self._timer = delay
        self._pending_callback = callback
        self._locked = True

    def _click(self, pos: int) -> None:
        if self._locked or self.game.game_over:
            return
        result = self.game.click(pos)
        if not result.accepted:
            return
        if result.pos2 is None:
            audio.play_sfx("card_select")
            return  # first pick of the pair, just wait for the second click

        if result.matched:
            self.message = "Great match!"
            audio.play_sfx("match")
            rect = dict(self._tile_rects).get(pos)
            if rect is not None:
                self._confetti = Confetti(rect, count=26, duration=1.0)
            if self.game.game_over:
                self._locked = True
                self._schedule(0.6, self._on_complete)
        else:
            self.message = "Not quite — try again!"
            audio.play_sfx("miss")
            first, second = result.pos1, result.pos2

            def clear() -> None:
                self.message = "Match each big letter to its little letter!"

            self._schedule(RESOLVE_PAUSE, clear)

    def _on_complete(self) -> None:
        self.message = f"All done! Accuracy: {round(self.game.accuracy * 100)}%"
        self._confetti = Confetti(pygame.Rect(0, 0, *self.size))
        audio.play_sfx("win")
        left_rect, right_rect = modal_button_rects(self.size)
        self._end_buttons = [
            Button(left_rect, "Play Again", self._restart, color=theme.SUCCESS, font_size=26),
            Button(right_rect, "Menu", lambda: self.go_to(self.on_menu()), color=theme.TEXT_MUTED, font_size=26),
        ]

    def _restart(self) -> None:
        self.go_to(LetterMatchScreen(self.size, self.on_menu))

    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.game.game_over and self._pause.handle_event(event):
            return
        for btn in self._end_buttons:
            btn.handle_event(event)
        if self._locked or self.game.game_over or self._pause.visible:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for pos, rect in self._tile_rects:
                if rect.collidepoint(event.pos):
                    self._click(pos)
                    return

    def update(self, dt: float) -> None:
        if self._pause.visible:
            return
        if not self.game.game_over:
            self._elapsed += dt
        if self._pending_callback is not None:
            self._timer -= dt
            if self._timer <= 0:
                cb = self._pending_callback
                self._pending_callback = None
                self._locked = False
                cb()
        if self._confetti is not None:
            self._confetti.update(dt)
            if self._confetti.done():
                self._confetti = None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(theme.BACKGROUND)
        draw_text(surface, "Letter Match", (30, 24), size=40, bold=True)
        draw_text(surface, f"Time: {int(self._elapsed)}s", (self.size[0] - 200, 40), size=28, bold=True)

        msg_rect = pygame.Rect(60, 110, self.size[0] - 120, 70)
        draw_panel(surface, msg_rect)
        draw_text(surface, self.message, msg_rect.center, size=26, center=True)

        self._tile_rects = self._draw_board(surface, y_start=200)

        if self.game.game_over:
            draw_game_over_modal(surface, self.size, self.message)
        else:
            self._pause.draw(surface)
        for btn in self._end_buttons:
            btn.draw(surface)
        if self._confetti is not None:
            self._confetti.draw(surface)

    def _draw_board(self, surface: pygame.Surface, y_start: int) -> list[tuple[int, pygame.Rect]]:
        n = len(self.game.board)
        cols = GRID_COLS
        tile_w, tile_h, gap = 125, 125, 18
        grid_w = cols * tile_w + (cols - 1) * gap
        start_x = (self.size[0] - grid_w) // 2

        color = theme.GAME_COLORS["letter_match"]
        rects = []
        for pos in range(n):
            col = pos % cols
            row = pos // cols
            rect = pygame.Rect(
                start_x + col * (tile_w + gap), y_start + row * (tile_h + gap), tile_w, tile_h
            )
            if pos in self.game.matched:
                draw_letter_tile(surface, rect, self.game.board[pos].display, theme.SUCCESS)
            elif pos == self.game.pending_first:
                draw_letter_tile(surface, rect, self.game.board[pos].display, theme.ACCENT)
            else:
                draw_letter_tile(surface, rect, self.game.board[pos].display, color)
            rects.append((pos, rect))
        return rects
