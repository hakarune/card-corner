"""Generates the app icon as a static PNG for desktop integration (the
hicolor icon theme needs a real image file, unlike every other visual in
this app which is drawn live). Reuses the existing card-back drawing code
from ui/widgets.py for visual consistency rather than hand-authoring a
separate icon asset -- run at package-build time, not at app runtime.

    python debpkg/generate_icon.py path/to/output.png [size]
"""
from __future__ import annotations

import sys
from pathlib import Path

import pygame

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ui import theme
from ui.widgets import draw_card_back


def render_icon(size: int) -> pygame.Surface:
    surface = pygame.Surface((size, size), pygame.SRCALPHA)
    # A standard card aspect ratio (~0.7), padded so the rounded corners and
    # border read clearly instead of bleeding off the square canvas.
    rect = pygame.Rect(0, 0, int(size * 0.62), int(size * 0.88))
    rect.center = (size // 2, size // 2)
    draw_card_back(surface, rect)
    return surface


def main() -> None:
    if len(sys.argv) < 2:
        print(__doc__)
        raise SystemExit(1)
    out_path = Path(sys.argv[1])
    size = int(sys.argv[2]) if len(sys.argv) > 2 else 256

    pygame.init()
    pygame.display.set_mode((1, 1))  # some SDL backends need a display surface to exist
    icon = render_icon(size)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    pygame.image.save(icon, str(out_path))
    pygame.quit()
    print(f"wrote {out_path} ({size}x{size})")


if __name__ == "__main__":
    main()
