"""OPTIONAL helper: rasterizes SVG sources placed under assets/source/
into the PNGs the game loads from ui/assets/ -- see assets/design.md.

This is NOT part of any normal flow. The game, run.sh, and the .deb build
all just load the PNG/JPG art committed directly under ui/assets/; art is
authored and committed as raster now. `assets/source/` does not exist by
default -- create it and drop `<category>/<key>.svg` files in if you'd
rather keep vector sources and batch-convert them here. main.py and every
ui module load only from ui/assets/ and never import this file or
cairosvg, so an end user never needs a rasterizer.

Usage:
    python tools/build_assets.py            # (re)build anything missing or stale
    python tools/build_assets.py --force     # rebuild everything regardless of mtimes

Requires cairosvg for .svg sources: `pip install -e ".[assets]"`.
"""
from __future__ import annotations

import sys
from dataclasses import dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_DIR = REPO_ROOT / "assets" / "source"
GENERATED_DIR = REPO_ROOT / "ui" / "assets"

sys.path.insert(0, str(REPO_ROOT))

import pygame  # noqa: E402

from ui.items import ANIMAL_ICONS, RANK_ITEMS  # noqa: E402
from ui.launcher import GAME_TILES  # noqa: E402


@dataclass(frozen=True)
class AssetSpec:
    category: str  # relative path under source/ and generated/, e.g. "cards/backs"
    key: str
    size: tuple[int, int]
    treatment: str  # "whole" | "tile2x2" | "icon"


def _item_keys() -> list[str]:
    return sorted({name.lower() for name, _ in RANK_ITEMS.values()})


def _animal_keys() -> list[str]:
    return sorted({name.lower() for name, _ in ANIMAL_ICONS.values()})


def _launcher_keys() -> list[str]:
    return sorted(key for key, _label, _icon_fn in GAME_TILES)


def _card_front_keys() -> list[str]:
    """Card fronts have no live code registry (unlike items/animals/launcher
    tiles): the only card with its own real front art is the Old Maid card.
    Add a key here as more get made -- keep it in sync with assets/design.md's
    "Card fronts" table.
    """
    return ["old_maid"]


def build_manifest() -> list[AssetSpec]:
    """The manifest is derived from the live registries in ui/items.py and
    ui/launcher.py (not a hand-maintained duplicate list), so a new item
    rank or animal letter added to the code automatically gets a manifest
    slot here without this file needing a matching edit. assets/design.md
    documents the same keys for humans -- if the two ever disagree, the
    code registries below are the ones that actually matter.
    """
    manifest = [
        AssetSpec("cards/backs", "go_fish", (280, 400), "whole"),
        AssetSpec("cards/backs", "old_maid", (280, 400), "tile2x2"),
        AssetSpec("cards/backs", "memory", (500, 500), "whole"),
        AssetSpec("icons/special", "old_maid_card", (512, 512), "icon"),
    ]
    manifest += [
        AssetSpec("cards/fronts", k, (280, 400), "card_front") for k in _card_front_keys()
    ]
    manifest += [AssetSpec("icons/items", k, (512, 512), "icon") for k in _item_keys()]
    manifest += [AssetSpec("icons/animals", k, (512, 512), "icon") for k in _animal_keys()]
    manifest += [AssetSpec("icons/launcher", k, (512, 512), "icon") for k in _launcher_keys()]
    return manifest


def find_source(spec: AssetSpec) -> Path | None:
    """SVG wins if both exist -- see design.md's "SVG or PNG?" section."""
    base = SOURCE_DIR / spec.category / spec.key
    svg, png = base.with_suffix(".svg"), base.with_suffix(".png")
    if svg.exists():
        return svg
    if png.exists():
        return png
    return None


def is_stale(source: Path, output: Path) -> bool:
    return not output.exists() or source.stat().st_mtime > output.stat().st_mtime


def rasterize_svg(path: Path) -> pygame.Surface:
    """Renders at the SVG's own declared pixel size (its viewBox), so
    later crop/tile/scale steps have real detail to work with rather than
    a resolution picked blind. Falls back to a generous fixed size if the
    SVG doesn't declare explicit width/height (still correct, just not
    matched to the file's own natural resolution).
    """
    import cairosvg

    try:
        import xml.etree.ElementTree as ET

        root = ET.parse(path).getroot()
        vb = root.get("viewBox")
        if vb:
            _, _, w, h = (float(v) for v in vb.split())
            w, h = max(1, round(w)), max(1, round(h))
        else:
            w, h = 2048, 2048
    except Exception:
        w, h = 2048, 2048

    png_bytes = cairosvg.svg2png(url=str(path), output_width=w, output_height=h)
    import io

    return pygame.image.load(io.BytesIO(png_bytes)).convert_alpha()


def load_source(path: Path) -> pygame.Surface:
    if path.suffix.lower() == ".svg":
        return rasterize_svg(path)
    return pygame.image.load(str(path)).convert_alpha()


def tile_crop(master: pygame.Surface, size: tuple[int, int], n: int) -> pygame.Surface:
    """Crops the center 1/n x 1/n of `master` and tiles it n x n times to
    fill `size` -- see design.md's per-asset "how it gets treated" notes.
    """
    mw, mh = master.get_size()
    crop_w, crop_h = max(1, mw // n), max(1, mh // n)
    crop_x, crop_y = (mw - crop_w) // 2, (mh - crop_h) // 2
    crop = master.subsurface((crop_x, crop_y, crop_w, crop_h)).copy()
    tile_w, tile_h = size[0] / n, size[1] / n
    tile_scaled = pygame.transform.smoothscale(crop, (max(1, round(tile_w)), max(1, round(tile_h))))
    surf = pygame.Surface(size, pygame.SRCALPHA)
    for i in range(n):
        for j in range(n):
            surf.blit(tile_scaled, (round(i * tile_w), round(j * tile_h)))
    return surf


def contain_on_canvas(master: pygame.Surface, size: tuple[int, int]) -> pygame.Surface:
    """Trims fully-transparent margins off `master`, then scales what's left
    to fit within `size` (aspect preserved) and centres it on a transparent
    canvas of exactly `size`. Lets a card front exported from a square
    artboard (lots of empty space around the card shape) land as a tight,
    correctly-proportioned portrait image without the artist having to crop
    it by hand.
    """
    bbox = master.get_bounding_rect(min_alpha=1)
    if bbox.width and bbox.height:
        master = master.subsurface(bbox).copy()
    mw, mh = master.get_size()
    scale = min(size[0] / mw, size[1] / mh)
    inner = pygame.transform.smoothscale(master, (max(1, round(mw * scale)), max(1, round(mh * scale))))
    surf = pygame.Surface(size, pygame.SRCALPHA)
    surf.blit(inner, inner.get_rect(center=(size[0] // 2, size[1] // 2)))
    return surf


def apply_treatment(master: pygame.Surface, spec: AssetSpec) -> pygame.Surface:
    if spec.treatment == "whole":
        return pygame.transform.smoothscale(master, spec.size)
    if spec.treatment == "tile2x2":
        return tile_crop(master, spec.size, 2)
    if spec.treatment == "card_front":
        return contain_on_canvas(master, spec.size)
    if spec.treatment == "icon":
        # Source is specced as a square, transparent-background canvas
        # (design.md) -- runtime code does its own contain-fit into
        # whatever non-square area an icon ends up in, so the build step
        # just needs to land on the exact generated square size.
        return pygame.transform.smoothscale(master, spec.size)
    raise ValueError(f"unknown treatment: {spec.treatment!r}")


def build_one(spec: AssetSpec, force: bool) -> str:
    source = find_source(spec)
    output = GENERATED_DIR / spec.category / f"{spec.key}.png"
    if source is None:
        return "skip (no source yet)"
    if not force and not is_stale(source, output):
        return "up to date"

    try:
        master = load_source(source)
    except ImportError:
        return "SKIPPED -- needs cairosvg: pip install -e '.[assets]'"
    except Exception as exc:  # a bad/corrupt source file must not abort the whole run
        return f"SKIPPED -- failed to load ({exc})"

    try:
        final = apply_treatment(master, spec)
        output.parent.mkdir(parents=True, exist_ok=True)
        pygame.image.save(final, str(output))
    except Exception as exc:
        return f"SKIPPED -- failed to build ({exc})"
    return f"built -> {output.relative_to(REPO_ROOT)}"


def main() -> None:
    force = "--force" in sys.argv
    pygame.init()
    pygame.display.set_mode((1, 1))  # convert_alpha() needs a display surface

    manifest = build_manifest()
    made, skipped, missing = 0, 0, 0
    for spec in manifest:
        result = build_one(spec, force)
        key = f"{spec.category}/{spec.key}"
        print(f"{key:32} {result}")
        if result.startswith("built"):
            made += 1
        elif result.startswith("SKIPPED"):
            skipped += 1
        elif result.startswith("skip"):
            missing += 1

    print(f"\n{made} built, {skipped} skipped (errors), {missing} not made yet, "
          f"{len(manifest) - made - skipped - missing} already up to date.")
    print("Anything not made yet or skipped just falls back to the built-in "
          "procedural art -- nothing here is required for the game to run.")


if __name__ == "__main__":
    main()
