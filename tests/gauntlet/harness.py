"""Shared helpers for the AI-vs-AI self-play gauntlet (spec §7.2): report
writing and per-game "no illegal state" invariant checks. This module
contains no test functions itself.
"""
from __future__ import annotations

import json
from pathlib import Path

from core.card import Card
from games.go_fish.game import GoFishGame
from games.memory.game import MemoryGame
from games.old_maid.game import OldMaidGame

REPORTS_DIR = Path(__file__).parent / "reports"


def write_report(name: str, data: dict) -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    path = REPORTS_DIR / f"{name}.json"
    path.write_text(json.dumps(data, indent=2, default=str))


def go_fish_legal_state(game: GoFishGame) -> bool:
    """No card duplicated or lost across hands/stock/books; no more than 26
    books (pairs, not 4-of-a-kind -- see games/go_fish/game.py's docstring)
    claimed in total.
    """
    live: list[Card] = list(game.stock)
    for p in game.players.values():
        live.extend(p.hand.cards)
    if len(live) != len(set(live)):
        return False
    total_books = sum(len(p.books) for p in game.players.values())
    if total_books > 26:
        return False
    total = len(live) + 2 * total_books
    return total == 52


def old_maid_legal_state(game: OldMaidGame) -> bool:
    live: list[Card] = []
    for p in game.players.values():
        live.extend(p.hand.cards)
    if len(live) != len(set(live)):
        return False
    total = len(live) + 2 * sum(len(p.books) for p in game.players.values())
    return total == 49


def memory_legal_state(game: MemoryGame) -> bool:
    if len(game.matched) > len(game.board):
        return False
    total_pairs_found = sum(len(p.books) for p in game.players.values())
    return total_pairs_found == len(game.matched) // 2
