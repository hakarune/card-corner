"""Card Corner: a kid-friendly card game suite (Go Fish, Old Maid, Memory,
Letter Match) in one launcher. Entry point.
"""
from __future__ import annotations

import sys

import pygame

from games.go_fish.screen import GoFishScreen
from games.letter_match.screen import LetterMatchScreen
from games.memory.screen import MemoryScreen
from games.old_maid.screen import OldMaidScreen
from ui import theme
from ui.launcher import DifficultySelectScreen, LauncherScreen
from ui.screen import Screen

GAME_SCREENS = {
    "go_fish": (GoFishScreen, "Go Fish"),
    "old_maid": (OldMaidScreen, "Old Maid"),
    "memory": (MemoryScreen, "Memory"),
}


def make_launcher(size: tuple[int, int]) -> Screen:
    def on_select(key: str) -> Screen:
        if key == "letter_match":
            return LetterMatchScreen(size, lambda: make_launcher(size))
        screen_cls, label = GAME_SCREENS[key]
        color = theme.GAME_COLORS[key]

        def on_pick(difficulty):
            return screen_cls(size, difficulty, lambda: make_launcher(size))

        return DifficultySelectScreen(
            size, label, color, on_pick, lambda: make_launcher(size)
        )

    return LauncherScreen(size, on_select)


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Card Corner")
    surface = pygame.display.set_mode(theme.WINDOW_SIZE)
    clock = pygame.time.Clock()

    current: Screen = make_launcher(theme.WINDOW_SIZE)

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            else:
                current.handle_event(event)

        current.update(dt)
        current.draw(surface)
        pygame.display.flip()

        nxt = current.next_screen()
        if nxt is not None:
            current = nxt

    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
