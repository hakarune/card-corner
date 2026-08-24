"""Confirms each game screen actually calls audio.play_sfx at the moments
spec §3 requires (card click/selection, card movement/deal, match,
miss/go-fish, win, loss) rather than just that the audio module itself
works in isolation.
"""
from __future__ import annotations

import pygame
import pytest

from core.ai.base import Difficulty
from core.card import Card, Rank, Suit
from games.go_fish import screen as go_fish_screen
from games.letter_match import screen as letter_match_screen
from games.memory import screen as memory_screen
from games.old_maid import screen as old_maid_screen
from ui.theme import WINDOW_SIZE


class SfxSpy:
    def __init__(self):
        self.calls: list[str] = []

    def __call__(self, name):
        self.calls.append(name)


@pytest.fixture()
def spy_go_fish(monkeypatch):
    spy = SfxSpy()
    monkeypatch.setattr(go_fish_screen.audio, "play_sfx", spy)
    return spy


@pytest.fixture()
def spy_old_maid(monkeypatch):
    spy = SfxSpy()
    monkeypatch.setattr(old_maid_screen.audio, "play_sfx", spy)
    return spy


@pytest.fixture()
def spy_memory(monkeypatch):
    spy = SfxSpy()
    monkeypatch.setattr(memory_screen.audio, "play_sfx", spy)
    return spy


@pytest.fixture()
def spy_letter_match(monkeypatch):
    spy = SfxSpy()
    monkeypatch.setattr(letter_match_screen.audio, "play_sfx", spy)
    return spy


def test_go_fish_deal_sound_on_construction(spy_go_fish):
    go_fish_screen.GoFishScreen(WINDOW_SIZE, Difficulty.EASY, lambda: None)
    assert "card_move" in spy_go_fish.calls


def test_go_fish_human_ask_plays_select_then_match_or_miss(spy_go_fish):
    screen = go_fish_screen.GoFishScreen(WINDOW_SIZE, Difficulty.EASY, lambda: None)
    spy_go_fish.calls.clear()
    p1, p2 = go_fish_screen.HUMAN_NAME, go_fish_screen.AI_NAME
    screen.game.players[p1].hand.cards = [Card(suit=Suit.CLUBS, rank=Rank.SEVEN)]
    screen.game.players[p2].hand.cards = [Card(suit=Suit.HEARTS, rank=Rank.SEVEN)]
    screen.game.turn_index = screen.game.order.index(p1)

    screen._human_ask(Rank.SEVEN)
    assert spy_go_fish.calls[0] == "card_select"
    screen.update(go_fish_screen.HUMAN_ASK_RESOLVE_DELAY)  # symmetric ask-then-resolve beat

    assert "match" in spy_go_fish.calls


def test_go_fish_win_and_loss_sounds(spy_go_fish):
    screen = go_fish_screen.GoFishScreen(WINDOW_SIZE, Difficulty.EASY, lambda: None)
    spy_go_fish.calls.clear()
    screen.game.game_over = True
    screen.game.winner = go_fish_screen.HUMAN_NAME
    screen._on_game_over()
    assert "win" in spy_go_fish.calls

    spy_go_fish.calls.clear()
    screen.game.winner = go_fish_screen.AI_NAME
    screen._on_game_over()
    assert "loss" in spy_go_fish.calls


def test_old_maid_deal_sound_on_construction(spy_old_maid):
    old_maid_screen.OldMaidScreen(WINDOW_SIZE, Difficulty.EASY, lambda: None)
    assert "card_move" in spy_old_maid.calls


def test_old_maid_human_draw_plays_select(spy_old_maid):
    screen = old_maid_screen.OldMaidScreen(WINDOW_SIZE, Difficulty.EASY, lambda: None)
    spy_old_maid.calls.clear()
    p1, p2 = old_maid_screen.HUMAN_NAME, old_maid_screen.AI_NAME
    screen.game.players[p1].hand.cards = [Card(suit=Suit.CLUBS, rank=Rank.FIVE)]
    screen.game.players[p2].hand.cards = [Card(suit=Suit.HEARTS, rank=Rank.FIVE)]
    screen.game.turn_index = screen.game.order.index(p1)

    screen._human_draw()

    assert "card_select" in spy_old_maid.calls
    assert "match" in spy_old_maid.calls


def test_old_maid_non_match_plays_miss_for_human(spy_old_maid):
    screen = old_maid_screen.OldMaidScreen(WINDOW_SIZE, Difficulty.EASY, lambda: None)
    p1, p2 = old_maid_screen.HUMAN_NAME, old_maid_screen.AI_NAME
    screen.game.players[p1].hand.cards = [Card(suit=Suit.CLUBS, rank=Rank.FIVE)]
    # p2 holds 2 cards so drawing 1 away leaves them still active (not an
    # instant game-over), matching the moment the SFX actually needs to fire.
    screen.game.players[p2].hand.cards = [
        Card(suit=Suit.HEARTS, rank=Rank.NINE),
        Card(suit=Suit.SPADES, rank=Rank.NINE),
    ]
    screen.game.turn_index = screen.game.order.index(p1)

    spy_old_maid.calls.clear()
    screen._human_draw()
    assert "miss" in spy_old_maid.calls
    assert "match" not in spy_old_maid.calls


def test_old_maid_non_match_plays_miss_for_ai(spy_old_maid):
    screen = old_maid_screen.OldMaidScreen(WINDOW_SIZE, Difficulty.EASY, lambda: None)
    p1, p2 = old_maid_screen.HUMAN_NAME, old_maid_screen.AI_NAME
    screen.game.players[p2].hand.cards = [Card(suit=Suit.CLUBS, rank=Rank.THREE)]
    screen.game.players[p1].hand.cards = [
        Card(suit=Suit.HEARTS, rank=Rank.NINE),
        Card(suit=Suit.SPADES, rank=Rank.NINE),
    ]
    screen.game.turn_index = screen.game.order.index(p2)

    spy_old_maid.calls.clear()
    screen._run_ai_turn()
    assert "miss" in spy_old_maid.calls
    assert "match" not in spy_old_maid.calls


def test_old_maid_win_and_loss_sounds(spy_old_maid):
    screen = old_maid_screen.OldMaidScreen(WINDOW_SIZE, Difficulty.EASY, lambda: None)
    spy_old_maid.calls.clear()
    screen.game.game_over = True
    screen.game.loser = old_maid_screen.AI_NAME  # human wins
    screen._on_game_over()
    assert "win" in spy_old_maid.calls

    spy_old_maid.calls.clear()
    screen.game.loser = old_maid_screen.HUMAN_NAME  # human loses
    screen._on_game_over()
    assert "loss" in spy_old_maid.calls


def test_memory_human_click_plays_select_then_match_or_miss(spy_memory):
    screen = memory_screen.MemoryScreen(WINDOW_SIZE, Difficulty.EASY, lambda: None)
    spy_memory.calls.clear()
    pos0_rank = screen.game.board[0].rank
    match_pos = next(
        i for i in range(1, len(screen.game.board)) if screen.game.board[i].rank == pos0_rank
    )

    screen._human_click(0)
    assert spy_memory.calls == ["card_select"]
    screen._human_click(match_pos)
    assert "card_select" in spy_memory.calls
    assert "match" in spy_memory.calls


def test_memory_win_and_loss_sounds(spy_memory):
    screen = memory_screen.MemoryScreen(WINDOW_SIZE, Difficulty.EASY, lambda: None)
    spy_memory.calls.clear()
    screen.game.players[memory_screen.HUMAN_NAME].score = 5
    screen.game.players[memory_screen.AI_NAME].score = 1
    screen._on_game_over()
    assert "win" in spy_memory.calls

    spy_memory.calls.clear()
    screen.game.players[memory_screen.HUMAN_NAME].score = 1
    screen.game.players[memory_screen.AI_NAME].score = 5
    screen._on_game_over()
    assert "loss" in spy_memory.calls


def test_letter_match_select_match_and_miss_sounds(spy_letter_match):
    screen = letter_match_screen.LetterMatchScreen(WINDOW_SIZE, lambda: None)
    first = 0
    match_pos = next(
        i
        for i in range(1, len(screen.game.board))
        if screen.game.board[i].letter == screen.game.board[first].letter
        and screen.game.board[i].is_upper != screen.game.board[first].is_upper
    )
    miss_pos = next(
        i
        for i in range(1, len(screen.game.board))
        if i != match_pos and screen.game.board[i].letter != screen.game.board[first].letter
    )

    screen._click(first)
    assert spy_letter_match.calls == ["card_select"]

    screen._click(miss_pos)
    assert "miss" in spy_letter_match.calls
    screen.update(5.0)  # let the post-miss resolve-pause lock clear

    spy_letter_match.calls.clear()
    screen._click(first)
    screen._click(match_pos)
    assert "match" in spy_letter_match.calls


def test_letter_match_completion_plays_win_sound(spy_letter_match):
    screen = letter_match_screen.LetterMatchScreen(WINDOW_SIZE, lambda: None)
    screen._on_complete()
    assert "win" in spy_letter_match.calls


def test_button_clicks_play_button_sound(monkeypatch, surface):
    from ui import widgets

    spy = SfxSpy()
    monkeypatch.setattr(widgets.audio, "play_sfx", spy)
    clicked = []
    btn = widgets.Button((10, 10, 100, 40), "Go", lambda: clicked.append(1))
    btn.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(50, 30)))
    assert clicked == [1]
    assert "button" in spy.calls
