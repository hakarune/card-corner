"""Tests for ui.settings. Every test redirects SETTINGS_PATH to a tmp_path
so nothing here ever touches the real ~/.config/card-corner/settings.json.
"""
from __future__ import annotations

import json

import pytest

from ui import settings


@pytest.fixture(autouse=True)
def isolated_settings_path(tmp_path, monkeypatch):
    path = tmp_path / "settings.json"
    monkeypatch.setattr(settings, "SETTINGS_PATH", path)
    settings._settings = dict(settings.DEFAULTS)
    yield path


def test_defaults_when_no_file_exists():
    settings.reload()
    for key, value in settings.DEFAULTS.items():
        assert settings.get(key) == value


def test_set_persists_to_disk(isolated_settings_path):
    settings.set("fullscreen", False)
    assert isolated_settings_path.exists()
    data = json.loads(isolated_settings_path.read_text())
    assert data["fullscreen"] is False


def test_set_is_readable_immediately_without_reload():
    settings.set("muted", True)
    assert settings.get("muted") is True


def test_reload_reads_persisted_value(isolated_settings_path):
    settings.set("music_volume", 0.1)
    settings.reload()
    assert settings.get("music_volume") == 0.1


def test_corrupt_file_falls_back_to_defaults(isolated_settings_path):
    isolated_settings_path.write_text("{not valid json")
    settings.reload()
    assert settings.get("fullscreen") == settings.DEFAULTS["fullscreen"]


def test_non_dict_json_falls_back_to_defaults(isolated_settings_path):
    isolated_settings_path.write_text("[1, 2, 3]")
    settings.reload()
    assert settings.get("muted") == settings.DEFAULTS["muted"]


def test_missing_key_falls_back_to_default_without_crashing(isolated_settings_path):
    isolated_settings_path.write_text(json.dumps({"fullscreen": False}))
    settings.reload()
    assert settings.get("fullscreen") is False
    assert settings.get("sfx_volume") == settings.DEFAULTS["sfx_volume"]


def test_non_json_serializable_value_does_not_raise(isolated_settings_path):
    settings.set("fullscreen", object())  # json.dumps can't serialize this
    # In-memory value is still whatever was set -- just never hits disk.
    assert settings.get("fullscreen") is not None
    assert not isolated_settings_path.exists()


def test_unwritable_path_does_not_raise(isolated_settings_path, monkeypatch):
    # Point at a path whose parent can never be created (a file, not a dir).
    bad_parent = isolated_settings_path.parent / "not_a_dir"
    bad_parent.write_text("i am a file, not a directory")
    monkeypatch.setattr(settings, "SETTINGS_PATH", bad_parent / "settings.json")
    settings.set("fullscreen", False)  # must not raise
    assert settings.get("fullscreen") is False
