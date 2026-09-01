"""Shared kid-friendly widgets: buttons, card/tile sprites, and celebration
effects. Every game screen renders through these rather than drawing its
own ad-hoc shapes, so the four games stay visually consistent (spec §6).
"""
from __future__ import annotations

import random
from typing import Callable

import pygame

from audio.manager import audio

from . import asset_loader, items, theme


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
                audio.play_sfx("button")
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


def _pattern_fish(surface: pygame.Surface, cx: float, cy: float, s: float, color) -> None:
    pygame.draw.polygon(
        surface, color, [(cx - s, cy), (cx - s * 0.15, cy - s * 0.55), (cx - s * 0.15, cy + s * 0.55)]
    )
    pygame.draw.circle(surface, color, (cx + s * 0.35, cy), s * 0.45)


def _pattern_crown(surface: pygame.Surface, cx: float, cy: float, s: float, color) -> None:
    points = [
        (cx - s, cy + s * 0.5), (cx - s, cy - s * 0.1), (cx - s * 0.5, cy + s * 0.15),
        (cx, cy - s * 0.55), (cx + s * 0.5, cy + s * 0.15), (cx + s, cy - s * 0.1),
        (cx + s, cy + s * 0.5),
    ]
    pygame.draw.polygon(surface, color, points)


def _pattern_puzzle(surface: pygame.Surface, cx: float, cy: float, s: float, color) -> None:
    pygame.draw.circle(surface, color, (cx, cy), s * 0.5, width=max(2, int(s * 0.15)))
    pygame.draw.circle(surface, color, (cx, cy), s * 0.2)


PATTERN_DRAWERS: dict[str, Callable] = {
    "fish": _pattern_fish,
    "crown": _pattern_crown,
    "puzzle": _pattern_puzzle,
}


def _fit_text(text: str, max_width: int, size: int, color) -> pygame.Surface:
    """Renders `text` at `size`, shrinking (via scale, not re-rendering) if
    it would overflow `max_width` -- keeps a themed back's game-name label
    legible even on the narrowest card sizes a screen uses.
    """
    font = theme.get_font(size, bold=True)
    surf = font.render(text, True, color)
    if surf.get_width() > max_width:
        scale = max_width / surf.get_width()
        new_size = (max_width, max(1, int(surf.get_height() * scale)))
        surf = pygame.transform.smoothscale(surf, new_size)
    return surf


def blit_icon_contain(surface: pygame.Surface, rect: pygame.Rect, icon: pygame.Surface) -> None:
    """Scales `icon` to fit within `rect` without distorting it (preserves
    aspect ratio, centered) -- icons are authored as a square (design.md)
    but get placed into all kinds of non-square areas across the app, so
    this never stretches a square source into an oval/rectangle.
    """
    iw, ih = icon.get_size()
    scale = min(rect.width / iw, rect.height / ih)
    size = (max(1, round(iw * scale)), max(1, round(ih * scale)))
    scaled = pygame.transform.smoothscale(icon, size)
    surface.blit(scaled, scaled.get_rect(center=rect.center))


def _clip_rounded(img: pygame.Surface, radius: int) -> pygame.Surface:
    mask = pygame.Surface(img.get_size(), pygame.SRCALPHA)
    pygame.draw.rect(mask, (255, 255, 255, 255), mask.get_rect(), border_radius=radius)
    result = img.convert_alpha()
    result.blit(mask, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return result


def draw_card_back(surface: pygame.Surface, rect: pygame.Rect, card_theme=None) -> None:
    """A themed card back: real art if it's been made (assets/design.md),
    otherwise a solid game color with a small repeating pattern in each
    corner -- either way, the game's name lettered across the middle, so a
    face-down card instantly tells you which game you're playing (spec §4).
    Falls back to the original generic circle-in-circle back if no theme is
    given at all (kept for callers/tests that don't care which game it's for).
    """
    if card_theme is not None:
        image = asset_loader.load_card_back(card_theme.asset_key)
        if image is not None:
            # The art is transparent in the gaps between pattern elements
            # (by design -- see assets/design.md), so a solid base fill has
            # to go down first or those gaps let whatever's underneath show
            # through: the page background, or -- worse -- an overlapping
            # previously-drawn card's own label text, in a hand of
            # face-down cards spaced close enough to overlap.
            pygame.draw.rect(surface, card_theme.back_color, rect, border_radius=12)
            scaled = pygame.transform.smoothscale(image, rect.size)
            surface.blit(_clip_rounded(scaled, 12), rect.topleft)
            pygame.draw.rect(surface, theme.CARD_BORDER, rect, width=3, border_radius=12)
            label_surf = _fit_text(
                card_theme.label, int(rect.width * 0.85), max(int(rect.height * 0.13), 11), theme.TEXT_LIGHT
            )
            surface.blit(label_surf, label_surf.get_rect(center=rect.center))
            return

    pygame.draw.rect(surface, card_theme.back_color if card_theme else theme.CARD_BACK, rect, border_radius=12)
    pygame.draw.rect(surface, theme.CARD_BORDER, rect, width=3, border_radius=12)

    if card_theme is None:
        center = rect.center
        r = min(rect.width, rect.height) // 5
        pygame.draw.circle(surface, theme.CARD_BACK_PATTERN, center, r, width=4)
        pygame.draw.circle(surface, theme.CARD_BACK_PATTERN, center, max(r - 14, 4))
        return

    pattern_color = theme.TEXT_LIGHT
    # On very narrow cards (e.g. a compact opponent-hand back) there isn't
    # room for both the corner pattern and a legible name label without
    # them colliding -- drop the pattern and let the color + label carry
    # the game identity instead.
    if rect.width >= 85:
        pattern_fn = PATTERN_DRAWERS[card_theme.pattern]
        s = min(rect.width, rect.height) * 0.11
        margin_x, margin_y = rect.width * 0.2, rect.height * 0.16
        for corner_x in (rect.left + margin_x, rect.right - margin_x):
            for corner_y in (rect.top + margin_y, rect.bottom - margin_y):
                pattern_fn(surface, corner_x, corner_y, s, pattern_color)

    label_surf = _fit_text(card_theme.label, int(rect.width * 0.85), max(int(rect.height * 0.13), 11), pattern_color)
    surface.blit(label_surf, label_surf.get_rect(center=rect.center))


def draw_old_maid_illustration(surface: pygame.Surface, rect: pygame.Rect) -> None:
    """A distinct, whimsical illustrated face for the one card the whole
    game revolves around -- a friendly, silly granny character (round
    glasses, a bonnet, rosy cheeks, a big smile), not a reused card back or
    a generic face, so it instantly reads as 'the Old Maid' (spec §6).
    """
    card_theme = theme.CARD_THEMES["old_maid"]
    pygame.draw.rect(surface, card_theme.front_tint, rect, border_radius=12)
    pygame.draw.rect(surface, card_theme.back_color, rect, width=3, border_radius=12)

    front = asset_loader.load_card_front("old_maid")
    if front is not None:
        # A whole pre-rendered card face (assets/design.md's "Card fronts"):
        # tint base stays underneath in case the art has transparent margins,
        # the name is still lettered by code on top (never baked into the art).
        scaled = pygame.transform.smoothscale(front, rect.size)
        surface.blit(_clip_rounded(scaled, 12), rect.topleft)
        pygame.draw.rect(surface, card_theme.back_color, rect, width=3, border_radius=12)
        label_surf = _fit_text(
            "OLD MAID", int(rect.width * 0.9), max(int(rect.height * 0.1), 10), card_theme.back_color
        )
        surface.blit(label_surf, label_surf.get_rect(midbottom=(rect.centerx, rect.bottom - 6)))
        return

    icon = asset_loader.load_icon("special", "old_maid_card")
    if icon is not None:
        icon_area = rect.inflate(-int(rect.width * 0.15), -int(rect.height * 0.15))
        icon_area.centery = rect.centery - rect.height * 0.05  # leave room for the label below
        blit_icon_contain(surface, icon_area, icon)
        label_surf = _fit_text(
            "OLD MAID", int(rect.width * 0.9), max(int(rect.height * 0.1), 10), card_theme.back_color
        )
        surface.blit(label_surf, label_surf.get_rect(midbottom=(rect.centerx, rect.bottom - 6)))
        return

    cx, cy = rect.centerx, rect.centery + rect.height * 0.06
    head_r = rect.width * 0.28
    skin = (247, 214, 180)

    # Bonnet: a triangle-topped headscarf peeking out behind the head.
    bonnet_pts = [
        (cx - head_r * 1.3, cy - head_r * 0.2),
        (cx, cy - head_r * 1.9),
        (cx + head_r * 1.3, cy - head_r * 0.2),
    ]
    pygame.draw.polygon(surface, card_theme.back_color, bonnet_pts)

    pygame.draw.circle(surface, skin, (cx, cy), head_r)

    # Round glasses.
    eye_dx, eye_y = head_r * 0.42, cy - head_r * 0.05
    glasses_r = head_r * 0.3
    for dx in (-eye_dx, eye_dx):
        pygame.draw.circle(surface, theme.TEXT_DARK, (cx + dx, eye_y), glasses_r, width=3)
        pygame.draw.circle(surface, theme.TEXT_DARK, (cx + dx, eye_y), glasses_r * 0.35)
    pygame.draw.line(
        surface, theme.TEXT_DARK, (cx - eye_dx + glasses_r, eye_y), (cx + eye_dx - glasses_r, eye_y), 2
    )

    # Rosy cheeks and a big smile.
    cheek_r = head_r * 0.18
    for dx in (-head_r * 0.55, head_r * 0.55):
        pygame.draw.circle(surface, (240, 150, 150), (int(cx + dx), int(cy + head_r * 0.35)), int(cheek_r))
    smile_rect = pygame.Rect(0, 0, head_r * 0.9, head_r * 0.7)
    smile_rect.center = (cx, cy + head_r * 0.3)
    pygame.draw.arc(surface, theme.TEXT_DARK, smile_rect, 3.53, 5.9, 3)

    label_surf = _fit_text("OLD MAID", int(rect.width * 0.9), max(int(rect.height * 0.1), 10), card_theme.back_color)
    surface.blit(label_surf, label_surf.get_rect(midbottom=(rect.centerx, rect.bottom - 6)))


def draw_card_face(
    surface: pygame.Surface, rect: pygame.Rect, label: str, symbol: str, is_red: bool, card_theme=None
) -> None:
    """A card front. Always carries a themed (non-white) background tint
    and a border matching its game's color when a theme is given, per
    spec §4's 'no plain white/blank card fronts' -- falls back to a plain
    white front for callers/tests that don't pass one.
    """
    bg = card_theme.front_tint if card_theme else theme.CARD_FACE
    border = card_theme.back_color if card_theme else theme.CARD_BORDER
    pygame.draw.rect(surface, bg, rect, border_radius=12)
    pygame.draw.rect(surface, border, rect, width=3, border_radius=12)
    color = theme.CARD_RED if is_red else theme.CARD_BLACK

    corner_font = theme.get_font(max(int(rect.height * 0.16), 12), bold=True)
    label_surf = corner_font.render(label, True, color)
    surface.blit(label_surf, label_surf.get_rect(topleft=(rect.left + 8, rect.top + 6)))

    symbol_font = theme.get_font(max(int(rect.height * 0.38), 16), bold=True)
    symbol_surf = symbol_font.render(symbol, True, color)
    surface.blit(symbol_surf, symbol_surf.get_rect(center=rect.center))


def draw_item_card_face(surface: pygame.Surface, rect: pygame.Rect, rank, card_theme) -> None:
    """A kid-themed card front: a simple everyday-item icon (sun, star,
    umbrella, ...) and its name, replacing the standard suit symbol/rank
    label (spec §5/§7 -- standard playing cards aren't engaging for this
    age group). `rank` picks the item via ui.items.RANK_ITEMS; the
    underlying Suit/Rank identity and matching logic are untouched, this
    only changes what's drawn. Every copy of a rank (all 4 suits) renders
    identically -- Go Fish/Memory both match by rank alone, so there's
    nothing for a differing suit to usefully signal here.
    """
    pygame.draw.rect(surface, card_theme.front_tint, rect, border_radius=12)
    pygame.draw.rect(surface, card_theme.back_color, rect, width=3, border_radius=12)

    name, icon_fn = items.RANK_ITEMS[rank]
    icon_area = rect.inflate(-int(rect.width * 0.3), -int(rect.height * 0.45))
    icon_area.centery = rect.centery - rect.height * 0.08
    icon_fn(surface, icon_area, card_theme.back_color)

    label_surf = _fit_text(name, int(rect.width * 0.85), max(int(rect.height * 0.13), 11), theme.TEXT_DARK)
    surface.blit(label_surf, label_surf.get_rect(midbottom=(rect.centerx, rect.bottom - 8)))


def draw_letter_tile(surface: pygame.Surface, rect: pygame.Rect, text: str, color) -> None:
    # A tinted (not plain white) background, per spec §4's "no plain
    # white/blank card fronts anywhere" -- even for tiles that are never
    # face-down.
    pygame.draw.rect(surface, theme._tint(color), rect, border_radius=14)
    pygame.draw.rect(surface, color, rect, width=5, border_radius=14)
    font = theme.get_font(max(int(rect.height * 0.55), 18), bold=True)
    text_surf = font.render(text, True, theme.TEXT_DARK)
    surface.blit(text_surf, text_surf.get_rect(center=rect.center))


def draw_animal_tile(surface: pygame.Surface, rect: pygame.Rect, letter: str, color) -> None:
    """Letter Match's "animals" mode picture tile (spec §8): same tinted
    tile chrome as draw_letter_tile, an animal icon in place of the letter
    text. `letter` looks the icon up via ui.items.ANIMAL_ICONS.
    """
    pygame.draw.rect(surface, theme._tint(color), rect, border_radius=14)
    pygame.draw.rect(surface, color, rect, width=5, border_radius=14)
    _, icon_fn = items.ANIMAL_ICONS[letter]
    icon_fn(surface, rect, theme.TEXT_DARK)


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
