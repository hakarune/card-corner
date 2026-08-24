"""Tests for audio.manager.AudioManager: mute/volume behavior sourced live
from ui.settings, graceful degradation when the mixer is unavailable, and
that nothing here ever raises.
"""
from __future__ import annotations

import pygame
import pytest

from audio import manager as manager_module
from audio.manager import AudioManager
from ui import settings


@pytest.fixture(autouse=True)
def isolated_settings(tmp_path, monkeypatch):
    monkeypatch.setattr(settings, "SETTINGS_PATH", tmp_path / "settings.json")
    settings._settings = dict(settings.DEFAULTS)
    yield


def test_available_when_mixer_can_initialize(surface):
    am = AudioManager()
    assert am.available


def test_unavailable_mixer_makes_everything_a_safe_no_op(monkeypatch):
    monkeypatch.setattr(manager_module.synth, "init_mixer", lambda: False)
    am = AudioManager()
    assert not am.available
    am.play_sfx("card_select")  # must not raise
    am.start_music()  # must not raise
    am.refresh_music_volume()  # must not raise
    am.stop_music()  # must not raise


def test_play_sfx_unknown_name_does_not_raise(surface):
    am = AudioManager()
    am.play_sfx("this_sound_does_not_exist")  # must not raise


def test_play_sfx_respects_mute(surface):
    settings.set("muted", True)
    am = AudioManager()
    played = []
    real_get = am._bank.get

    def spy_get(name):
        played.append(name)
        return real_get(name)

    am._bank.get = spy_get
    am.play_sfx("card_select")
    assert played == []  # never even looked up the sound while muted


def test_play_sfx_plays_when_unmuted(surface):
    settings.set("muted", False)
    am = AudioManager()
    played = []
    real_get = am._bank.get

    def spy_get(name):
        played.append(name)
        return real_get(name)

    am._bank.get = spy_get
    am.play_sfx("card_select")
    assert played == ["card_select"]


def test_start_music_is_idempotent(surface):
    am = AudioManager()
    am.start_music()
    channel_after_first = am._music_channel
    am.start_music()  # second call should be a no-op, not restart/stack
    assert am._music_channel is channel_after_first
    am.stop_music()


def test_stop_music_after_start(surface):
    am = AudioManager()
    am.start_music()
    assert am._music_playing
    am.stop_music()
    assert not am._music_playing


def test_refresh_music_volume_mutes_to_zero(surface):
    am = AudioManager()
    am.start_music()
    settings.set("muted", True)
    am.refresh_music_volume()
    assert am._music_channel.get_volume() == pytest.approx(0.0)
    settings.set("muted", False)
    settings.set("music_volume", 0.5)
    am.refresh_music_volume()
    assert am._music_channel.get_volume() == pytest.approx(0.5)
    am.stop_music()


def test_refresh_music_volume_clamps_out_of_range_values(surface):
    am = AudioManager()
    am.start_music()
    settings.set("music_volume", 5.0)  # way over 1.0
    am.refresh_music_volume()
    assert am._music_channel.get_volume() == pytest.approx(1.0)
    settings.set("music_volume", -3.0)
    am.refresh_music_volume()
    assert am._music_channel.get_volume() == pytest.approx(0.0)
    am.stop_music()


def test_module_level_singleton_exists_and_is_usable(surface):
    from audio.manager import audio

    assert isinstance(audio, AudioManager)
    audio.play_sfx("button")  # must not raise regardless of test ordering
