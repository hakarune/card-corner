"""Procedural audio synthesis primitives. Every sound in this game — music
and SFX alike — is generated at runtime from simple waveforms rather than
sourced from any external asset, sidestepping any licensing question for
something baked into a distributed package. Pure stdlib (`array`, `math`)
plus `pygame.mixer` — deliberately no numpy dependency, so packaging stays
simple (see debpkg/build_deb.py's Depends).
"""
from __future__ import annotations

import array
import math

import pygame

SAMPLE_RATE = 44100
# Headroom below int16 max (32767) so mixing multiple simultaneous sounds
# doesn't clip.
AMPLITUDE = 24000

WAVE_SINE = "sine"
WAVE_SQUARE = "square"
WAVE_TRIANGLE = "triangle"


def init_mixer() -> bool:
    """Ensures the mixer is active with the exact format this module's
    buffers assume (44100Hz, 16-bit signed, mono). `pygame.init()` (called
    by main.py, and by every test's shared session fixture) initializes
    the mixer itself first, with SDL's own default -- (44100, -16, 2),
    i.e. *stereo* -- which would silently mismatch every mono buffer this
    module generates (pygame.mixer.Sound does not resample/convert a
    buffer to the active format). So: if the mixer is already running with
    a different format, tear it down and re-init with ours. Returns
    whether audio is actually available -- some environments (a minimal
    container, a machine with no sound hardware) can fail here, and that
    must never block the game from launching.
    """
    desired = (SAMPLE_RATE, -16, 1)
    current = pygame.mixer.get_init()
    if current == desired:
        return True
    try:
        if current is not None:
            pygame.mixer.quit()
        pygame.mixer.init(frequency=SAMPLE_RATE, size=-16, channels=1, buffer=512)
        return True
    except pygame.error:
        return False


def _envelope(i: int, n: int, attack: int, release: int) -> float:
    """Linear fade-in/out so notes don't click at their edges."""
    if i < attack:
        return i / attack
    if i > n - release:
        return max(0.0, (n - i) / release)
    return 1.0


def _clamp_sample(value: float) -> int:
    """Clamps to the valid int16 range regardless of `volume` -- a future
    caller passing e.g. volume=1.2 for emphasis must degrade to a clipped-
    but-valid sample, never an uncaught OverflowError from array.array.
    """
    return max(-32768, min(32767, int(value)))


def _wave(shape: str, phase: float) -> float:
    theta = phase % 1.0
    if shape == WAVE_SQUARE:
        return 1.0 if theta < 0.5 else -1.0
    if shape == WAVE_TRIANGLE:
        return 4 * abs(theta - 0.5) - 1.0
    return math.sin(2 * math.pi * theta)


def tone(freq: float, duration: float, shape: str = WAVE_SINE, volume: float = 1.0) -> pygame.mixer.Sound:
    """A single note. `freq` <= 0 produces silence of the given duration."""
    n = max(1, int(SAMPLE_RATE * duration))
    attack = max(1, int(n * 0.05))
    release = max(1, int(n * 0.2))
    samples = array.array("h", bytes(2 * n))
    if freq > 0:
        for i in range(n):
            phase = freq * i / SAMPLE_RATE
            env = _envelope(i, n, attack, release)
            samples[i] = _clamp_sample(AMPLITUDE * volume * env * _wave(shape, phase))
    return pygame.mixer.Sound(buffer=samples.tobytes())


def sweep(start_freq: float, end_freq: float, duration: float, shape: str = WAVE_SINE, volume: float = 1.0) -> pygame.mixer.Sound:
    """A single note whose pitch glides linearly from start_freq to
    end_freq -- used for the deal/draw 'whoosh' and similar effects.
    """
    n = max(1, int(SAMPLE_RATE * duration))
    attack = max(1, int(n * 0.05))
    release = max(1, int(n * 0.25))
    samples = array.array("h", bytes(2 * n))
    phase = 0.0
    for i in range(n):
        t = i / n
        freq = start_freq + (end_freq - start_freq) * t
        phase += freq / SAMPLE_RATE
        env = _envelope(i, n, attack, release)
        samples[i] = _clamp_sample(AMPLITUDE * volume * env * _wave(shape, phase))
    return pygame.mixer.Sound(buffer=samples.tobytes())


def sequence(
    notes: list[tuple[float, float]],
    shape: str = WAVE_SQUARE,
    volume: float = 1.0,
    gap: float = 0.015,
) -> pygame.mixer.Sound:
    """A short melody: `notes` is a list of (freq_hz, duration_s) pairs;
    freq <= 0 is a rest. Used for celebratory/miss/win/loss stingers and
    the background music loop.
    """
    segments = []
    total_n = 0
    gap_n = int(SAMPLE_RATE * gap)
    for freq, dur in notes:
        n = max(1, int(SAMPLE_RATE * dur))
        segments.append((freq, n))
        total_n += n + gap_n

    samples = array.array("h", bytes(2 * total_n))
    idx = 0
    for freq, n in segments:
        if freq > 0:
            attack = max(1, int(n * 0.05))
            release = max(1, int(n * 0.15))
            for i in range(n):
                phase = freq * i / SAMPLE_RATE
                env = _envelope(i, n, attack, release)
                samples[idx + i] = _clamp_sample(AMPLITUDE * volume * env * _wave(shape, phase))
        idx += n + gap_n
    return pygame.mixer.Sound(buffer=samples.tobytes())
