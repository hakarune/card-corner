"""Old Maid Pygame screen: human (You) vs one AI opponent. The "loser" is
framed lightly and positively — a gentle animation, not a mean one.
"""
from __future__ import annotations

import pygame

from core.ai.base import DIFFICULTY_LABELS, Difficulty
from ui import theme
from ui.screen import Screen
from ui.widgets import Button, Confetti, draw_card_back, draw_card_face, draw_panel, draw_text

from .game import OldMaidGame

AI_NAME = "Fox"
HUMAN_NAME = "You"
AI_TURN_DELAY = 0.9
DEAL_DURATION = 0.35
DEAL_STAGGER = 0.05


class OldMaidScreen(Screen):
    def __init__(self, size: tuple[int, int], difficulty: Difficulty, on_menu):
        super().__init__(size)
        self.on_menu = on_menu
        self.difficulty = difficulty
        self.game = OldMaidGame(
            [HUMAN_NAME, AI_NAME], ai_difficulties={AI_NAME: difficulty}, seed=None
        )
        self.message = f"Draw a card from {AI_NAME}'s hand — click it!"
        self._ai_timer = 0.0
        self._waiting_for_ai = False
        self._confetti: Confetti | None = None
        self._end_buttons: list[Button] = []
        self._ai_hand_rect: pygame.Rect | None = None
        self._deal_elapsed = 0.0
        self._maybe_start_ai_turn()

    def _maybe_start_ai_turn(self) -> None:
        if self.game.game_over:
            self._on_game_over()
            return
        if self.game.is_ai_turn():
            self._waiting_for_ai = True
            self._ai_timer = AI_TURN_DELAY
            self.message = f"{AI_NAME} is picking a card from your hand..."

    def _run_ai_turn(self) -> None:
        result = self.game.draw(AI_NAME, HUMAN_NAME)
        if result.paired_ranks:
            self.message = f"{AI_NAME} drew a match! Pair set aside."
        else:
            self.message = f"{AI_NAME} drew a card — no match yet."
        self._waiting_for_ai = False
        self._maybe_start_ai_turn()

    def _human_draw(self) -> None:
        if self.game.game_over or self.game.is_ai_turn():
            return
        result = self.game.draw(HUMAN_NAME, AI_NAME)
        if result.paired_ranks:
            self.message = "You got a match! Nicely done."
        else:
            self.message = "No match this time — your turn is over."
        self._maybe_start_ai_turn()

    def _on_game_over(self) -> None:
        if self.game.loser == HUMAN_NAME:
            self.message = "You're holding the Old Maid! Good game — want a rematch?"
        elif self.game.loser == AI_NAME:
            self.message = f"{AI_NAME} got stuck with the Old Maid! You win!"
            self._confetti = Confetti(pygame.Rect(0, 0, *self.size))
        else:
            self.message = "Good game!"
        cx = self.size[0] // 2
        self._end_buttons = [
            Button((cx - 220, 555, 200, theme.MIN_TOUCH_TARGET), "Play Again", self._restart, color=theme.SUCCESS, font_size=28),
            Button((cx + 20, 555, 200, theme.MIN_TOUCH_TARGET), "Menu", lambda: self.go_to(self.on_menu()), color=theme.TEXT_MUTED, font_size=28),
        ]

    def _restart(self) -> None:
        self.go_to(OldMaidScreen(self.size, self.difficulty, self.on_menu))

    def handle_event(self, event: pygame.event.Event) -> None:
        for btn in self._end_buttons:
            btn.handle_event(event)
        if self._waiting_for_ai or self.game.game_over:
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._ai_hand_rect is not None and self._ai_hand_rect.collidepoint(event.pos):
                if not self.game.players[AI_NAME].hand.is_empty():
                    self._human_draw()

    def update(self, dt: float) -> None:
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
        draw_text(surface, "Old Maid", (30, 24), size=40, bold=True)
        draw_text(
            surface,
            f"Playing against {AI_NAME} ({DIFFICULTY_LABELS[self.difficulty]})",
            (30, 74),
            size=22,
            color=theme.TEXT_MUTED,
        )

        ai_player = self.game.players[AI_NAME]
        human_player = self.game.players[HUMAN_NAME]

        active = not self.game.game_over and not self.game.is_ai_turn() and not ai_player.hand.is_empty()
        draw_text(surface, f"{AI_NAME}'s hand: {len(ai_player.hand)} cards", (30, 130), size=26, bold=True)
        self._ai_hand_rect = self._draw_backs(
            surface, len(ai_player.hand), y=170, highlight=active
        )
        draw_text(surface, f"Pairs found: {len(ai_player.books) // 1}", (30, 260), size=24, color=theme.TEXT_MUTED)

        msg_rect = pygame.Rect(60, 320, self.size[0] - 120, 90)
        draw_panel(surface, msg_rect, color=theme.PANEL)
        draw_text(surface, self.message, msg_rect.center, size=26, center=True)

        draw_text(surface, f"Your hand — pairs found: {len(human_player.books)}", (30, 470), size=26, bold=True)
        self._draw_hand(surface, human_player.hand.cards, y=510)

        if self.game.game_over:
            for btn in self._end_buttons:
                btn.draw(surface)
        if self._confetti is not None:
            self._confetti.draw(surface)

    def _draw_backs(self, surface: pygame.Surface, count: int, y: int, highlight: bool) -> pygame.Rect | None:
        if count == 0:
            return None
        card_w, card_h = 70, 100
        x = 30
        first_rect = None
        for i in range(count):
            rect = pygame.Rect(x, y, card_w, card_h)
            draw_card_back(surface, rect)
            if highlight:
                pygame.draw.rect(surface, theme.ACCENT, rect, width=4, border_radius=12)
            if first_rect is None:
                first_rect = rect
            x += 26
        return pygame.Rect(30, y, x - 30 + card_w - 26, card_h)

    def _draw_hand(self, surface: pygame.Surface, cards, y: int) -> None:
        card_w, card_h = 90, 130
        gap = min(70, max(20, (self.size[0] - 60 - card_w) // max(len(cards), 1)))
        x = 30
        for i, card in enumerate(cards):
            rect = pygame.Rect(x, y, card_w, card_h)
            draw_card_face(surface, self._dealt_position(rect, i), card.label, card.symbol, card.is_red)
            x += gap

    def _dealt_position(self, final_rect: pygame.Rect, index: int) -> pygame.Rect:
        """A staggered slide-up-into-place deal animation for the initial
        hand; a no-op past its short window (see the identical helper in
        games/go_fish/screen.py for the full rationale).
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
