# Asset attributions

**No external (third-party) art, font, or audio assets are used anywhere
in this project.** Everything below is either drawn procedurally by code
or original artwork made by this project's own contributors — nothing
needs a license entry here, since there's no external source to credit.

## Original static art

Some card backs are now real static PNGs (see `assets/design.md` for the
full pipeline: source files under `assets/source/`, generated output
under `ui/assets/`, converted by `tools/build_assets.py`) rather than
being drawn procedurally. Every one of these is original artwork made
directly for this project — none are sourced from a stock/third-party
library. As more are added, they belong here as originals too, not as an
attribution entry, unless one is ever sourced from outside the project
(see the note at the bottom).

## Procedural art

Everything not covered by a real asset yet (see `assets/design.md` for
what's outstanding) is drawn procedurally at runtime with Pygame's `draw`
primitives (rectangles, circles, polygons) and its bundled system-font
text rendering, as a working placeholder/fallback for whatever real art
doesn't exist yet:

- `ui/widgets.py` — shared card/tile/button/confetti drawing functions used
  by every game screen.
- `ui/items.py` — the procedural item and animal icon set (Go Fish/Memory's
  card faces, Letter Match's Animals mode).
- `ui/launcher.py` — the four per-game menu icons (fish, crown, card pair,
  "Aa"), drawn the same way.
- `ui/theme.py` — the shared color palette and font settings referenced by
  all of the above.

Text is rendered with `pygame.font.SysFont`, which uses fonts already
installed on the host system — no font files are bundled with the
repository.

If an external CC0/public-domain asset pack, font, or audio sample is
ever added in the future, log its source and license here, one entry per
asset (or asset pack) — distinct from the original art noted above.
