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

```bash
git clone <this-repo>
cd card-corner
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
python main.py
```

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

## Project layout

```
core/            Shared card/deck/player primitives and per-game AI strategies
games/           Game-specific rules and screens (go_fish, old_maid, memory, letter_match)
ui/              Shared kid-friendly widgets, theme, and the main menu launcher
assets/          Procedurally generated art (generator scripts, not hand-drawn files)
tests/unit/      Unit tests for core + per-game rule logic
tests/gauntlet/  Headless AI-vs-AI self-play simulation harness
```

## License

MIT — see `LICENSE`.
