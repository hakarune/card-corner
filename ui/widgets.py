"""Shared kid-friendly widgets: buttons, card/tile sprites, and celebration
effects. Every game screen renders through these rather than drawing its
own ad-hoc shapes, so the four games stay visually consistent (spec §6).
"""
from __future__ import annotations

import random
from typing import Callable

import pygame

from . import theme


class Button:
    def __init__(
        self,
        rect: tuple[int, int, int, int],
        label: str,
        on_click: Callable[[], None],
        color: tuple[int, int, int] = theme.PRIMARY,
        text_color: tuple[int, int, int] = theme.TEXT_LIGHT,
        font_size: int = 30,
        enabled: bool = True,
    ):
        self.rect = pygame.Rect(rect)
        self.label = label
        self.on_click = on_click
        self.color = color
        self.text_color = text_color
        self.font = theme.get_font(font_size, bold=True)
        self.enabled = enabled
        self.hovered = False

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.enabled:
            return False
        if event.type == pygame.MOUSEMOTION:
            self.hovered = self.rect.collidepoint(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                self.on_click()
                return True
        return False

    def draw(self, surface: pygame.Surface) -> None:
        color = self.color if self.enabled else theme.TEXT_MUTED
        if self.enabled and self.hovered:
            color = tuple(min(255, c + 24) for c in color)
        pygame.draw.rect(surface, color, self.rect, border_radius=18)
        pygame.draw.rect(surface, theme.TEXT_DARK, self.rect, width=3, border_radius=18)
        text_surf = self.font.render(self.label, True, self.text_color)
        surface.blit(text_surf, text_surf.get_rect(center=self.rect.center))


def draw_card_back(surface: pygame.Surface, rect: pygame.Rect) -> None:
    pygame.draw.rect(surface, theme.CARD_BACK, rect, border_radius=12)
    pygame.draw.rect(surface, theme.CARD_BORDER, rect, width=3, border_radius=12)
    center = rect.center
    r = min(rect.width, rect.height) // 5
    pygame.draw.circle(surface, theme.CARD_BACK_PATTERN, center, r, width=4)
    pygame.draw.circle(surface, theme.CARD_BACK_PATTERN, center, max(r - 14, 4))


def draw_card_face(
    surface: pygame.Surface, rect: pygame.Rect, label: str, symbol: str, is_red: bool
) -> None:
    pygame.draw.rect(surface, theme.CARD_FACE, rect, border_radius=12)
    pygame.draw.rect(surface, theme.CARD_BORDER, rect, width=3, border_radius=12)
    color = theme.CARD_RED if is_red else theme.CARD_BLACK

    corner_font = theme.get_font(max(int(rect.height * 0.16), 12), bold=True)
    label_surf = corner_font.render(label, True, color)
    surface.blit(label_surf, label_surf.get_rect(topleft=(rect.left + 8, rect.top + 6)))

    symbol_font = theme.get_font(max(int(rect.height * 0.38), 16), bold=True)
    symbol_surf = symbol_font.render(symbol, True, color)
    surface.blit(symbol_surf, symbol_surf.get_rect(center=rect.center))


def draw_letter_tile(surface: pygame.Surface, rect: pygame.Rect, text: str, color) -> None:
    pygame.draw.rect(surface, theme.CARD_FACE, rect, border_radius=14)
    pygame.draw.rect(surface, color, rect, width=5, border_radius=14)
    font = theme.get_font(max(int(rect.height * 0.55), 18), bold=True)
    text_surf = font.render(text, True, theme.TEXT_DARK)
    surface.blit(text_surf, text_surf.get_rect(center=rect.center))


def draw_face_down_tile(surface: pygame.Surface, rect: pygame.Rect, color) -> None:
    pygame.draw.rect(surface, color, rect, border_radius=14)
    pygame.draw.rect(surface, theme.TEXT_DARK, rect, width=3, border_radius=14)
    font = theme.get_font(max(int(rect.height * 0.5), 18), bold=True)
    text_surf = font.render("?", True, theme.TEXT_LIGHT)
    surface.blit(text_surf, text_surf.get_rect(center=rect.center))


def draw_flip(
    surface: pygame.Surface,
    rect: pygame.Rect,
    progress: float,
    draw_back: Callable[[pygame.Surface, pygame.Rect], None],
    draw_face: Callable[[pygame.Surface, pygame.Rect], None],
) -> None:
    """A simple horizontal-squeeze card flip: `progress` 0->1 shrinks the
    card to an edge-on sliver (showing `draw_back`) then grows it back out
    (showing `draw_face`) — a cheap, readable stand-in for a real 3D flip.
    """
    progress = max(0.0, min(1.0, progress))
    scale = abs(1 - 2 * progress)
    scaled = rect.copy()
    scaled.width = max(4, int(rect.width * scale))
    scaled.centerx = rect.centerx
    if progress < 0.5:
        draw_back(surface, scaled)
    else:
        draw_face(surface, scaled)


def draw_panel(surface: pygame.Surface, rect: pygame.Rect, color=theme.PANEL) -> None:
    pygame.draw.rect(surface, color, rect, border_radius=20)
    pygame.draw.rect(surface, theme.TEXT_DARK, rect, width=3, border_radius=20)


MODAL_SIZE = (680, 280)


def modal_rect(window_size: tuple[int, int]) -> pygame.Rect:
    rect = pygame.Rect(0, 0, *MODAL_SIZE)
    rect.center = (window_size[0] // 2, window_size[1] // 2)
    return rect


def modal_button_rects(window_size: tuple[int, int]) -> tuple[pygame.Rect, pygame.Rect]:
    """Standard positions for the two end-of-game buttons, sized to
    MIN_TOUCH_TARGET and placed inside the modal panel — not floating over
    whatever board/hand state happens to still be rendered underneath.
    """
    m = modal_rect(window_size)
    y = m.top + 170
    left = pygame.Rect(m.centerx - 220, y, 200, theme.MIN_TOUCH_TARGET)
    right = pygame.Rect(m.centerx + 20, y, 200, theme.MIN_TOUCH_TARGET)
    return left, right


def draw_dim_overlay(surface: pygame.Surface, alpha: int = 190) -> None:
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((*theme.BACKGROUND, alpha))
    surface.blit(overlay, (0, 0))


def draw_game_over_modal(surface: pygame.Surface, window_size: tuple[int, int], message: str) -> None:
    """Dims whatever's still on screen and draws the end-of-game message
    inside a centered panel, so the Play Again/Menu buttons (positioned via
    `modal_button_rects`) never overlap board/hand content underneath.
    """
    draw_dim_overlay(surface)
    m = modal_rect(window_size)
    draw_panel(surface, m)
    draw_text(surface, message, (m.centerx, m.top + 70), size=28, center=True)


def draw_text(
    surface: pygame.Surface,
    text: str,
    pos: tuple[int, int],
    size: int = 28,
    color=theme.TEXT_DARK,
    bold: bool = False,
    center: bool = False,
) -> pygame.Rect:
    font = theme.get_font(size, bold=bold)
    text_surf = font.render(text, True, color)
    rect = text_surf.get_rect(center=pos) if center else text_surf.get_rect(topleft=pos)
    surface.blit(text_surf, rect)
    return rect


class Confetti:
    """A short-lived celebration burst. Call update(dt) then draw(surface)
    each frame; check done() to know when it's finished.
    """

    COLORS = [theme.PRIMARY, theme.SECONDARY, theme.ACCENT, theme.SUCCESS]

    def __init__(self, origin_rect: pygame.Rect, count: int = 90, duration: float = 2.2):
        self.duration = duration
        self.age = 0.0
        self._rng = random.Random()
        self.particles = [
            {
                "pos": [
                    self._rng.uniform(origin_rect.left, origin_rect.right),
                    self._rng.uniform(origin_rect.top, origin_rect.top + 40),
                ],
                "vel": [self._rng.uniform(-60, 60), self._rng.uniform(-260, -120)],
                "color": self._rng.choice(self.COLORS),
                "size": self._rng.randint(6, 14),
            }
            for _ in range(count)
        ]

    def update(self, dt: float) -> None:
        self.age += dt
        for p in self.particles:
            p["pos"][0] += p["vel"][0] * dt
            p["pos"][1] += p["vel"][1] * dt
            p["vel"][1] += 480 * dt  # gravity

    def draw(self, surface: pygame.Surface) -> None:
        for p in self.particles:
            pygame.draw.rect(
                surface, p["color"], (int(p["pos"][0]), int(p["pos"][1]), p["size"], p["size"])
            )

    def done(self) -> bool:
        return self.age >= self.duration
