"""Loads generated art from ui/assets/ (see assets/design.md for the full
art pipeline this is the runtime half of). Strict "never raise" contract:
a missing file, a bad/corrupt PNG, or an asset that just hasn't been made
yet all return None, so every caller can fall back to the existing
procedural drawing instead of crashing -- real art is a pure visual
upgrade over the built-in placeholder, never a hard dependency.

Uses importlib.resources rather than a path built from __file__, so this
works the same way whether running from source (editable install), a
regular pip install, or the .deb's extracted site-packages layout.
"""
from __future__ import annotations

import functools
from importlib import resources

import pygame


@functools.lru_cache(maxsize=None)
def _load(relative_path: str) -> pygame.Surface | None:
    try:
        ref = resources.files("ui.assets").joinpath(relative_path)
        if not ref.is_file():
            return None
        with resources.as_file(ref) as path:
            return pygame.image.load(str(path)).convert_alpha()
    except Exception:
        # Any failure (corrupt file, no display surface yet, permissions,
        # a partially-written file mid-edit) -- fall back, don't crash.
        return None


def load_card_back(key: str) -> pygame.Surface | None:
    """The whole card-back pattern (see assets/design.md's "Card backs"
    section) for game `key` (e.g. "go_fish"), or None if not made yet.
    """
    return _load(f"cards/backs/{key}.png")


def load_icon(category: str, key: str) -> pygame.Surface | None:
    """A square icon (items/animals/launcher/special -- see design.md's
    "Icons" section) for `key` in `category`, or None if not made yet.
    """
    return _load(f"icons/{category}/{key}.png")
