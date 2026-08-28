"""ui/asset_loader.py: loading real art from ui/assets/ (see
assets/design.md), and the "never raise, missing just means fall back"
contract every caller depends on.
"""
from __future__ import annotations

import pygame
import pytest

from ui import asset_loader, theme
from ui.widgets import draw_card_back


def test_load_card_back_finds_a_real_generated_asset():
    # These three are committed, real art (assets/design.md) -- not a
    # placeholder-only test fixture.
    img = asset_loader.load_card_back("go_fish")
    assert img is not None
    assert img.get_size() == (280, 400)


def test_load_card_back_returns_none_for_a_key_with_no_art_yet():
    assert asset_loader.load_card_back("not_a_real_game") is None


def test_load_icon_returns_none_when_nothing_has_been_made_yet():
    # No icon-category art exists yet at all (only the 3 card backs do).
    assert asset_loader.load_icon("items", "sun") is None
    assert asset_loader.load_icon("animals", "cat") is None
    assert asset_loader.load_icon("launcher", "memory") is None
    assert asset_loader.load_icon("special", "old_maid_card") is None


def test_load_card_back_is_cached_not_reloaded_every_call():
    first = asset_loader.load_card_back("memory")
    second = asset_loader.load_card_back("memory")
    assert first is second


def test_a_missing_or_broken_asset_never_raises(monkeypatch):
    # Simulates corruption/a bad path -- must degrade to None, never crash
    # the caller (spec: real art is a pure upgrade, never a hard dependency).
    asset_loader._load.cache_clear()

    class ExplodingPath:
        def joinpath(self, *_a):
            raise OSError("simulated corrupt/unreadable asset")

    import importlib.resources

    monkeypatch.setattr(importlib.resources, "files", lambda *_a: ExplodingPath())
    assert asset_loader.load_card_back("go_fish") is None
    asset_loader._load.cache_clear()


def test_draw_card_back_uses_real_art_when_present(surface, monkeypatch):
    from ui import widgets

    fake = pygame.Surface((10, 10), pygame.SRCALPHA)
    fake.fill((1, 2, 3, 255))
    monkeypatch.setattr(widgets.asset_loader, "load_card_back", lambda key: fake)

    rect = pygame.Rect(0, 0, 90, 130)
    surf = pygame.Surface(rect.size)
    draw_card_back(surf, rect, theme.CARD_THEMES["go_fish"])
    # A pixel well inside the card (clear of the border stroke and the
    # centered label text) should carry the fake image's color, not the
    # theme's flat back_color -- proof the image path actually rendered.
    assert surf.get_at((10, 10))[:3] == (1, 2, 3)


def test_draw_card_back_falls_back_to_procedural_when_no_art(surface, monkeypatch):
    from ui import widgets

    monkeypatch.setattr(widgets.asset_loader, "load_card_back", lambda key: None)
    rect = pygame.Rect(0, 0, 90, 130)
    surf = pygame.Surface(rect.size)
    draw_card_back(surf, rect, theme.CARD_THEMES["go_fish"])
    assert surf.get_at((5, 65))[:3] == theme.CARD_THEMES["go_fish"].back_color
