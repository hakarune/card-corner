"""Card Corner: a kid-friendly card game suite (Go Fish, Old Maid, Memory,
Letter Match) in one launcher. Entry point.

Renders everything at a fixed LOGICAL_SIZE, then scales that (preserving
aspect ratio, letterboxed) onto the real OS window each frame. This means
every screen's existing layout code needs no changes to support fullscreen
or an arbitrarily-resized window -- only main.py's loop knows about the
real window size, and it just scales the finished frame + inverse-transforms
mouse coordinates before handing events to the active screen.
"""
from __future__ import annotations

import sys

import pygame

from audio.manager import audio
from games.go_fish.screen import GoFishScreen
from games.letter_match.screen import LetterMatchScreen
from games.memory.screen import MemoryScreen
from games.old_maid.screen import OldMaidScreen
from ui import settings, theme
from ui.launcher import DifficultySelectScreen, LauncherScreen
from ui.screen import Screen

GAME_SCREENS = {
    "go_fish": (GoFishScreen, "Go Fish"),
    "old_maid": (OldMaidScreen, "Old Maid"),
    "memory": (MemoryScreen, "Memory"),
}

LOGICAL_SIZE = theme.WINDOW_SIZE  # fixed internal render resolution
POS_EVENTS = {pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN, pygame.MOUSEBUTTONUP}


def make_launcher(size: tuple[int, int]) -> Screen:
    def on_select(key: str) -> Screen:
        if key == "letter_match":
            return LetterMatchScreen(size, lambda: make_launcher(size))
        screen_cls, label = GAME_SCREENS[key]
        color = theme.GAME_COLORS[key]

        def on_pick(difficulty):
            return screen_cls(size, difficulty, lambda: make_launcher(size))

        solo_pick = None
        if key == "memory":
            def solo_pick():
                return screen_cls(size, None, lambda: make_launcher(size))

        return DifficultySelectScreen(
            size, label, color, on_pick, lambda: make_launcher(size), solo_pick=solo_pick
        )

    return LauncherScreen(size, on_select)


def create_window(fullscreen: bool, windowed_size: tuple[int, int]) -> pygame.Surface:
    if fullscreen:
        return pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
    return pygame.display.set_mode(windowed_size, pygame.RESIZABLE)


def compute_scale(window_size: tuple[int, int], logical_size: tuple[int, int]):
    wx, wy = window_size
    lx, ly = logical_size
    scale = max(0.01, min(wx / lx, wy / ly))
    render_w, render_h = int(lx * scale), int(ly * scale)
    offset = ((wx - render_w) // 2, (wy - render_h) // 2)
    return scale, offset, (render_w, render_h)


def transform_event(event: pygame.event.Event, scale: float, offset: tuple[int, int]) -> pygame.event.Event:
    if event.type in POS_EVENTS:
        lx = (event.pos[0] - offset[0]) / scale
        ly = (event.pos[1] - offset[1]) / scale
        data = event.dict.copy()
        data["pos"] = (lx, ly)
        return pygame.event.Event(event.type, data)
    return event


def main() -> None:
    pygame.init()
    pygame.display.set_caption("Card Corner")

    windowed_size = tuple(settings.get("windowed_size"))
    window = create_window(settings.get("fullscreen"), windowed_size)
    last_fullscreen = settings.get("fullscreen")

    logical_surface = pygame.Surface(LOGICAL_SIZE)
    clock = pygame.time.Clock()

    current: Screen = make_launcher(LOGICAL_SIZE)
    audio.start_music()

    running = True
    while running:
        dt = clock.tick(60) / 1000.0
        audio.refresh_music_volume()

        # Fullscreen/windowed can change from inside a screen (main menu
        # icon, in-game pause overlay) -- the source of truth is the
        # settings module, so just watch for it to change each frame.
        if settings.get("fullscreen") != last_fullscreen:
            last_fullscreen = settings.get("fullscreen")
            window = create_window(last_fullscreen, tuple(settings.get("windowed_size")))

        scale, offset, render_size = compute_scale(window.get_size(), LOGICAL_SIZE)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.VIDEORESIZE:
                if not settings.get("fullscreen"):
                    settings.set("windowed_size", [event.w, event.h])
            else:
                current.handle_event(transform_event(event, scale, offset))

        current.update(dt)

        logical_surface.fill(theme.BACKGROUND)
        current.draw(logical_surface)

        window.fill((0, 0, 0))
        scaled = pygame.transform.smoothscale(logical_surface, render_size)
        window.blit(scaled, offset)
        pygame.display.flip()

        if current.quit_requested:
            running = False

        nxt = current.next_screen()
        if nxt is not None:
            current = nxt

    audio.stop_music()
    pygame.quit()
    sys.exit(0)


if __name__ == "__main__":
    main()
