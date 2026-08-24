"""Base class for a full-window screen (launcher, difficulty picker, or a
game). main.py's loop drives every screen through this same interface.
"""
from __future__ import annotations

from typing import Optional

import pygame


class Screen:
    def __init__(self, size: tuple[int, int]):
        self.size = size
        self._next: Optional["Screen"] = None

    def handle_event(self, event: pygame.event.Event) -> None:
        pass

    def update(self, dt: float) -> None:
        pass

    def draw(self, surface: pygame.Surface) -> None:
        pass

    def go_to(self, screen: "Screen") -> None:
        self._next = screen

    def next_screen(self) -> Optional["Screen"]:
        n = self._next
        self._next = None
        return n
