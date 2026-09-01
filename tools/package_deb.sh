#!/bin/sh
# Wrap an already-exported Linux Godot binary into a .deb.
#
#   tools/package_deb.sh <exported-linux-binary> [output-dir]
#
# Produces <output-dir>/card-corner_<version>_amd64.deb. Version comes from
# godot/project.godot (config/version). Needs: dpkg-deb, and one of
# rsvg-convert / inkscape / convert to rasterize the icon (optional -- a
# missing icon just omits the hicolor entry).
set -eu

BIN="${1:?usage: package_deb.sh <linux-binary> [outdir]}"
OUT_DIR="${2:-dist}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PKG="card-corner"

VERSION="$(sed -n 's/.*config\/version="\([^"]*\)".*/\1/p' "$ROOT/godot/project.godot")"
[ -n "$VERSION" ] || VERSION="0.0.0"

STAGE="$(mktemp -d)"
trap 'rm -rf "$STAGE"' EXIT

mkdir -p "$STAGE/DEBIAN" \
         "$STAGE/usr/lib/$PKG" \
         "$STAGE/usr/bin" \
         "$STAGE/usr/share/applications" \
         "$STAGE/usr/share/icons/hicolor/256x256/apps"

install -m 0755 "$BIN" "$STAGE/usr/lib/$PKG/$PKG"
cat > "$STAGE/usr/bin/$PKG" <<EOF
#!/bin/sh
exec /usr/lib/$PKG/$PKG "\$@"
EOF
chmod 0755 "$STAGE/usr/bin/$PKG"

cat > "$STAGE/usr/share/applications/$PKG.desktop" <<EOF
[Desktop Entry]
Type=Application
Name=Card Corner
Comment=Kid-friendly card games: Go Fish, Old Maid, Memory, and Letter Match
Exec=$PKG
Icon=$PKG
Terminal=false
Categories=Game;KidsGame;
EOF

# Icon (best effort)
SVG="$ROOT/godot/icon.svg"
PNG="$STAGE/usr/share/icons/hicolor/256x256/apps/$PKG.png"
if   command -v rsvg-convert >/dev/null 2>&1; then rsvg-convert -w 256 -h 256 "$SVG" -o "$PNG"
elif command -v inkscape     >/dev/null 2>&1; then inkscape "$SVG" -w 256 -h 256 -o "$PNG"
elif command -v convert       >/dev/null 2>&1; then convert -background none -resize 256x256 "$SVG" "$PNG"
else echo "warn: no SVG rasterizer; shipping without a hicolor icon"; rm -f "$PNG"; rmdir -p "$(dirname "$PNG")" 2>/dev/null || true
fi

chmod -R u=rwX,go=rX "$STAGE"   # dpkg-deb rejects DEBIAN dir perms outside 0755-0775

INSTALLED_KB="$(du -sk "$STAGE/usr" | cut -f1)"
cat > "$STAGE/DEBIAN/control" <<EOF
Package: $PKG
Version: $VERSION
Section: games
Priority: optional
Architecture: amd64
Maintainer: Card Corner Maintainers <card-corner@users.noreply.github.com>
Installed-Size: $INSTALLED_KB
Depends: libc6, libgl1, libx11-6, libxcursor1, libxinerama1, libxrandr2, libxi6, libfontconfig1, libudev1, libdbus-1-3
Recommends: libasound2 | libasound2t64, libpulse0
Description: Kid-friendly card game suite (Go Fish, Old Maid, Memory, Letter Match)
 Card Corner is a collection of four card games for ages 5-8, with
 computer opponents at three difficulty tiers and a shared launcher.
 Built with the Godot engine; self-contained, no runtime to install.
EOF

mkdir -p "$ROOT/$OUT_DIR"
DEB="$ROOT/$OUT_DIR/${PKG}_${VERSION}_amd64.deb"
dpkg-deb --build --root-owner-group "$STAGE" "$DEB"
echo "built $DEB"
