"""Kid-themed item identities for each card rank, replacing standard suit
symbols on card fronts in Go Fish and Memory (spec §5/§7) -- simple,
everyday things a 5-8 year old recognizes at a glance, drawn procedurally
with the same primitives as everything else in ui/widgets.py. The
underlying game logic is untouched: cards are still Suit/Rank internally
(so Go Fish's ask-for-a-rank / Memory's match-by-rank rules don't change at
all), this only swaps what's *shown*.
"""
from __future__ import annotations

import math
from typing import Callable

import pygame

from core.card import Rank


def _sun(surface, rect, color) -> None:
    cx, cy = rect.center
    r = min(rect.width, rect.height) * 0.18
    pygame.draw.circle(surface, color, (cx, cy), r)
    for i in range(8):
        angle = i * math.pi / 4
        x1, y1 = cx + math.cos(angle) * r * 1.4, cy + math.sin(angle) * r * 1.4
        x2, y2 = cx + math.cos(angle) * r * 2.0, cy + math.sin(angle) * r * 2.0
        pygame.draw.line(surface, color, (x1, y1), (x2, y2), 3)


def _moon(surface, rect, color) -> None:
    # A simple crescent: draw the full circle, then a slightly-offset
    # lighter circle on top -- reads as a moon without needing to know or
    # sample the card's own background color to "cut out" a bite.
    cx, cy = rect.center
    r = min(rect.width, rect.height) * 0.22
    pygame.draw.circle(surface, color, (cx, cy), r)
    lighter = tuple(min(255, c + 60) for c in color)
    pygame.draw.circle(surface, lighter, (int(cx + r * 0.55), cy), r * 0.8)


def _star(surface, rect, color) -> None:
    cx, cy = rect.center
    r = min(rect.width, rect.height) * 0.22
    points = []
    for i in range(10):
        angle = i * math.pi / 5 - math.pi / 2
        radius = r if i % 2 == 0 else r * 0.42
        points.append((cx + math.cos(angle) * radius, cy + math.sin(angle) * radius))
    pygame.draw.polygon(surface, color, points)


def _heart(surface, rect, color) -> None:
    cx, cy = rect.center
    s = min(rect.width, rect.height) * 0.16
    pygame.draw.circle(surface, color, (int(cx - s * 0.5), int(cy - s * 0.2)), s * 0.6)
    pygame.draw.circle(surface, color, (int(cx + s * 0.5), int(cy - s * 0.2)), s * 0.6)
    pygame.draw.polygon(
        surface, color,
        [(cx - s, cy - s * 0.1), (cx + s, cy - s * 0.1), (cx, cy + s * 1.2)],
    )


def _flower(surface, rect, color) -> None:
    cx, cy = rect.center
    r = min(rect.width, rect.height) * 0.12
    for i in range(5):
        angle = i * 2 * math.pi / 5
        px, py = cx + math.cos(angle) * r * 1.6, cy + math.sin(angle) * r * 1.6
        pygame.draw.circle(surface, color, (int(px), int(py)), r)
    pygame.draw.circle(surface, color, (cx, cy), r * 0.9)


def _fish_item(surface, rect, color) -> None:
    cx, cy = rect.center
    w = min(rect.width, rect.height) * 0.3
    pygame.draw.ellipse(surface, color, pygame.Rect(0, 0, w * 1.4, w * 0.8).move(cx - w * 0.5, cy - w * 0.4))
    pygame.draw.polygon(surface, color, [(cx - w * 0.5, cy), (cx - w * 1.0, cy - w * 0.4), (cx - w * 1.0, cy + w * 0.4)])


def _bird(surface, rect, color) -> None:
    # A sitting-bird silhouette: separate head + body + beak + wing, rather
    # than the original twin-spike shape which visual QA found read more
    # like a comet/spinning-top than a bird at real tile size.
    cx, cy = rect.center
    s = min(rect.width, rect.height) * 0.2
    body = pygame.Rect(0, 0, s * 1.6, s * 1.3)
    body.center = (cx, int(cy + s * 0.15))
    pygame.draw.ellipse(surface, color, body)
    head_c = (int(cx - s * 0.55), int(cy - s * 0.55))
    pygame.draw.circle(surface, color, head_c, s * 0.55)
    pygame.draw.polygon(
        surface, color,
        [
            (head_c[0] - s * 0.55, head_c[1]),
            (head_c[0] - s * 0.95, head_c[1] - s * 0.12),
            (head_c[0] - s * 0.95, head_c[1] + s * 0.12),
        ],
    )
    lighter = tuple(min(255, c + 60) for c in color)
    wing = pygame.Rect(0, 0, s * 0.8, s * 0.6)
    wing.center = (int(cx + s * 0.15), int(cy + s * 0.1))
    pygame.draw.ellipse(surface, lighter, wing)


def _tree(surface, rect, color) -> None:
    cx, cy = rect.center
    s = min(rect.width, rect.height) * 0.18
    pygame.draw.rect(surface, color, pygame.Rect(cx - s * 0.15, cy, s * 0.3, s * 1.1))
    pygame.draw.circle(surface, color, (cx, int(cy - s * 0.3)), s * 0.9)


def _house(surface, rect, color) -> None:
    cx, cy = rect.center
    s = min(rect.width, rect.height) * 0.17
    body = pygame.Rect(0, 0, s * 1.6, s * 1.1)
    body.center = (cx, cy + s * 0.4)
    pygame.draw.rect(surface, color, body)
    pygame.draw.polygon(surface, color, [(cx - s * 1.0, cy - s * 0.1), (cx, cy - s * 1.3), (cx + s * 1.0, cy - s * 0.1)])


def _umbrella(surface, rect, color) -> None:
    cx, cy = rect.center
    s = min(rect.width, rect.height) * 0.2
    pygame.draw.arc(surface, color, pygame.Rect(cx - s, cy - s, s * 2, s * 2), 0, math.pi, max(3, int(s * 0.3)))
    pygame.draw.line(surface, color, (cx, cy), (cx, cy + s * 1.3), 3)


def _apple(surface, rect, color) -> None:
    cx, cy = rect.center
    r = min(rect.width, rect.height) * 0.2
    pygame.draw.circle(surface, color, (int(cx - r * 0.5), cy), r)
    pygame.draw.circle(surface, color, (int(cx + r * 0.5), cy), r)
    pygame.draw.line(surface, color, (cx, cy - r), (cx, cy - r * 1.7), 3)


def _ball(surface, rect, color) -> None:
    cx, cy = rect.center
    r = min(rect.width, rect.height) * 0.22
    pygame.draw.circle(surface, color, (cx, cy), r, width=max(3, int(r * 0.25)))
    pygame.draw.line(surface, color, (cx - r, cy), (cx + r, cy), 2)
    pygame.draw.line(surface, color, (cx, cy - r), (cx, cy + r), 2)


def _boat(surface, rect, color) -> None:
    cx, cy = rect.center
    s = min(rect.width, rect.height) * 0.2
    pygame.draw.polygon(surface, color, [(cx - s * 1.3, cy), (cx + s * 1.3, cy), (cx + s * 0.8, cy + s * 0.7), (cx - s * 0.8, cy + s * 0.7)])
    pygame.draw.polygon(surface, color, [(cx, cy - s * 1.4), (cx, cy), (cx + s * 0.9, cy)])


def _cat(surface, rect, color) -> None:
    cx, cy = rect.center
    r = min(rect.width, rect.height) * 0.2
    pygame.draw.circle(surface, color, (cx, cy), r)
    pygame.draw.polygon(
        surface, color,
        [(cx - r * 0.8, cy - r * 0.5), (cx - r * 0.2, cy - r * 0.5), (cx - r * 0.6, cy - r * 1.3)],
    )
    pygame.draw.polygon(
        surface, color,
        [(cx + r * 0.8, cy - r * 0.5), (cx + r * 0.2, cy - r * 0.5), (cx + r * 0.6, cy - r * 1.3)],
    )


def _dog(surface, rect, color) -> None:
    cx, cy = rect.center
    r = min(rect.width, rect.height) * 0.18
    pygame.draw.circle(surface, color, (cx, int(cy - r * 0.2)), r)
    pygame.draw.ellipse(surface, color, pygame.Rect(0, 0, r * 0.6, r * 1.3).move(cx - r * 1.3, cy - r * 0.6))
    pygame.draw.ellipse(surface, color, pygame.Rect(0, 0, r * 0.6, r * 1.3).move(cx + r * 0.7, cy - r * 0.6))
    pygame.draw.ellipse(surface, color, pygame.Rect(0, 0, r * 0.9, r * 0.6).move(cx - r * 0.45, cy + r * 0.4))


def _lion(surface, rect, color) -> None:
    # A plain ring-on-ring (mane, then face) read as a target/eye rather
    # than a lion in visual QA -- added mane tufts + face ears so the
    # "furry ring" actually registers as a mane.
    cx, cy = rect.center
    r = min(rect.width, rect.height) * 0.22
    lighter = tuple(min(255, c + 50) for c in color)
    pygame.draw.circle(surface, lighter, (cx, cy), r * 1.35)  # mane
    for dx in (-1, 1):
        pygame.draw.circle(surface, lighter, (int(cx + dx * r * 1.1), int(cy - r * 0.9)), r * 0.5)
    pygame.draw.circle(surface, color, (cx, cy), r * 0.85)  # face
    for dx in (-1, 1):
        pygame.draw.circle(surface, color, (int(cx + dx * r * 0.6), int(cy - r * 0.7)), r * 0.25)


def _owl(surface, rect, color) -> None:
    cx, cy = rect.center
    r = min(rect.width, rect.height) * 0.22
    pygame.draw.circle(surface, color, (cx, cy), r)
    lighter = tuple(min(255, c + 60) for c in color)
    eye_r = r * 0.35
    pygame.draw.circle(surface, lighter, (int(cx - r * 0.4), int(cy - r * 0.1)), eye_r)
    pygame.draw.circle(surface, lighter, (int(cx + r * 0.4), int(cy - r * 0.1)), eye_r)
    pygame.draw.polygon(
        surface, color,
        [(cx - r * 0.15, cy + r * 0.15), (cx + r * 0.15, cy + r * 0.15), (cx, cy + r * 0.45)],
    )


def _pig(surface, rect, color) -> None:
    # Round ears (not Cat's pointy triangles) and a big, high-contrast
    # snout with nostrils -- visual QA found the original version (pointy
    # ears + a small low-contrast snout dot) nearly indistinguishable from
    # Cat at real tile size.
    cx, cy = rect.center
    r = min(rect.width, rect.height) * 0.2
    pygame.draw.circle(surface, color, (cx, cy), r)
    pygame.draw.circle(surface, color, (int(cx - r * 0.75), int(cy - r * 0.75)), r * 0.35)
    pygame.draw.circle(surface, color, (int(cx + r * 0.75), int(cy - r * 0.75)), r * 0.35)
    lighter = tuple(min(255, c + 90) for c in color)
    snout = pygame.Rect(0, 0, r * 0.9, r * 0.6)
    snout.center = (cx, int(cy + r * 0.35))
    pygame.draw.ellipse(surface, lighter, snout)
    pygame.draw.circle(surface, color, (int(cx - r * 0.18), int(cy + r * 0.35)), r * 0.07)
    pygame.draw.circle(surface, color, (int(cx + r * 0.18), int(cy + r * 0.35)), r * 0.07)


# Letter Match's "animals" mode (spec §8): an animal picture matched to its
# starting letter. Keys must exactly match games.letter_match.game's
# ANIMAL_MODE_LETTERS (cross-checked by tests/unit/test_letter_match.py) --
# the engine picks which letters are eligible without depending on pygame,
# this supplies the actual drawings.
ANIMAL_ICONS: dict[str, tuple[str, Callable]] = {
    "B": ("Bird", _bird),
    "C": ("Cat", _cat),
    "D": ("Dog", _dog),
    "F": ("Fish", _fish_item),
    "L": ("Lion", _lion),
    "O": ("Owl", _owl),
    "P": ("Pig", _pig),
}


RANK_ITEMS: dict[Rank, tuple[str, Callable]] = {
    Rank.ACE: ("Sun", _sun),
    Rank.TWO: ("Moon", _moon),
    Rank.THREE: ("Star", _star),
    Rank.FOUR: ("Heart", _heart),
    Rank.FIVE: ("Flower", _flower),
    Rank.SIX: ("Fish", _fish_item),
    Rank.SEVEN: ("Bird", _bird),
    Rank.EIGHT: ("Tree", _tree),
    Rank.NINE: ("House", _house),
    Rank.TEN: ("Umbrella", _umbrella),
    Rank.JACK: ("Apple", _apple),
    Rank.QUEEN: ("Ball", _ball),
    Rank.KING: ("Boat", _boat),
}


def item_name(rank: Rank) -> str:
    return RANK_ITEMS[rank][0]


_IRREGULAR_PLURALS = {"Fish": "Fish"}


def item_name_plural(rank: Rank) -> str:
    """The plural form of item_name(rank), e.g. for "wants your Birds!"
    prompts. Every item name pluralizes with a plain "s" except "Fish",
    which is already plural (an Auditor #1 finding: naive `f"{name}s"`
    produced "Fishs").
    """
    name = item_name(rank)
    return _IRREGULAR_PLURALS.get(name, name + "s")
