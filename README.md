# Card Corner

A small suite of kid-friendly card games for **ages 5–8**. One launcher,
four games:

- **Go Fish**
- **Old Maid**
- **Memory / Concentration**
- **Letter Match** — a solo mini-game matching uppercase letters to their
  lowercase counterparts

Go Fish, Old Maid, and Memory each ship a computer opponent with three
selectable difficulty tiers (Sleepy Fox / Clever Fox / Sneaky Fox). The
opponent never peeks at hidden information, and its choices are randomized
per-tier so no two games play out the same way.

## Repository layout

This project has been migrated from Python/Pygame to **Godot 4.7**:

- **`godot/`** — the Godot 4.7 project. Open `godot/project.godot` in the
  editor and press Play. See `godot/SUMMARY.md` for port status, what's
  verified, and the first-run checklist.
- **`legacy/`** — the original Python/Pygame implementation, archived
  intact for reference. Still runnable (`cd legacy && ./run.sh`); its
  pytest suite is the behavioural spec the port was validated against.
- **`assets/`** — shared art: editable originals under `assets/Designing/`,
  the art guide in `assets/design.md`.

### Building

The exports produce **Linux**, **Windows**, and **Web** builds from one
codebase.

- Locally (needs Godot 4.7.x + its export templates):
  `cd godot && godot --headless --export-release "Linux" ../dist/card-corner.x86_64`
  (also `"Windows Desktop"` → `.exe`, `"Web"` → `dist/web/index.html`).
- `.deb`: `sh tools/package_deb.sh dist/card-corner.x86_64 dist`.
- CI: push a `vX.Y.Z` tag → `.github/workflows/release.yml` builds all
  three targets + the `.deb` and attaches them to a GitHub Release. Every
  push to `main` redeploys the web build to
  <https://hakarune.github.io/card-corner/> via `pages.yml`.

### Tests

`cd godot` then run the headless suites, e.g.
`godot --headless --script res://tests/test_compile_all.gd` and
`... res://tests/test_go_fish.gd` (see `godot/tests/`). CI runs all of
them on every push.

## Requirements (legacy Python version)

- Python 3.11+
- Linux (the target platform — other OSes are not actively tested)

## Install & run

### From a `.deb` (Debian/Ubuntu and derivatives)

Download the latest `card-corner_*.deb` from the
[Releases page](https://github.com/hakarune/card-corner/releases), then:

```bash
sudo apt install ./card-corner_*.deb
```

(or double-click it in a GUI package installer like GDebi). This registers
Card Corner in your desktop's app menu with its own icon. A newer `.deb`
installed the same way cleanly upgrades the existing install. To remove:
`sudo apt remove card-corner`.

### From source (development)

```bash
git clone https://github.com/hakarune/card-corner
cd card-corner
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
./run.sh          # or: python main.py
```

The app launches fullscreen by default; toggle windowed/fullscreen from the
icon on the main menu or the in-game pause overlay (Esc, or the pause icon)
— your choice is remembered for next time.

## Running the tests

```bash
source .venv/bin/activate
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy pytest tests/unit -v
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy pytest tests/gauntlet -v
```

The `dummy` SDL drivers let the test suite (including thousands of simulated
AI-vs-AI games in `tests/gauntlet`) run headless, with no display or audio
device required — this is also how CI runs it (see
`.github/workflows/ci.yml`).

## Building the `.deb` yourself

```bash
source .venv/bin/activate
python debpkg/build_deb.py dist   # -> dist/card-corner_<version>_all.deb
```

Requires system `dpkg-deb` (present on any Debian-family distro). The
package depends on `python3` and `python3-pygame` at install time rather
than vendoring Pygame, matching how a normal apt-installed app pulls its
dependencies. Releases are built and published automatically by
`.github/workflows/release.yml` whenever a `vX.Y.Z` tag is pushed — bump
`version.py` and push a matching tag to cut one.

## Project layout

```
core/            Shared card/deck/player primitives and per-game AI strategies
games/           Game-specific rules and screens (go_fish, old_maid, memory, letter_match)
ui/              Shared kid-friendly widgets, theme, settings, pause overlay, update check
ui/assets/       Real art the game loads — commit PNG/JPG here (see "Art assets" below)
debpkg/          .deb packaging (build script, .desktop file, icon generator)
assets/          design.md (art guide), attributions, Designing/ (editable art originals)
tools/           build_assets.py — optional SVG→PNG converter, not part of any normal flow
tests/unit/      Unit tests for core + per-game rule logic
tests/gauntlet/  Headless AI-vs-AI self-play simulation harness
version.py       Single source of truth for the app version
```

## Art assets

Every game/card/icon has a working built-in procedural fallback, so real
art is always optional — nothing breaks if a piece is missing, mid-edit,
or corrupted. To add or replace art:

1. Read `assets/design.md` for exact sizes, naming, and which folder each
   file goes in.
2. Export a PNG or JPG at the documented size and drop it straight into
   `ui/assets/<category>/<key>.<png|jpg>`. That folder is what the game
   loads — there's no build or convert step.
3. Commit it. Keep your editable original (SVG, `.afdesign`, layered
   export) wherever you like — `assets/Designing/` is the spot for that;
   the game never touches it.

## License

MIT — see `LICENSE`.
