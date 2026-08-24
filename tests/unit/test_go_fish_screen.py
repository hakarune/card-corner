"""Go Fish screen layout/hit-testing regression tests.

These cover a real bug an Auditor #1 pass found: overlapping hand cards
(gap < card width) were hit-tested in draw order, so a click on the
visually topmost card could resolve to an earlier, now-covered card
instead. Fixed by hit-testing in reverse draw order and by spacing cards
MIN_TOUCH_TARGET apart (wrapping to additional rows for large hands rather
than shrinking below that floor).
"""
from __future__ import annotations

import pygame

from core.ai.base import Difficulty
from core.card import Card, Rank, Suit
from games.go_fish.screen import GoFishScreen
from ui import theme


def make_screen_with_hand(surface, ranks: list[Rank]) -> GoFishScreen:
    screen = GoFishScreen((1024, 720), Difficulty.EASY, lambda: None)
    screen.game.players["You"].hand.cards = [Card(suit=Suit.CLUBS, rank=r) for r in ranks]
    screen.draw(surface)
    return screen


def click(screen, pos):
    screen.handle_event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=pos))


def test_hand_cards_within_a_row_are_spaced_at_least_touch_target_apart(surface):
    ranks = [Rank.TWO, Rank.THREE, Rank.FOUR, Rank.FIVE, Rank.SIX]
    screen = make_screen_with_hand(surface, ranks)
    xs = [rect.x for rect, _ in screen._card_rects]
    for a, b in zip(xs, xs[1:]):
        assert b - a >= theme.MIN_TOUCH_TARGET


def test_click_in_overlap_zone_resolves_to_the_topmost_later_drawn_card(surface):
    ranks = [Rank.TWO, Rank.THREE, Rank.FOUR]
    screen = make_screen_with_hand(surface, ranks)
    first_rect, first_rank = screen._card_rects[0]
    second_rect, second_rank = screen._card_rects[1]
    assert first_rank != second_rank

    # Card width (90) > gap (MIN_TOUCH_TARGET=88), so cards overlap by a
    # sliver; a click right at the second card's left edge lands inside
    # both rects. It must resolve to the second (topmost/later-drawn) card.
    overlap_x = second_rect.left + 1
    assert first_rect.collidepoint((overlap_x, first_rect.centery))
    assert second_rect.collidepoint((overlap_x, second_rect.centery))

    asked = []
    screen._human_ask = lambda rank: asked.append(rank)
    click(screen, (overlap_x, first_rect.centery))
    assert asked == [second_rank]


def test_large_hand_wraps_to_additional_rows_and_stays_within_the_window(surface):
    ranks = (list(Rank) * 2)[:15]
    screen = make_screen_with_hand(surface, ranks)
    rects = [rect for rect, _ in screen._card_rects]
    assert len(rects) == 15
    for rect in rects:
        assert rect.right <= screen.size[0]
        assert rect.bottom <= screen.size[1]
    # More than one row was actually used.
    assert len({rect.y for rect in rects}) > 1


def test_small_hand_still_uses_full_size_cards(surface):
    ranks = [Rank.TWO, Rank.THREE]
    screen = make_screen_with_hand(surface, ranks)
    for rect, _ in screen._card_rects:
        assert rect.height == 130


# -- interactive ask (spec §5: "less passive" AI-ask/human-ask flow) -------


def test_ai_ask_with_a_match_in_hand_waits_for_a_handover_click_not_an_instant_transfer(surface):
    screen = make_screen_with_hand(surface, [Rank.SEVEN, Rank.TWO])
    screen.game.players["Fox"].hand.cards = [Card(suit=Suit.HEARTS, rank=Rank.SEVEN)]
    screen.game.turn_index = screen.game.order.index("Fox")

    screen._ai_decide()
    assert screen._pending_ai_ask == Rank.SEVEN
    assert screen._awaiting_handover is True
    hand_before = list(screen.game.players["You"].hand.cards)

    # Clicking a non-matching card must not resolve the ask.
    screen.draw(surface)
    for rect, rank in screen._card_rects:
        if rank == Rank.TWO:
            click(screen, rect.center)
            break
    assert screen._awaiting_handover is True
    assert screen.game.players["You"].hand.cards == hand_before

    # Clicking the actual matching card hands it over and resolves the ask.
    for rect, rank in screen._card_rects:
        if rank == Rank.SEVEN:
            click(screen, rect.center)
            break
    assert screen._awaiting_handover is False
    assert screen.game.players["You"].hand.cards != hand_before


def test_ai_ask_with_no_match_auto_resolves_after_a_beat_with_nothing_to_click(surface):
    screen = make_screen_with_hand(surface, [Rank.TWO])
    screen.game.players["Fox"].hand.cards = [Card(suit=Suit.HEARTS, rank=Rank.SEVEN)]
    screen.game.turn_index = screen.game.order.index("Fox")

    screen._ai_decide()
    assert screen._pending_ai_ask == Rank.SEVEN
    assert screen._awaiting_handover is False
    assert screen._ai_resolve_timer > 0

    screen.update(screen._ai_resolve_timer + 0.01)
    assert screen._ai_resolve_timer == 0.0
    assert screen._pending_ai_ask is None


def test_human_ask_has_a_symmetric_delay_before_it_actually_transfers_cards(surface):
    screen = make_screen_with_hand(surface, [Rank.SEVEN])
    screen.game.players["Fox"].hand.cards = [Card(suit=Suit.HEARTS, rank=Rank.SEVEN)]
    screen.game.turn_index = screen.game.order.index("You")
    hand_before_ai = list(screen.game.players["Fox"].hand.cards)

    screen._human_ask(Rank.SEVEN)
    assert screen._waiting_for_human_resolve is True
    assert screen.game.players["Fox"].hand.cards == hand_before_ai  # not yet transferred

    screen.update(0.5)
    assert screen._waiting_for_human_resolve is False
    assert screen.game.players["Fox"].hand.cards != hand_before_ai
