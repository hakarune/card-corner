"""Shared pygame session for UI tests. A single init/quit cycle for the
whole test session avoids a real bug this caught: `ui.theme._FONT_CACHE`
is a process-global cache of `pygame.font.Font` objects, and reusing one
created under a since-`pygame.quit()`-ed SDL session segfaults. Module-level
init/quit cycles (one pygame session per test file) triggered exactly that;
a single session-scoped fixture sidesteps it entirely.
"""
from __future__ import annotations

import pygame
import pytest

from ui.theme import WINDOW_SIZE


@pytest.fixture(scope="session", autouse=True)
def _pygame_session():
    pygame.init()
    pygame.display.set_mode(WINDOW_SIZE)
    yield
    pygame.quit()


@pytest.fixture()
def surface():
    return pygame.display.get_surface()
