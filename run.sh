#!/bin/sh
# Convenience launcher for running from source during development. The
# .deb package (see debpkg/) is for distribution -- use this for iterating
# on the code.
set -e
cd "$(dirname "$0")"
if [ -d .venv ]; then
    . .venv/bin/activate
fi
# Best-effort: pick up any new/edited assets/source/*.svg before launching
# (see assets/design.md). Never blocks startup -- tools/build_assets.py
# already degrades gracefully (skips, doesn't crash) if cairosvg isn't
# installed or a source file is bad, so a failure here just means you
# keep seeing whatever art was already generated, or the built-in
# placeholder art, never a broken launch. Run it directly (not through
# this script) to see per-asset build status.
python3 tools/build_assets.py >/dev/null 2>&1 || true
exec python3 main.py "$@"
