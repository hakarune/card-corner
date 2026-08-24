"""The actual sound library: named SFX and the background music loop, all
built from audio.synth's waveform primitives. Sounds are synthesized lazily
on first use and cached (`SoundBank`) rather than up front, so a headless
test run that never touches audio never pays the synthesis cost.
"""
from __future__ import annotations

from typing import Callable

import pygame

from . import synth

NOTES = {
    "C4": 261.63, "D4": 293.66, "E4": 329.63, "F4": 349.23,
    "G4": 392.00, "A4": 440.00, "B4": 493.88,
    "C5": 523.25, "D5": 587.33, "E5": 659.25, "F5": 698.46,
    "G5": 783.99, "A5": 880.00, "B5": 987.77,
    "C6": 1046.50,
}


def _n(name: str, dur: float) -> tuple[float, float]:
    return NOTES[name], dur


def _build_card_select() -> pygame.mixer.Sound:
    return synth.tone(880, 0.05, synth.WAVE_SINE, volume=0.6)


def _build_card_move() -> pygame.mixer.Sound:
    return synth.sweep(700, 320, 0.14, synth.WAVE_TRIANGLE, volume=0.5)


def _build_match() -> pygame.mixer.Sound:
    return synth.sequence(
        [_n("C5", 0.08), _n("E5", 0.08), _n("G5", 0.16)], synth.WAVE_SQUARE, volume=0.7
    )


def _build_miss() -> pygame.mixer.Sound:
    # Gentle, not harsh -- a soft two-note dip, no "wrong buzzer" feel.
    return synth.sequence([_n("A4", 0.12), _n("F4", 0.18)], synth.WAVE_SINE, volume=0.5)


def _build_win() -> pygame.mixer.Sound:
    return synth.sequence(
        [_n("C5", 0.1), _n("E5", 0.1), _n("G5", 0.1), _n("C6", 0.3)], synth.WAVE_SQUARE, volume=0.75
    )


def _build_loss() -> pygame.mixer.Sound:
    # Calm and neutral, not sad -- a short, unhurried descending phrase.
    return synth.sequence([_n("E4", 0.18), _n("C4", 0.3)], synth.WAVE_SINE, volume=0.55)


def _build_button() -> pygame.mixer.Sound:
    return synth.tone(700, 0.04, synth.WAVE_SINE, volume=0.45)


def _build_music_loop() -> pygame.mixer.Sound:
    melody = [
        _n("C5", 0.3), _n("E5", 0.3), _n("G5", 0.3), _n("E5", 0.3),
        _n("C5", 0.3), _n("D5", 0.3), _n("E5", 0.3), _n("G5", 0.5),
        _n("F5", 0.3), _n("E5", 0.3), _n("D5", 0.3), _n("C5", 0.5),
    ]
    return synth.sequence(melody, synth.WAVE_SQUARE, volume=0.35, gap=0.01)


BUILDERS: dict[str, Callable[[], pygame.mixer.Sound]] = {
    "card_select": _build_card_select,
    "card_move": _build_card_move,
    "match": _build_match,
    "miss": _build_miss,
    "win": _build_win,
    "loss": _build_loss,
    "button": _build_button,
    "music_loop": _build_music_loop,
}


class SoundBank:
    def __init__(self):
        self._cache: dict[str, pygame.mixer.Sound] = {}

    def get(self, name: str) -> pygame.mixer.Sound:
        if name not in self._cache:
            if name not in BUILDERS:
                raise KeyError(f"unknown sound: {name}")
            self._cache[name] = BUILDERS[name]()
        return self._cache[name]
