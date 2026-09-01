"""Tests for audio.synth's waveform synthesis primitives."""
from __future__ import annotations

import pygame

from audio import synth


def test_init_mixer_forces_mono_16bit_44100(surface):
    assert synth.init_mixer()
    assert pygame.mixer.get_init() == (synth.SAMPLE_RATE, -16, 1)


def test_init_mixer_is_idempotent(surface):
    synth.init_mixer()
    first = pygame.mixer.get_init()
    assert synth.init_mixer()
    assert pygame.mixer.get_init() == first


def test_tone_produces_a_sound_of_the_requested_duration(surface):
    synth.init_mixer()
    snd = synth.tone(440, 0.3)
    assert isinstance(snd, pygame.mixer.Sound)
    assert snd.get_length() == _approx(0.3)


def test_tone_zero_frequency_is_silent_but_still_valid(surface):
    synth.init_mixer()
    snd = synth.tone(0, 0.1)
    raw = pygame.mixer.Sound.get_raw(snd)
    assert all(b == 0 for b in raw)


def test_sweep_produces_a_sound_of_the_requested_duration(surface):
    synth.init_mixer()
    snd = synth.sweep(600, 200, 0.15)
    assert snd.get_length() == _approx(0.15)


def test_sequence_duration_is_roughly_sum_of_notes_and_gaps(surface):
    synth.init_mixer()
    notes = [(440, 0.1), (550, 0.1), (660, 0.1)]
    snd = synth.sequence(notes, gap=0.02)
    expected = sum(d for _, d in notes) + 0.02 * len(notes)
    assert snd.get_length() == _approx(expected, rel=0.05)


def test_sequence_handles_rests():
    # A rest (freq <= 0) must not raise and must still occupy its duration.
    synth.init_mixer()
    snd = synth.sequence([(0, 0.05), (440, 0.05)])
    assert snd.get_length() > 0.05


def test_different_wave_shapes_produce_different_audio(surface):
    synth.init_mixer()
    sine = pygame.mixer.Sound.get_raw(synth.tone(440, 0.05, synth.WAVE_SINE))
    square = pygame.mixer.Sound.get_raw(synth.tone(440, 0.05, synth.WAVE_SQUARE))
    assert sine != square


def test_out_of_range_volume_clamps_instead_of_raising(surface):
    # A future caller passing e.g. volume=1.2 for emphasis must degrade to
    # a clipped sample, not an uncaught OverflowError from array.array.
    synth.init_mixer()
    assert synth.tone(440, 0.05, volume=5.0) is not None
    assert synth.sweep(600, 200, 0.05, volume=5.0) is not None
    assert synth.sequence([(440, 0.05)], volume=5.0) is not None
    assert synth.tone(440, 0.05, volume=-5.0) is not None


def _approx(value, rel=1e-2):
    import pytest

    return pytest.approx(value, rel=rel)
