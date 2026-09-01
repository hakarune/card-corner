# Card Corner — Godot 4.7 port

Status of the pygame → Godot port. The original Python is archived intact
under `legacy/` and its pytest suite is the behavioural spec this port was
validated against.

## What's done

| Area | Godot | Ported from |
|---|---|---|
| Core primitives | `core/{card,deck,hand,player,ai_strategy}.gd` | `legacy/core/` |
| Go Fish | `games/go_fish/{go_fish_game,go_fish_ai,go_fish_ask}.gd` + `go_fish.gd`/`.tscn` | `legacy/games/go_fish/` + `core/ai/go_fish_ai.py` |
| Old Maid | `games/old_maid/{old_maid_game,old_maid_ai,old_maid_draw}.gd` + screen | `legacy/games/old_maid/` + `core/ai/old_maid_ai.py` |
| Memory | `games/memory/{memory_game,memory_ai,memory_flip}.gd` + screen (vs-AI + solo) | `legacy/games/memory/` + `core/ai/memory_ai.py` |
| Letter Match | `games/letter_match/letter_match_game.gd` + screen (letters + animals) | `legacy/games/letter_match/` |
| Main menu / difficulty select | `ui/main_menu.gd`, `ui/difficulty_select.gd` | `legacy/ui/launcher.py` |
| Routing | `ui/cc_router.gd` (autoload) | `legacy/main.py` screen stack |
| Theme / card + tile rendering | `ui/theme_data.gd`, `ui/card_theme.gd`, `ui/card_view.gd`, `ui/item_icons.gd` | `legacy/ui/{theme,widgets,items}.py` |
| Audio | `audio/synth.gd` + `ui/cc_audio.gd`; sounds baked by `tools/bake_audio.gd` to `assets/audio/*.wav` | `legacy/audio/` |
| Exports | `export_presets.cfg` (Linux / Windows / Web); `tools/package_deb.sh` | `legacy/debpkg/` |
| CI | `.github/workflows/{ci,release,pages}.yml` | `legacy/github-workflows/` |

## What was verified (Godot 4.7.2 headless, in-repo)

- `tests/test_compile_all.gd` — loads every `.gd` + instantiates every `.tscn`.
- `tests/test_{core,go_fish,go_fish_ai,old_maid,memory,letter_match,audio}.gd` —
  logic + AI unit tests ported from `legacy/tests/unit/`. All green.
- `tests/test_screens.gd` — headless-drives every screen to completion
  (Old Maid to a loser; Memory solo + vs-AI clear the board; Letter Match
  both modes complete) with no script errors.
- `tests/test_go_fish_scene.gd` — plays a full Go Fish game via the screen.
- **Linux + Windows exports** produced and verified locally. **`.deb`**
  built and inspected (`tools/package_deb.sh`).

## What is NOT verified here

- **Visuals / layout.** Godot headless renders no pixels, so pixel-level
  layout, colours, and the ported `item_icons.gd` glyph geometry were not
  eyeballed. Open the project in the editor and run each scene once.
- **Web export.** No web export template is installed on the dev machine;
  the `Web` preset is configured (single-threaded, no COOP/COEP needed)
  but only CI (`release.yml` / `pages.yml`) actually builds it.
- **Audio playback.** Synth correctness is unit-tested on short buffers
  and every sound is baked to a valid WAV, but nothing was listened to.

## Known gaps / deferred

- Deal-slide and card-flip animations, and win confetti (all games) —
  legacy had them; ported screens don't yet. Polish pass.
- Bold headings and suit glyphs (♥♦♣♠ on the Old Maid card face) need a
  bundled font — `ThemeDB.fallback_font` may render tofu for suits.
- "Check for Updates" launcher UI — dropped; revisit with `HTTPRequest`
  if wanted (low value for the web build).
- Pause overlay — legacy had an in-game pause menu; screens currently
  have only a "Menu" button. Add a shared pause scene.

## First-run checklist (in the Godot editor)

1. Open `godot/project.godot` in Godot 4.7.x. Let it import.
2. Press Play. The main menu should show four colour-coded tiles with
   launcher icons.
3. Play one round of each game; check card faces, the Memory grid, the
   Letter Match reshuffle, the Old Maid "Draw" button, difficulty select,
   and "Play Alone" for Memory.
4. Confirm audio plays (music on the menu; SFX on taps/matches).
5. `godot --headless --export-release "Web" build/web/index.html` once a
   web template is installed, and serve `build/web/` to test in a browser.

## Releasing

- Bump `config/version` in `godot/project.godot`, commit, tag `vX.Y.Z`,
  push the tag. `release.yml` exports all three targets, builds the `.deb`,
  and attaches everything to a GitHub Release.
- `pages.yml` deploys the web build to
  `https://hakarune.github.io/card-corner/` on every push to `main`
  (GitHub Pages source is already set to "GitHub Actions").
- Re-run `tools/bake_audio.gd` after any change to `audio/synth.gd` or a
  sound recipe, and commit the updated `assets/audio/*.wav`.
