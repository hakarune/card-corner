# Asset attributions

**No external art, font, or audio assets are used anywhere in this project.**

All visuals — card faces and backs, Memory tiles, Letter Match tiles, menu
icons, buttons, and the confetti celebration effect — are drawn
procedurally at runtime with Pygame's `draw` primitives (rectangles,
circles, polygons) and its bundled system-font text rendering. There are no
static image files to generate or attribute, so there's no separate
`assets/generated/` output step: the "generator" is simply the shared
drawing code itself, executed live every frame.

- `ui/widgets.py` — shared card/tile/button/confetti drawing functions used
  by every game screen.
- `ui/launcher.py` — the four per-game menu icons (fish, crown, card pair,
  "Aa"), drawn the same way.
- `ui/theme.py` — the shared color palette and font settings referenced by
  all of the above.

Text is rendered with `pygame.font.SysFont`, which uses fonts already
installed on the host system — no font files are bundled with the
repository.

If an external CC0/public-domain asset pack is ever added in the future,
log its source and license here, one entry per asset (or asset pack).
