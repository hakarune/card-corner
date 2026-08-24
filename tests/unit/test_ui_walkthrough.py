"""Scripted headless input-simulation walkthrough: menu -> game select ->
play -> win/lose -> return to menu, for all four games. Runs under the
SDL dummy video/audio drivers (see CI workflow and README) so no real
display or audio device is required.
"""
from __future__ import annotations

import pygame

from core.ai.base import Difficulty
from games.go_fish.screen import GoFishScreen
from games.letter_match.screen import LetterMatchScreen
from games.memory.screen import MemoryScreen
from games.old_maid.screen import OldMaidScreen
from ui.launcher import DifficultySelectScreen, LauncherScreen
from ui.theme import WINDOW_SIZE

MAX_STEPS = 3000


def click(screen, pos):
    event = pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos)
    screen.handle_event(event)


def test_launcher_renders_and_all_four_tiles_are_clickable(surface):
    selections = []
    launcher = LauncherScreen(WINDOW_SIZE, lambda key: selections.append(key) or None)
    launcher.draw(surface)
    assert len(launcher.buttons) == 4
    for btn in launcher.buttons:
        click(launcher, btn.rect.center)
    assert set(selections) == {"go_fish", "old_maid", "memory", "letter_match"}


def test_difficulty_select_all_buttons_navigate_and_back_works():
    picked = []
    screen = DifficultySelectScreen(
        WINDOW_SIZE, "Go Fish", (91, 155, 213), lambda d: picked.append(d) or "GAME", lambda: "MENU"
    )
    assert len(screen.buttons) == 4  # 3 difficulties + back
    for btn in screen.buttons[:3]:
        click(screen, btn.rect.center)
    assert set(picked) == {Difficulty.EASY, Difficulty.MEDIUM, Difficulty.HARD}
    back_btn = screen.buttons[-1]
    click(screen, back_btn.rect.center)
    assert screen.next_screen() == "MENU"


def _drain_ai_turns(screen, flag_attr: str, max_steps: int = MAX_STEPS) -> None:
    # Deliberately keeps draining even after game.game_over flips True: a
    # screen's own end-of-game callback (confetti, _end_buttons) can be
    # scheduled with a short delay that outlives the engine-level flag.
    steps = 0
    while getattr(screen, flag_attr) and steps < max_steps:
        screen.update(5.0)
        steps += 1
    assert steps < max_steps, f"{flag_attr} never cleared within {max_steps} steps"


def test_go_fish_full_playthrough_reaches_game_over_and_returns_to_menu(surface):
    menu_hits = []
    screen = GoFishScreen(WINDOW_SIZE, Difficulty.EASY, lambda: menu_hits.append(1) or "MENU")
    steps = 0
    while not screen.game.game_over and steps < MAX_STEPS:
        _drain_ai_turns(screen, "_waiting_for_ai")
        screen.draw(surface)
        if screen.game.game_over:
            break
        if screen._card_rects:
            rect, _rank = screen._card_rects[0]
            click(screen, rect.center)
        screen.update(0.0)
        steps += 1
    assert screen.game.game_over
    assert steps < MAX_STEPS

    screen.draw(surface)
    assert len(screen._end_buttons) == 2
    menu_btn = screen._end_buttons[1]
    click(screen, menu_btn.rect.center)
    assert screen.next_screen() == "MENU"


def test_old_maid_full_playthrough_reaches_game_over_and_returns_to_menu(surface):
    screen = OldMaidScreen(WINDOW_SIZE, Difficulty.EASY, lambda: "MENU")
    steps = 0
    while not screen.game.game_over and steps < MAX_STEPS:
        _drain_ai_turns(screen, "_waiting_for_ai")
        screen.draw(surface)
        if screen.game.game_over:
            break
        if screen._ai_hand_rect is not None and not screen.game.players["Fox"].hand.is_empty():
            click(screen, screen._ai_hand_rect.center)
        screen.update(0.0)
        steps += 1
    assert screen.game.game_over
    assert steps < MAX_STEPS

    screen.draw(surface)
    assert len(screen._end_buttons) == 2
    menu_btn = screen._end_buttons[1]
    click(screen, menu_btn.rect.center)
    assert screen.next_screen() == "MENU"


def test_memory_full_playthrough_reaches_game_over_and_returns_to_menu(surface):
    screen = MemoryScreen(WINDOW_SIZE, Difficulty.EASY, lambda: "MENU")
    steps = 0
    while not screen.game.game_over and steps < MAX_STEPS:
        _drain_ai_turns(screen, "_locked")
        screen.draw(surface)
        if screen.game.game_over:
            break
        if not screen.game.is_ai_turn() and screen._tile_rects:
            unflipped = screen.game.unflipped_positions()
            first = unflipped[0]
            partner = next(
                (
                    i
                    for i in unflipped
                    if i != first and screen.game.board[i].matches_rank(screen.game.board[first])
                ),
                unflipped[1] if len(unflipped) > 1 else None,
            )
            rects = dict(screen._tile_rects)
            click(screen, rects[first].center)
            screen.update(0.0)
            if partner is not None and not screen._locked:
                click(screen, rects[partner].center)
        screen.update(0.0)
        steps += 1
    assert screen.game.game_over
    assert steps < MAX_STEPS

    # game.game_over can flip True (e.g. inside take_ai_turn) before the
    # screen's own delayed reveal/finish callback chain has run far enough
    # to populate _end_buttons -- drain any trailing scheduled callback
    # before checking for them.
    _drain_ai_turns(screen, "_locked")
    screen.draw(surface)
    assert len(screen._end_buttons) == 2
    menu_btn = screen._end_buttons[1]
    click(screen, menu_btn.rect.center)
    assert screen.next_screen() == "MENU"


def test_letter_match_full_playthrough_reaches_completion_and_returns_to_menu(surface):
    screen = LetterMatchScreen(WINDOW_SIZE, lambda: "MENU")
    steps = 0
    while not screen.game.game_over and steps < MAX_STEPS:
        _drain_ai_turns(screen, "_locked")
        screen.draw(surface)
        if screen.game.game_over:
            break
        unflipped = screen.game.unflipped_positions()
        if len(unflipped) >= 2 and not screen._locked:
            first = unflipped[0]
            partner = next(
                i
                for i in unflipped
                if i != first
                and screen.game.board[i].letter == screen.game.board[first].letter
                and screen.game.board[i].is_upper != screen.game.board[first].is_upper
            )
            rects = dict(screen._tile_rects)
            click(screen, rects[first].center)
            screen.update(0.0)
            click(screen, rects[partner].center)
        screen.update(0.0)
        steps += 1
    assert screen.game.game_over
    assert steps < MAX_STEPS

    # The final match's celebratory confetti/on-complete callback is
    # scheduled with a short delay, which can outlive the loop above.
    _drain_ai_turns(screen, "_locked")
    screen.draw(surface)
    assert len(screen._end_buttons) == 2
    menu_btn = screen._end_buttons[1]
    click(screen, menu_btn.rect.center)
    assert screen.next_screen() == "MENU"


def test_restart_button_creates_a_fresh_playable_screen(surface):
    screen = GoFishScreen(WINDOW_SIZE, Difficulty.EASY, lambda: "MENU")
    # Force game over cheaply rather than replaying a full game.
    screen.game.game_over = True
    screen.game.winner = None
    screen._on_game_over()
    screen.draw(surface)
    play_again_btn = screen._end_buttons[0]
    click(screen, play_again_btn.rect.center)
    new_screen = screen.next_screen()
    assert isinstance(new_screen, GoFishScreen)
    assert not new_screen.game.game_over
