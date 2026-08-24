"""Go Fish Pygame screen: human (You) vs one AI opponent."""
from __future__ import annotations

import pygame

from audio.manager import audio
from core.ai.base import DIFFICULTY_LABELS, Difficulty
from core.card import Rank
from ui import theme
from ui.pause import PauseMenu
from ui.screen import Screen
from ui.widgets import (
    Button,
    Confetti,
    draw_card_back,
    draw_card_face,
    draw_game_over_modal,
    draw_panel,
    draw_text,
    modal_button_rects,
)

from .game import GoFishGame

AI_NAME = "Fox"
HUMAN_NAME = "You"
AI_TURN_DELAY = 0.9
DEAL_DURATION = 0.35
DEAL_STAGGER = 0.05


class GoFishScreen(Screen):
    def __init__(self, size: tuple[int, int], difficulty: Difficulty, on_menu):
        super().__init__(size)
        self.on_menu = on_menu
        self.difficulty = difficulty
        self.game = GoFishGame(
            [HUMAN_NAME, AI_NAME], ai_difficulties={AI_NAME: difficulty}, seed=None
        )
        self.message = f"Ask {AI_NAME} for a card you'd like!"
        self._ai_timer = 0.0
        self._waiting_for_ai = False
        self._confetti: Confetti | None = None
        self._end_buttons: list[Button] = []
        self._card_rects: list[tuple[pygame.Rect, Rank]] = []
        self._deal_elapsed = 0.0
        self._pause = PauseMenu(
            size,
            on_restart=self._restart,
            on_quit_to_menu=lambda: self.go_to(self.on_menu()),
            on_quit_app=self._quit_app,
        )
        audio.play_sfx("card_move")  # the initial deal
        self._maybe_start_ai_turn()

    def _quit_app(self) -> None:
        self.quit_requested = True

    # -- game flow ------------------------------------------------------
    def _maybe_start_ai_turn(self) -> None:
        if self.game.game_over:
            self._on_game_over()
            return
        if self.game.is_ai_turn():
            self._waiting_for_ai = True
            self._ai_timer = AI_TURN_DELAY

    def _run_ai_turn(self) -> None:
        result = self.game.take_ai_turn()
        if result.cards_transferred:
            self.message = f"{AI_NAME} asks You for {result.rank.name.title()}s... and gets {result.cards_transferred}!"
            audio.play_sfx("match")
        elif result.asker_drew_matched:
            self.message = f"{AI_NAME} asks You for {result.rank.name.title()}s, goes fish, and draws one!"
            audio.play_sfx("match")
        else:
            self.message = f"{AI_NAME} asks You for {result.rank.name.title()}s... Go Fish!"
            audio.play_sfx("miss")
        self._waiting_for_ai = False
        self._maybe_start_ai_turn()

    def _human_ask(self, rank: Rank) -> None:
        if self.game.game_over or self.game.is_ai_turn():
            return
        audio.play_sfx("card_select")
        result = self.game.ask(HUMAN_NAME, AI_NAME, rank)
        rank_name = rank.name.title()
        if result.cards_transferred:
            self.message = f"{AI_NAME} hands over {result.cards_transferred} {rank_name}(s)! Go again."
            audio.play_sfx("match")
        elif result.asker_drew_matched:
            self.message = f"Go Fish! But you drew a {rank_name} yourself — go again!"
            audio.play_sfx("match")
        else:
            self.message = "Go Fish! Your turn is over."
            audio.play_sfx("miss")
        self._maybe_start_ai_turn()

    def _on_game_over(self) -> None:
        if self.game.winner == HUMAN_NAME:
            self.message = "You collected the most books! Great job!"
            self._confetti = Confetti(pygame.Rect(0, 0, *self.size))
            audio.play_sfx("win")
        elif self.game.winner == AI_NAME:
            self.message = f"{AI_NAME} collected the most books this time. Play again?"
            audio.play_sfx("loss")
        else:
            self.message = "It's a tie! Nicely played."
        left_rect, right_rect = modal_button_rects(self.size)
        self._end_buttons = [
            Button(left_rect, "Play Again", self._restart, color=theme.SUCCESS, font_size=28),
            Button(right_rect, "Menu", lambda: self.go_to(self.on_menu()), color=theme.TEXT_MUTED, font_size=28),
        ]

    def _restart(self) -> None:
        self.go_to(GoFishScreen(self.size, self.difficulty, self.on_menu))

    # -- Screen interface -------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        if not self.game.game_over and self._pause.handle_event(event):
            return
        for btn in self._end_buttons:
            btn.handle_event(event)
        if self._waiting_for_ai or self.game.game_over or self._pause.visible:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            # Cards can overlap slightly when a hand is large; check in
            # reverse draw order so a click resolves to the visually
            # topmost (later-drawn) card, not whichever one happens to be
            # first in the list.
            for rect, rank in reversed(self._card_rects):
                if rect.collidepoint(event.pos):
                    self._human_ask(rank)
                    return

    def update(self, dt: float) -> None:
        if self._pause.visible:
            return
        self._deal_elapsed += dt
        if self._waiting_for_ai:
            self._ai_timer -= dt
            if self._ai_timer <= 0:
                self._run_ai_turn()
        if self._confetti is not None:
            self._confetti.update(dt)
            if self._confetti.done():
                self._confetti = None

    def draw(self, surface: pygame.Surface) -> None:
        surface.fill(theme.BACKGROUND)
        draw_text(surface, "Go Fish", (30, 24), size=40, bold=True)
        draw_text(
            surface,
            f"Playing against {AI_NAME} ({DIFFICULTY_LABELS[self.difficulty]})",
            (30, 74),
            size=22,
            color=theme.TEXT_MUTED,
        )

        ai_player = self.game.players[AI_NAME]
        human_player = self.game.players[HUMAN_NAME]

        # AI area
        draw_text(surface, f"{AI_NAME}'s hand: {len(ai_player.hand)} cards", (30, 130), size=26, bold=True)
        self._draw_backs(surface, len(ai_player.hand), y=170)
        draw_text(surface, f"Books: {len(ai_player.books)}", (30, 282), size=24, color=theme.TEXT_MUTED)

        # Middle: pond + message
        draw_text(surface, f"Pond: {len(self.game.stock)} cards left", (self.size[0] // 2, 320), size=24, color=theme.TEXT_MUTED, center=True)
        if not self.game.game_over:
            msg_rect = pygame.Rect(60, 350, self.size[0] - 120, 90)
            draw_panel(surface, msg_rect, color=theme.PANEL)
            draw_text(surface, self.message, msg_rect.center, size=26, center=True)

        # Human area
        draw_text(surface, f"Your hand — click a card to ask for it! Books: {len(human_player.books)}", (30, 470), size=26, bold=True)
        self._card_rects = self._draw_hand(surface, human_player.hand.cards, y=510)

        if self.game.game_over:
            draw_game_over_modal(surface, self.size, self.message)
            for btn in self._end_buttons:
                btn.draw(surface)
        else:
            self._pause.draw(surface)
        if self._confetti is not None:
            self._confetti.draw(surface)

    def _draw_backs(self, surface: pygame.Surface, count: int, y: int) -> None:
        card_w, card_h = 70, 100
        x = 30
        for i in range(count):
            rect = pygame.Rect(x, y, card_w, card_h)
            draw_card_back(surface, rect)
            x += 26

    def _draw_hand(self, surface: pygame.Surface, cards, y: int) -> list[tuple[pygame.Rect, Rank]]:
        card_w = 90
        margin, row_gap, bottom_margin = 30, 14, 20
        # Space cards MIN_TOUCH_TARGET apart (not by however many happen to
        # fit in one row) so every card's clickable strip stays at least
        # touch-target width, wrapping to additional rows for large hands
        # instead of shrinking hit targets below that floor. If a large
        # hand needs more rows than fit at full height, shrink card height
        # (never the touch-target-wide gap) so it still fits the window.
        gap = theme.MIN_TOUCH_TARGET
        available_width = self.size[0] - 2 * margin
        cards_per_row = max(1, (available_width - card_w) // gap + 1)
        rows_needed = max(1, -(-len(cards) // cards_per_row)) if cards else 1

        available_height = max(1, self.size[1] - y - bottom_margin)
        max_card_h = (available_height - (rows_needed - 1) * row_gap) // rows_needed
        card_h = max(70, min(130, max_card_h))

        rects = []
        for i, card in enumerate(cards):
            row, col = divmod(i, cards_per_row)
            rect = pygame.Rect(margin + col * gap, y + row * (card_h + row_gap), card_w, card_h)
            draw_rect = self._dealt_position(rect, i)
            draw_card_face(surface, draw_rect, card.label, card.symbol, card.is_red)
            rects.append((rect, card.rank))  # click hit-testing always uses the final rect
        return rects

    def _dealt_position(self, final_rect: pygame.Rect, index: int) -> pygame.Rect:
        """A staggered slide-up-into-place deal animation for the initial
        hand. Cheap to compute and a no-op past its short window, so cards
        drawn later mid-game (well outside any card's stagger + duration)
        just render at their final position with no extra work.
        """
        local_t = self._deal_elapsed - index * DEAL_STAGGER
        if local_t >= DEAL_DURATION:
            return final_rect
        progress = max(0.0, min(1.0, local_t / DEAL_DURATION))
        eased = 1 - (1 - progress) ** 3
        start_y = self.size[1] + 40
        animated = final_rect.copy()
        animated.y = int(start_y + (final_rect.y - start_y) * eased)
        return animated
