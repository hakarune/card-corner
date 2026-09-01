#!/bin/sh
# Convenience launcher for running from source during development. The
# .deb package (see debpkg/) is for distribution -- use this for iterating
# on the code.
set -e
cd "$(dirname "$0")"
if [ -d .venv ]; then
    . .venv/bin/activate
fi
# Art is committed straight into ui/assets/ as PNG/JPG and loaded directly
# (see assets/design.md) -- nothing to build or convert before launch.
exec python3 main.py "$@"
