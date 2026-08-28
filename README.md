# Card Corner

A small suite of kid-friendly card games for **ages 5–8**, built with Python
and Pygame. One launcher, four games:

- **Go Fish**
- **Old Maid**
- **Memory / Concentration**
- **Letter Match** — a solo mini-game matching uppercase letters to their
  lowercase counterparts

Go Fish, Old Maid, and Memory each ship a computer opponent with three
selectable difficulty tiers (Sleepy Fox / Clever Fox / Sneaky Fox). The
opponent never peeks at hidden information, and its choices are randomized
per-tier so no two games play out the same way.

## Requirements

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
ui/assets/       Generated art (see "Art assets" below) — never hand-edited
debpkg/          .deb packaging (build script, .desktop file, icon generator)
assets/          Art source files, the art pipeline guide (design.md), attributions
tools/           build_assets.py — converts assets/source/ into ui/assets/
tests/unit/      Unit tests for core + per-game rule logic
tests/gauntlet/  Headless AI-vs-AI self-play simulation harness
version.py       Single source of truth for the app version
```

## Art assets

Every game/card/icon has a working built-in procedural fallback, so real
art is always optional — nothing breaks if a piece is missing, mid-edit,
or corrupted. To add or replace art:

1. Read `assets/design.md` for exact sizes, naming, and where each file
   goes under `assets/source/`.
2. Run `python tools/build_assets.py` (needs `pip install -e ".[assets]"`
   only if you're using `.svg` sources — a `.png`-only workflow needs
   nothing extra) to regenerate `ui/assets/`, which is what the game
   actually loads.
3. `run.sh` also does this automatically (best-effort, never blocks
   startup) so day-to-day `./run.sh` picks up edits without a separate
   step; the `.deb` build does the same before packaging.

## License

MIT — see `LICENSE`.
