"""Persistent user settings (fullscreen, mute, volumes, last windowed size),
stored as JSON under the platform config dir (XDG_CONFIG_HOME if set, else
~/.config). Loaded once at import time and kept as a module-level singleton
so any screen can read/write it without threading a settings object through
every constructor.

Never raises: a missing/corrupt settings file falls back to defaults, and a
failed write is silently ignored -- a settings file problem should never
crash or block the game from launching.
"""
from __future__ import annotations

import json
import os
from pathlib import Path

DEFAULTS: dict = {
    "fullscreen": True,
    "muted": False,
    "music_volume": 0.35,
    "sfx_volume": 0.8,
    "windowed_size": [1024, 720],
}


def _config_dir() -> Path:
    xdg = os.environ.get("XDG_CONFIG_HOME")
    base = Path(xdg) if xdg else Path.home() / ".config"
    return base / "card-corner"


SETTINGS_PATH = _config_dir() / "settings.json"


def _load() -> dict:
    try:
        data = json.loads(SETTINGS_PATH.read_text())
        if not isinstance(data, dict):
            return dict(DEFAULTS)
        return {**DEFAULTS, **data}
    except (FileNotFoundError, json.JSONDecodeError, OSError, ValueError):
        return dict(DEFAULTS)


def _save() -> None:
    try:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        SETTINGS_PATH.write_text(json.dumps(_settings, indent=2))
    except (OSError, TypeError):
        pass


_settings: dict = _load()


def get(key: str):
    return _settings.get(key, DEFAULTS.get(key))


def set(key: str, value) -> None:
    _settings[key] = value
    _save()


def reload() -> None:
    """Re-read the settings file from disk, discarding in-memory changes.
    Used by tests to isolate cases from each other.
    """
    global _settings
    _settings = _load()
