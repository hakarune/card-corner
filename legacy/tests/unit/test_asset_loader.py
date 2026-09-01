"""ui/asset_loader.py: loading real art from ui/assets/ (see
assets/design.md), and the "never raise, missing just means fall back"
contract every caller depends on.
"""
from __future__ import annotations

import pygame
import pytest

from ui import asset_loader, theme
from ui.widgets import draw_card_back, draw_old_maid_illustration


def test_load_card_back_finds_a_real_generated_asset():
    # These three are committed, real art (assets/design.md) -- not a
    # placeholder-only test fixture.
    img = asset_loader.load_card_back("go_fish")
    assert img is not None
    assert img.get_size() == (280, 400)


def test_load_card_back_returns_none_for_a_key_with_no_art_yet():
    assert asset_loader.load_card_back("not_a_real_game") is None


def test_load_icon_finds_a_real_generated_launcher_asset():
    # The four main-menu game icons are committed, real art (assets/design.md).
    img = asset_loader.load_icon("launcher", "memory")
    assert img is not None
    assert img.get_size() == (512, 512)


def test_load_icon_returns_none_for_categories_with_no_art_yet():
    # Item / animal / special icons haven't been made yet -- must fall back.
    assert asset_loader.load_icon("items", "sun") is None
    assert asset_loader.load_icon("animals", "cat") is None
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


@pytest.fixture
def staged_assets(tmp_path, monkeypatch):
    """Redirects asset_loader's importlib.resources.files("ui.assets") at a
    real temp directory so a test can drop arbitrary art files under it.
    Clears the load cache on the way in and out so nothing leaks between
    tests.
    """
    import importlib.resources

    asset_loader._load.cache_clear()
    monkeypatch.setattr(importlib.resources, "files", lambda *_a: tmp_path)
    yield tmp_path
    asset_loader._load.cache_clear()


def test_load_resolves_a_jpg_when_that_is_the_only_file(surface, staged_assets):
    # A .jpg drop-in must be picked up just like a .png (design.md: card
    # backs may be committed as JPG).
    backs = staged_assets / "cards" / "backs"
    backs.mkdir(parents=True)
    art = pygame.Surface((280, 400))
    art.fill((10, 120, 200))
    pygame.image.save(art, str(backs / "go_fish.jpg"))

    img = asset_loader.load_card_back("go_fish")
    assert img is not None
    assert img.get_size() == (280, 400)


def test_load_prefers_png_over_jpg_when_both_exist(surface, staged_assets):
    backs = staged_assets / "cards" / "backs"
    backs.mkdir(parents=True)
    png_art = pygame.Surface((12, 12), pygame.SRCALPHA)
    png_art.fill((0, 0, 0, 255))
    pygame.image.save(png_art, str(backs / "memory.png"))
    jpg_art = pygame.Surface((34, 34))
    jpg_art.fill((255, 255, 255))
    pygame.image.save(jpg_art, str(backs / "memory.jpg"))

    img = asset_loader.load_card_back("memory")
    assert img is not None
    assert img.get_size() == (12, 12)  # the .png, not the .jpg


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


def test_transparent_gaps_in_real_art_show_the_theme_color_not_whatever_is_behind(surface, monkeypatch):
    # Bug caught during playtesting: the source SVGs are transparent in the
    # gaps between pattern elements (by design -- see assets/design.md),
    # but draw_card_back's image path used to blit straight onto the
    # destination with no solid base fill first, so those gaps let
    # whatever was already on the surface show through -- the page
    # background, or an overlapping *previous* card's own label text in a
    # hand of face-down cards spaced close enough to overlap.
    from ui import widgets

    fake = pygame.Surface((10, 10), pygame.SRCALPHA)  # fully transparent everywhere
    monkeypatch.setattr(widgets.asset_loader, "load_card_back", lambda key: fake)

    rect = pygame.Rect(0, 0, 90, 130)
    surf = pygame.Surface(rect.size)
    intruder = (222, 33, 99)  # stands in for "an overlapping card's label" / page background
    surf.fill(intruder)

    card_theme = theme.CARD_THEMES["go_fish"]
    draw_card_back(surf, rect, card_theme)

    # Near the top edge: clear of the border stroke, clear of the rounded
    # corners (horizontally centered), and clear of the vertically-
    # centered label -- must be the theme's solid color, never the
    # intruder color.
    assert surf.get_at((45, 20))[:3] == card_theme.back_color
    assert surf.get_at((45, 20))[:3] != intruder


def test_load_card_front_finds_a_real_generated_asset():
    # The Old Maid card face is committed, real art (assets/design.md).
    img = asset_loader.load_card_front("old_maid")
    assert img is not None
    assert img.get_size() == (280, 400)


def test_load_card_front_returns_none_for_a_key_with_no_art_yet():
    assert asset_loader.load_card_front("not_a_real_card") is None


def test_old_maid_illustration_falls_through_cleanly_when_no_art(surface, monkeypatch):
    # Neither the card front nor the special icon exists -- must reach the
    # procedural granny face without crashing on an empty category.
    from ui import widgets

    monkeypatch.setattr(widgets.asset_loader, "load_card_front", lambda key: None)
    monkeypatch.setattr(widgets.asset_loader, "load_icon", lambda category, key: None)
    rect = pygame.Rect(0, 0, 90, 130)
    surf = pygame.Surface(rect.size)
    draw_old_maid_illustration(surf, rect)  # must not raise


def test_old_maid_illustration_uses_card_front_art_when_present(surface, monkeypatch):
    from ui import widgets

    fake = pygame.Surface((10, 10), pygame.SRCALPHA)
    fake.fill((7, 8, 9, 255))
    monkeypatch.setattr(widgets.asset_loader, "load_card_front", lambda key: fake)

    rect = pygame.Rect(0, 0, 90, 130)
    surf = pygame.Surface(rect.size)
    draw_old_maid_illustration(surf, rect)
    # Well inside the card, clear of the border stroke and the bottom label.
    assert surf.get_at((45, 45))[:3] == (7, 8, 9)


def test_old_maid_illustration_uses_special_icon_when_no_card_front(surface, monkeypatch):
    from ui import widgets

    fake = pygame.Surface((10, 10), pygame.SRCALPHA)
    fake.fill((4, 5, 6, 255))
    monkeypatch.setattr(widgets.asset_loader, "load_card_front", lambda key: None)
    monkeypatch.setattr(widgets.asset_loader, "load_icon", lambda category, key: fake)

    rect = pygame.Rect(0, 0, 90, 130)
    surf = pygame.Surface(rect.size)
    draw_old_maid_illustration(surf, rect)
    # Center of the icon area -- must be the fake art's flat color, not
    # any part of the procedural face (which would never be flat there).
    assert surf.get_at((45, 55))[:3] == (4, 5, 6)
