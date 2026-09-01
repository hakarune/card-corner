# Card Corner — art asset guide

Reference for making real art for the game: exact sizes, file naming, and
where each file goes. It's written so **anyone** — you on desktop, you on
your phone, or someone else — can drop in a correctly-named file and have
it show up, with no code changes needed for anything already listed below.

## The short version

1. Make your art at the size given in the tables further down. Export it
   as **PNG** (anything that needs transparency — every icon, card
   fronts, UI glyphs), **JPG** (edge-to-edge, fully opaque pieces like
   card-back patterns), or **SVG** (Godot rasterizes SVG on import).
2. Save it straight into **`godot/assets/<category>/<key>.<ext>`**, using
   the exact `key` from the tables — lowercase, underscores, no spaces.
   That folder **is** what the game loads (`res://assets/...`). There is
   no build/convert/copy step.
3. Open the project in Godot (or let CI import it) and look. If a file is
   missing or hasn't been made yet, the game silently falls back to a
   built-in drawn version for that one piece — nothing crashes.

That's it. Commit the file under `godot/assets/` (plus its generated
`.import` sidecar) and you're done.

## Where things live — one folder, no copy script

There is exactly **one** place for art the game uses: **`godot/assets/`**.
Godot's exporter bundles that whole tree into *every* build automatically
— the Linux binary, the Windows `.exe`, the `.deb`, and the Web build's
`index.pck`. There is no separate "web/canvas" image folder to populate;
the web export packs `godot/assets/` into `public/index.pck` and GitHub
Pages just serves that. Nothing to copy anywhere.

```
godot/assets/           <- THE ART THE GAME LOADS + SHIPS. Commit files here, by category/key.
  cards/backs/          go_fish / old_maid / memory  (.png or .jpg)
  cards/fronts/         old_maid                     (.png)
  icons/launcher/       go_fish / old_maid / memory / letter_match  (.png)
  icons/items/          the 13 Go Fish / Memory item icons  (.png, not made yet)
  icons/animals/        the 7 Letter Match animals          (.png, not made yet)
  icons/special/        old_maid_card                        (.png, not made yet)
  icons/ui/             mute / fullscreen menu-toggle glyphs (.png, optional override)
  audio/                *.wav  (baked from audio/synth.gd by tools/bake_audio.gd)

assets/                 <- REPO ROOT. Source-of-truth for EDITABLE ORIGINALS only.
  Designing/            your .svg / .afdesign / layered exports. NOT loaded by the game,
                        NOT shipped. This is the folder to sync between machines and
                        share with the other project.
  design.md  image-list.md  ATTRIBUTIONS.md
```

Workflow: keep the editable master in `assets/Designing/` (or wherever you
like), export a flat PNG/JPG/SVG, drop it in the matching
`godot/assets/<category>/` with the right key name, commit. Done — it's
now in the game and every platform build.

### PNG or JPG?

Both load directly, so pick per asset by what the art needs:

- **PNG** — anything with transparency: every icon (square subject on a
  clear background) and the card fronts (card shape with rounded-corner
  transparency). Also fine for flat-color patterns.
- **JPG** — good for painterly / photographic / textured pieces that are
  edge-to-edge and fully opaque, i.e. the card-back patterns. Smaller
  files at that kind of content. Never use JPG where you need
  transparency.
- If both `<key>.png` and `<key>.jpg` exist, **PNG wins** — delete the one
  you're not using to avoid confusion.

### SVG is fine too

Godot imports `.svg` as a texture (rasterized on import; set the import
`scale` if you need it bigger). So you can drop a `.svg` straight into
`godot/assets/<category>/<key>.svg` and skip exporting a PNG — the game
loader tries `.png`, then `.svg`, then `.jpg` for each key. Keep the
editable master (with layers) in `assets/Designing/`; the file under
`godot/assets/` is the flattened one the game ships.

## Card backs

Each is the **whole card back**, edge-to-edge — the game draws a thin
border on top of it, but the pattern itself should fill the entire canvas
with no padding.

| Key | Used by | Real on-screen size | Make it at (4x headroom) | File |
|---|---|---|---|---|
| `go_fish` | Go Fish card backs | 70 × 100 | **280 × 400** | `godot/assets/cards/backs/go_fish.png` (or `.jpg`) |
| `old_maid` | Old Maid card backs | 70 × 100 | **280 × 400** | `godot/assets/cards/backs/old_maid.png` (or `.jpg`) |
| `memory` | Memory face-down tiles | 125 × 125 (square) | **500 × 500** | `godot/assets/cards/backs/memory.png` (or `.jpg`) |

Why 4x: the game renders to a fixed 1024×720 canvas and then scales that
whole canvas up to fill the real window — on a large/4K monitor that's a
3-4x upscale, so art made at exactly 70×100 would look soft. Made at 4x it
stays crisp big and still shrinks fine.

**The game's name is *not* part of the art.** "GO FISH!" / "OLD MAID" /
"MEMORY" is lettered by code on top of your pattern — don't draw it in.

**Non-uniform sizes across the three are fine.** Each is scaled
independently against its own game's card size.

**About the `old_maid` back specifically:** the file committed today is a
2×2 tiling of a larger center crop of the pattern — at true card size the
un-tiled faces packed in too small to read. If you redraw it, either
pre-tile it the same way, or export the raw pattern and ask for the
tiling to move into runtime (small change). `go_fish` and `memory` are
used as one whole image, scaled straight to the card/tile.

## Card fronts

The whole *face* of a specific card, drawn edge-to-edge in place of the
procedural tint-plus-illustration — same idea as a card back, for the
front. Only the Old Maid card has its own front art today.

| Key | Used by | Real on-screen size | Make it at (4x headroom) | File |
|---|---|---|---|---|
| `old_maid` | The Old Maid card's face in every player's hand | 70 × 100 | **280 × 400** | `godot/assets/cards/fronts/old_maid.png` |

- **Portrait, card-shaped** (PNG — it needs rounded-corner transparency).
  The illustration should read as a whole card face.
- **The "OLD MAID" lettering is drawn by code on top** — don't letter it
  in.
- Falls back, in order: this front art → the `old_maid_card` icon (below)
  → the built-in procedural granny face.
- The file committed today was auto-trimmed of transparent margins and
  centered on a 280×400 canvas (it came off a square artboard). A
  replacement just needs to be a portrait card shape roughly filling
  280×400.

## Icons (items, animals, launcher tiles, the Old Maid card)

One size and shape rule for everything here: a **square PNG, 512 × 512px,
transparent background**, subject centered and not touching the edges. The
game scales it down proportionally and centers it into whatever space it
needs, so one square icon works on a portrait Go Fish card or a square
Memory tile alike.

### Item icons (Go Fish's card faces / Memory's tile faces)

The everyday-object icons (currently procedurally drawn) on Go Fish hand
cards and Memory face-up tiles — both games share the same 13-item set.

| Key | Used for |
|---|---|
| `sun`, `moon`, `star`, `heart`, `flower`, `fish`, `bird`, `tree`, `house`, `umbrella`, `apple`, `ball`, `boat` | Go Fish + Memory item deck (13 ranks) |

Path: `godot/assets/icons/items/<key>.png`

### Animal icons (Letter Match's "Animals" mode)

| Key | Used for |
|---|---|
| `bird`, `cat`, `dog`, `fish`, `lion`, `owl`, `pig` | Letter Match's Animal↔Letter mode (7 letters) |

Path: `godot/assets/icons/animals/<key>.png`

`bird` and `fish` appear in both sets — they can be the same artwork in
both folders if you want; nothing requires them to differ.

### Launcher tile icons

The icon inside each of the four big main-menu buttons (not the whole
button — the colored tile background and label text stay code-drawn).

| Key | Tile |
|---|---|
| `go_fish` | Go Fish |
| `old_maid` | Old Maid |
| `memory` | Memory |
| `letter_match` | Letter Match |

Path: `godot/assets/icons/launcher/<key>.png` — all four exist as real art.

### The Old Maid card's own illustration

| Key | Used for |
|---|---|
| `old_maid_card` | Face on the actual Old Maid card (fallback for the `old_maid` card front above) |

Path: `godot/assets/icons/special/old_maid_card.png`

### About `image-list.md`

That's your running wishlist and can grow freely. But dropping a new
`elephant.png` into `icons/animals/` won't do anything on its own yet —
the game only draws icons for keys it already knows (the 13 item ranks and
7 animal letters above). A genuinely new one needs a small code change to
register it — quick to add, just ask.

## Launcher tile — full custom art (optional, later)

To redo a whole main-menu tile as one piece (background + icon together)
rather than the solid-color background: real tile size 420 × 220px, make
it at **1260 × 660** (3x). Not wired up yet — noted so the number exists.

## The fallback safety net

Every category has a working built-in procedural fallback — this already
works for every piece of art that doesn't exist yet. If a file is
missing, fails to load, or is corrupt, the game draws the built-in
version for that one asset and carries on. So:

- You can replace assets one at a time, in any order; the game stays
  fully playable throughout.
- A bad export, an accidental deletion, or a half-written file never
  breaks the game — worst case that one card/icon shows placeholder art.
- Nothing to "turn on" — real and placeholder art run through the exact
  same code path, just a different source.
