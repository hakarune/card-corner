"""Memory/Concentration Pygame screen: human (You) vs one AI opponent.

Engine state (`game.matched`, `game.known_positions`) updates immediately
when a flip resolves; the screen's own `self._visible` set is the single
source of truth for what's rendered face-up at any instant, so a match can
be staged as "reveal first card, pause, reveal second card, pause" purely
for readability without the engine and the animation getting out of sync.
"""
from __future__ import annotations

from typing import Callable, Optional

import pygame

from audio.manager import audio
from core.ai.base import DIFFICULTY_LABELS, Difficulty
from ui import theme
from ui.pause import PauseMenu
from ui.screen import Screen
from ui.widgets import (
    Button,
    Confetti,
    draw_card_face,
    draw_face_down_tile,
    draw_flip,
    draw_game_over_modal,
    draw_panel,
    draw_text,
    modal_button_rects,
)

from .game import MemoryGame

AI_NAME = "Fox"
HUMAN_NAME = "You"
AI_TURN_DELAY = 0.7
REVEAL_GAP = 0.7
RESOLVE_PAUSE = 0.9
NUM_PAIRS = 6
GRID_COLS = 4
FLIP_DURATION = 0.28


class MemoryScreen(Screen):
    def __init__(self, size: tuple[int, int], difficulty: Difficulty, on_menu):
        super().__init__(size)
        self.on_menu = on_menu
        self.difficulty = difficulty
        self.game = MemoryGame(
            [HUMAN_NAME, AI_NAME], num_pairs=NUM_PAIRS, ai_difficulties={AI_NAME: difficulty}, seed=None
        )
        self.message = "Flip two cards to find a match!"
        self._visible: set[int] = set()
        self._human_first: Optional[int] = None
        self._locked = False
        self._timer = 0.0
        self._pending_callback: Optional[Callable[[], None]] = None
        self._confetti: Confetti | None = None
        self._end_buttons: list[Button] = []
        self._tile_rects: list[tuple[int, pygame.Rect]] = []
        self._flip_anim: dict[int, float] = {}
        self._prev_shown: set[int] = set()
        self._pause = PauseMenu(
            size,
            on_restart=self._restart,
            on_quit_to_menu=lambda: self.go_to(self.on_menu()),
            on_quit_app=self._quit_app,
        )
        self._maybe_start_ai_turn()

    def _quit_app(self) -> None:
        self.quit_requested = True

    # -- timing helper ----------------------------------------------------
    def _schedule(self, delay: float, callback: Callable[[], None]) -> None:
        self._timer = delay
        self._pending_callback = callback
        self._locked = True

    # -- game flow ----------------------------------------------------------
    def _maybe_start_ai_turn(self) -> None:
        if self.game.game_over:
            self._on_game_over()
            return
        if self.game.is_ai_turn():
            self._schedule(AI_TURN_DELAY, self._run_ai_turn)

    def _run_ai_turn(self) -> None:
        result = self.game.take_ai_turn()
        self._visible.add(result.pos1)
        audio.play_sfx("card_move")

        def reveal_second() -> None:
            self._visible.add(result.pos2)
            audio.play_sfx("card_move")

            def finish() -> None:
                if result.matched:
                    self.message = f"{AI_NAME} found a match!"
                    audio.play_sfx("match")
                else:
                    self._visible.discard(result.pos1)
                    self._visible.discard(result.pos2)
                    self.message = f"{AI_NAME} didn't find a match."
                    audio.play_sfx("miss")
                self._maybe_start_ai_turn()

            self._schedule(RESOLVE_PAUSE, finish)

        self._schedule(REVEAL_GAP, reveal_second)

    def _human_click(self, pos: int) -> None:
        if self._locked or self.game.game_over or self.game.is_ai_turn():
            return
        if pos in self.game.matched or pos in self._visible:
            return

        if self._human_first is None:
            self._human_first = pos
            self._visible.add(pos)
            audio.play_sfx("card_select")
            return
        if pos == self._human_first:
            return

        first, second = self._human_first, pos
        self._human_first = None
        self._visible.add(second)
        audio.play_sfx("card_select")
        result = self.game.flip_two(HUMAN_NAME, first, second)

        if result.matched:
            self.message = "Match! Go again."
            audio.play_sfx("match")
            self._maybe_start_ai_turn()
        else:
            self.message = "No match this time — try again!"
            audio.play_sfx("miss")

            def hide() -> None:
                self._visible.discard(first)
                self._visible.discard(second)
                self.message = "Flip two cards to find a match!"
                self._maybe_start_ai_turn()

            self._schedule(RESOLVE_PAUSE, hide)

    def _on_game_over(self) -> None:
        human_score = self.game.players[HUMAN_NAME].score
        ai_score = self.game.players[AI_NAME].score
        if human_score > ai_score:
            self.message = f"You win, {human_score} to {ai_score}!"
            self._confetti = Confetti(pygame.Rect(0, 0, *self.size))
            audio.play_sfx("win")
        elif ai_score > human_score:
            self.message = f"{AI_NAME} wins, {ai_score} to {human_score}. Play again?"
            audio.play_sfx("loss")
        else:
            self.message = f"It's a tie, {human_score} to {ai_score}!"
        left_rect, right_rect = modal_button_rects(self.size)
        self._end_buttons = [
            Button(left_rect, "Play Again", self._restart, color=theme.SUCCESS, font_size=26),
            Button(right_rect, "Menu", lambda: self.go_to(self.on_menu()), color=theme.TEXT_MUTED, font_size=26),
        ]

    def _restart(self) -> None:
        self.go_to(MemoryScreen(self.size, self.difficulty, self.on_menu))

    # -- Screen interface -------------------------------------------------
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
                    self._human_click(pos)
                    return

    def update(self, dt: float) -> None:
        if self._pause.visible:
            return
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

        # Start a flip animation for any tile whose shown/hidden state just
        # changed, and age out any animations already in progress.
        shown_now = self._visible | self.game.matched
        for pos in shown_now.symmetric_difference(self._prev_shown):
            self._flip_anim[pos] = 0.0
        self._prev_shown = shown_now
        for pos in list(self._flip_anim):
            self._flip_anim[pos] += dt
            if self._flip_anim[pos] >= FLIP_DURATION:
                del self._flip_anim[pos]

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(theme.BACKGROUND)
        draw_text(surface, "Memory", (30, 24), size=40, bold=True)
        draw_text(
            surface,
            f"Playing against {AI_NAME} ({DIFFICULTY_LABELS[self.difficulty]})",
            (30, 74),
            size=22,
            color=theme.TEXT_MUTED,
        )
        draw_text(
            surface,
            f"You: {self.game.players[HUMAN_NAME].score}    {AI_NAME}: {self.game.players[AI_NAME].score}",
            (self.size[0] - 260, 40),
            size=30,
            bold=True,
        )

        msg_rect = pygame.Rect(60, 110, self.size[0] - 120, 70)
        draw_panel(surface, msg_rect)
        draw_text(surface, self.message, msg_rect.center, size=26, center=True)

        self._tile_rects = self._draw_board(surface, y_start=200)

        if self.game.game_over:
            draw_game_over_modal(surface, self.size, self.message)
            for btn in self._end_buttons:
                btn.draw(surface)
        else:
            self._pause.draw(surface)
        if self._confetti is not None:
            self._confetti.draw(surface)

    def _draw_board(self, surface: pygame.Surface, y_start: int) -> list[tuple[int, pygame.Rect]]:
        n = len(self.game.board)
        cols = GRID_COLS
        tile_w, tile_h, gap = 125, 125, 18
        grid_w = cols * tile_w + (cols - 1) * gap
        start_x = (self.size[0] - grid_w) // 2

        rects = []
        for pos in range(n):
            col = pos % cols
            row = pos // cols
            rect = pygame.Rect(
                start_x + col * (tile_w + gap), y_start + row * (tile_h + gap), tile_w, tile_h
            )
            card = self.game.board[pos]
            face_up = pos in self._visible or pos in self.game.matched

            def render_back(surf, r) -> None:
                draw_face_down_tile(surf, r, theme.GAME_COLORS["memory"])

            def render_face(surf, r, card=card) -> None:
                draw_card_face(surf, r, card.label, card.symbol, card.is_red)

            if pos in self._flip_anim:
                progress = self._flip_anim[pos] / FLIP_DURATION
                # Reveals flip back->face; hides flip face->back — pick the
                # order so the second half always lands on the true state.
                first, second = (render_back, render_face) if face_up else (render_face, render_back)
                draw_flip(surface, rect, progress, first, second)
            elif face_up:
                render_face(surface, rect)
            else:
                render_back(surface, rect)
            rects.append((pos, rect))
        return rects
