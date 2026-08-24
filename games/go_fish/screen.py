"""Go Fish Pygame screen: human (You) vs one AI opponent."""
from __future__ import annotations

import pygame

from core.ai.base import DIFFICULTY_LABELS, Difficulty
from core.card import Rank
from ui import theme
from ui.screen import Screen
from ui.widgets import Button, Confetti, draw_card_back, draw_card_face, draw_panel, draw_text

from .game import GoFishGame

AI_NAME = "Fox"
HUMAN_NAME = "You"
AI_TURN_DELAY = 0.9


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
        self._maybe_start_ai_turn()

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
        elif result.asker_drew_matched:
            self.message = f"{AI_NAME} asks You for {result.rank.name.title()}s, goes fish, and draws one!"
        else:
            self.message = f"{AI_NAME} asks You for {result.rank.name.title()}s... Go Fish!"
        self._waiting_for_ai = False
        self._maybe_start_ai_turn()

    def _human_ask(self, rank: Rank) -> None:
        if self.game.game_over or self.game.is_ai_turn():
            return
        result = self.game.ask(HUMAN_NAME, AI_NAME, rank)
        rank_name = rank.name.title()
        if result.cards_transferred:
            self.message = f"{AI_NAME} hands over {result.cards_transferred} {rank_name}(s)! Go again."
        elif result.asker_drew_matched:
            self.message = f"Go Fish! But you drew a {rank_name} yourself — go again!"
        else:
            self.message = "Go Fish! Your turn is over."
        self._maybe_start_ai_turn()

    def _on_game_over(self) -> None:
        if self.game.winner == HUMAN_NAME:
            self.message = "You collected the most books! Great job!"
            self._confetti = Confetti(pygame.Rect(0, 0, *self.size))
        elif self.game.winner == AI_NAME:
            self.message = f"{AI_NAME} collected the most books this time. Play again?"
        else:
            self.message = "It's a tie! Nicely played."
        cx = self.size[0] // 2
        self._end_buttons = [
            Button((cx - 220, 560, 200, 70), "Play Again", self._restart, color=theme.SUCCESS, font_size=28),
            Button((cx + 20, 560, 200, 70), "Menu", lambda: self.go_to(self.on_menu()), color=theme.TEXT_MUTED, font_size=28),
        ]

    def _restart(self) -> None:
        self.go_to(GoFishScreen(self.size, self.difficulty, self.on_menu))

    # -- Screen interface -------------------------------------------------
    def handle_event(self, event: pygame.event.Event) -> None:
        for btn in self._end_buttons:
            btn.handle_event(event)
        if self._waiting_for_ai or self.game.game_over:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for rect, rank in self._card_rects:
                if rect.collidepoint(event.pos):
                    self._human_ask(rank)
                    return

    def update(self, dt: float) -> None:
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
        draw_text(surface, f"Books: {len(ai_player.books)}", (30, 260), size=24, color=theme.TEXT_MUTED)

        # Middle: pond + message
        draw_text(surface, f"Pond: {len(self.game.stock)} cards left", (self.size[0] // 2, 320), size=24, color=theme.TEXT_MUTED, center=True)
        msg_rect = pygame.Rect(60, 350, self.size[0] - 120, 90)
        draw_panel(surface, msg_rect, color=theme.PANEL)
        draw_text(surface, self.message, msg_rect.center, size=26, center=True)

        # Human area
        draw_text(surface, f"Your hand — click a card to ask for it! Books: {len(human_player.books)}", (30, 470), size=26, bold=True)
        self._card_rects = self._draw_hand(surface, human_player.hand.cards, y=510)

        if self.game.game_over:
            for btn in self._end_buttons:
                btn.draw(surface)
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
        card_w, card_h = 90, 130
        gap = min(70, max(20, (self.size[0] - 60 - card_w) // max(len(cards), 1)))
        x = 30
        rects = []
        for card in cards:
            rect = pygame.Rect(x, y, card_w, card_h)
            draw_card_face(surface, rect, card.label, card.symbol, card.is_red)
            rects.append((rect, card.rank))
            x += gap
        return rects
