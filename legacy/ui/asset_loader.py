"""Loads real art from ui/assets/ (see assets/design.md for the art
workflow this is the runtime half of). Strict "never raise" contract: a
missing file, a bad/corrupt image, or an asset that just hasn't been made
yet all return None, so every caller can fall back to the existing
procedural drawing instead of crashing -- real art is a pure visual
upgrade over the built-in placeholder, never a hard dependency.

Art is committed straight into ui/assets/ as PNG or JPG -- whichever the
artist exported -- and loaded directly here; there is no build/convert
step. Uses importlib.resources rather than a path built from __file__, so
this works the same way whether running from source, a regular pip
install, or the .deb's extracted layout.
"""
from __future__ import annotations

import functools
from importlib import resources

import pygame

# Tried in order for a given key; first file that exists wins. PNG first
# (transparency, the common case for icons/fronts), then JPG for the
# painterly/photographic edge-to-edge pieces where alpha isn't needed.
_EXTENSIONS = (".png", ".jpg", ".jpeg")


@functools.lru_cache(maxsize=None)
def _load(relative_path: str) -> pygame.Surface | None:
    """`relative_path` is the key path *without* an extension, e.g.
    "cards/backs/go_fish" -- this tries each of `_EXTENSIONS` in turn.
    """
    try:
        base = resources.files("ui.assets")
        for ext in _EXTENSIONS:
            ref = base.joinpath(relative_path + ext)
            if not ref.is_file():
                continue
            with resources.as_file(ref) as path:
                return pygame.image.load(str(path)).convert_alpha()
        return None
    except Exception:
        # Any failure (corrupt file, no display surface yet, permissions,
        # a partially-written file mid-edit) -- fall back, don't crash.
        return None


def load_card_back(key: str) -> pygame.Surface | None:
    """The whole card-back pattern (see assets/design.md's "Card backs"
    section) for game `key` (e.g. "go_fish"), or None if not made yet.
    """
    return _load(f"cards/backs/{key}")


def load_card_front(key: str) -> pygame.Surface | None:
    """The whole pre-rendered card *face* (see assets/design.md's "Card
    fronts" section) for game `key` (e.g. "old_maid"), or None if not made
    yet. Unlike an icon, this is the entire card face edge-to-edge, drawn
    in place of the procedural tint + illustration.
    """
    return _load(f"cards/fronts/{key}")


def load_icon(category: str, key: str) -> pygame.Surface | None:
    """A square icon (items/animals/launcher/special -- see design.md's
    "Icons" section) for `key` in `category`, or None if not made yet.
    """
    return _load(f"icons/{category}/{key}")
