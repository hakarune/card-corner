"""Tests for audio.sounds' SoundBank -- lazy synthesis + caching of the
named SFX/music library.
"""
from __future__ import annotations

import pygame
import pytest

from audio import synth
from audio.sounds import BUILDERS, SoundBank


@pytest.fixture(autouse=True)
def mixer_ready(surface):
    synth.init_mixer()


def test_all_builders_produce_a_valid_sound():
    bank = SoundBank()
    for name in BUILDERS:
        sound = bank.get(name)
        assert isinstance(sound, pygame.mixer.Sound)
        assert sound.get_length() > 0


def test_get_caches_the_same_object():
    bank = SoundBank()
    first = bank.get("card_select")
    second = bank.get("card_select")
    assert first is second


def test_unknown_sound_name_raises_key_error():
    bank = SoundBank()
    with pytest.raises(KeyError):
        bank.get("not_a_real_sound")


def test_expected_sfx_names_are_all_present():
    # Spec §3 minimum SFX list, mapped to the names screens will use.
    expected = {"card_select", "card_move", "match", "miss", "win", "loss", "button", "music_loop"}
    assert expected == set(BUILDERS.keys())


def test_win_and_loss_are_audibly_distinct():
    bank = SoundBank()
    win_raw = pygame.mixer.Sound.get_raw(bank.get("win"))
    loss_raw = pygame.mixer.Sound.get_raw(bank.get("loss"))
    assert win_raw != loss_raw


def test_win_is_longer_than_a_single_ui_click():
    # A celebratory win stinger should read as more than an incidental blip.
    bank = SoundBank()
    assert bank.get("win").get_length() > bank.get("button").get_length()
