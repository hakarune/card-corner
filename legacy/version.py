"""Single source of truth for the app version. Read by the .deb build
(debpkg/build_deb.py embeds this into DEBIAN/control), and by the
in-app "Check for Updates" feature to compare against the latest GitHub
release tag.

Bump this and push a matching `vX.Y.Z` git tag to cut a release (see
.github/workflows/release.yml).
"""

__version__ = "0.2.0"
