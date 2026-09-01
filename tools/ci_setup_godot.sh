#!/usr/bin/env bash
# Download Godot (headless Linux) + matching export templates for CI.
# Version comes from godot/project.godot's config/features ("4.7") plus
# GODOT_PATCH (default below). Exports GODOT_BIN.
set -euo pipefail

GODOT_VERSION="${GODOT_VERSION:-4.7.2}"
BASE="https://github.com/godotengine/godot/releases/download/${GODOT_VERSION}-stable"
WORK="${RUNNER_TEMP:-/tmp}/godot"
mkdir -p "$WORK"

echo "::group::Download Godot ${GODOT_VERSION}"
curl -sSL -o "$WORK/godot.zip" "${BASE}/Godot_v${GODOT_VERSION}-stable_linux.x86_64.zip"
unzip -o -q "$WORK/godot.zip" -d "$WORK"
GODOT_BIN="$(find "$WORK" -maxdepth 1 -name 'Godot_v*_linux.x86_64' -type f | head -n1)"
chmod +x "$GODOT_BIN"
echo "GODOT_BIN=$GODOT_BIN" >> "$GITHUB_ENV"
echo "::endgroup::"

echo "::group::Download export templates"
curl -sSL -o "$WORK/templates.tpz" "${BASE}/Godot_v${GODOT_VERSION}-stable_export_templates.tpz"
TPL_DIR="$HOME/.local/share/godot/export_templates/${GODOT_VERSION}.stable"
mkdir -p "$TPL_DIR"
unzip -o -q "$WORK/templates.tpz" -d "$WORK"
mv "$WORK"/templates/* "$TPL_DIR/"
echo "templates -> $TPL_DIR"
ls "$TPL_DIR" | head
echo "::endgroup::"
