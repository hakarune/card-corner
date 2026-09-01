"""Manual, non-intrusive "Check for Updates": queries the GitHub Releases
API for the latest published release and compares it to the installed
version (version.py). Never auto-installs anything -- a game process
running a `sudo dpkg -i` on its own would be a real security smell, so the
honest UX is "here's the new version and its release page", not a fake
one-click auto-update.

Runs the network call on a background thread (`UpdateChecker`) so a slow or
absent network connection can never freeze the game -- the caller polls
`.result` each frame. Must never raise: every failure mode (offline, DNS
failure, timeout, malformed response) resolves to a result with `ok=False`
and a plain error message rather than propagating an exception.
"""
from __future__ import annotations

import json
import threading
import urllib.error
import urllib.request
from dataclasses import dataclass
from typing import Optional

from version import __version__

REPO = "hakarune/card-corner"
API_URL = f"https://api.github.com/repos/{REPO}/releases/latest"
RELEASES_URL = f"https://github.com/{REPO}/releases"
TIMEOUT_SECONDS = 6


@dataclass
class UpdateCheckResult:
    ok: bool
    latest_version: Optional[str] = None
    release_url: str = RELEASES_URL
    error: Optional[str] = None

    @property
    def update_available(self) -> bool:
        if not self.ok or not self.latest_version:
            return False
        return _parse_version(self.latest_version) > _parse_version(__version__)


def _parse_version(v: str) -> tuple:
    """Best-effort 'vX.Y.Z' / 'X.Y.Z' -> (X, Y, Z) for comparison. Any
    non-numeric noise (e.g. a '-beta' suffix) is dropped rather than
    raising, since a malformed tag shouldn't crash the update check.
    """
    v = v.lstrip("vV")
    parts = []
    for piece in v.split("."):
        digits = ""
        for ch in piece:
            if ch.isdigit():
                digits += ch
            else:
                break
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return tuple(parts[:3])


def check_for_update_now() -> UpdateCheckResult:
    """Synchronous check -- blocks up to TIMEOUT_SECONDS. Prefer
    UpdateChecker for anything running inside the game loop.
    """
    try:
        request = urllib.request.Request(
            API_URL,
            headers={"Accept": "application/vnd.github+json", "User-Agent": "card-corner-update-check"},
        )
        with urllib.request.urlopen(request, timeout=TIMEOUT_SECONDS) as response:
            data = json.loads(response.read().decode("utf-8"))
        tag = data.get("tag_name")
        url = data.get("html_url") or RELEASES_URL
        if not tag:
            return UpdateCheckResult(ok=False, error="Couldn't read the latest release.")
        return UpdateCheckResult(ok=True, latest_version=tag, release_url=url)
    except Exception:  # noqa: BLE001 - any failure here must degrade gracefully, never crash
        return UpdateCheckResult(ok=False, error="Couldn't check for updates. Are you online?")


class UpdateChecker:
    """Runs check_for_update_now() on a background thread so the caller's
    render loop never blocks on the network.
    """

    def __init__(self):
        self._thread: Optional[threading.Thread] = None
        self._result: Optional[UpdateCheckResult] = None

    @property
    def checking(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    @property
    def result(self) -> Optional[UpdateCheckResult]:
        return self._result

    def start(self) -> None:
        if self.checking:
            return
        self._result = None
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def _run(self) -> None:
        self._result = check_for_update_now()
