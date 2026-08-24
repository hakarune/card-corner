"""App-wide audio manager: a singleton (`audio`) any screen or widget can
import and call `audio.play_sfx("...")` / `audio.start_music()` on, mirroring
the `ui.settings` singleton pattern. Reads mute/volume from `ui.settings`
on every play (not cached), so toggling mute takes effect immediately
without needing to reload or restart anything.

Never raises and never blocks: if the mixer can't initialize (headless CI,
a machine with no audio hardware), every method becomes a silent no-op.
"""
from __future__ import annotations

import pygame

from ui import settings

from . import synth
from .sounds import SoundBank


class AudioManager:
    def __init__(self):
        self._available = synth.init_mixer()
        self._bank = SoundBank() if self._available else None
        self._music_channel = None
        self._music_playing = False
        if self._available:
            try:
                pygame.mixer.set_num_channels(16)
                self._music_channel = pygame.mixer.Channel(0)
            except pygame.error:
                self._available = False

    @property
    def available(self) -> bool:
        return self._available

    def _muted(self) -> bool:
        return bool(settings.get("muted"))

    def play_sfx(self, name: str) -> None:
        if not self._available or self._muted():
            return
        try:
            sound = self._bank.get(name)
            sound.set_volume(max(0.0, min(1.0, settings.get("sfx_volume"))))
            sound.play()
        except (pygame.error, KeyError):
            pass

    def start_music(self) -> None:
        if not self._available or self._music_playing:
            return
        try:
            music = self._bank.get("music_loop")
            self._music_channel.play(music, loops=-1)
            self._music_playing = True
            self.refresh_music_volume()
        except pygame.error:
            pass

    def stop_music(self) -> None:
        if not self._available:
            return
        try:
            self._music_channel.stop()
        except pygame.error:
            pass
        self._music_playing = False

    def refresh_music_volume(self) -> None:
        """Call every frame (cheap) so a mute/volume change while music is
        already playing takes effect immediately.
        """
        if not self._available or self._music_channel is None:
            return
        volume = 0.0 if self._muted() else max(0.0, min(1.0, settings.get("music_volume")))
        try:
            self._music_channel.set_volume(volume)
        except pygame.error:
            pass


audio = AudioManager()
