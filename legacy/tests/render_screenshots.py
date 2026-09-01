"""Ad-hoc visual QA script (not part of the pytest suite): renders each
screen to an offscreen surface and exports a PNG for human/auditor
inspection. Run headless with SDL_VIDEODRIVER=dummy.

    SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python tests/render_screenshots.py /path/to/out_dir
"""
from __future__ import annotations

import sys
from pathlib import Path

import pygame

from core.ai.base import Difficulty
from core.card import Card, Rank, Suit
from games.go_fish.screen import GoFishScreen
from games.letter_match.screen import LetterMatchScreen
from games.memory.screen import MemoryScreen
from games.old_maid.screen import OldMaidScreen
from ui.launcher import DifficultySelectScreen, LauncherScreen
from ui.theme import WINDOW_SIZE


def save(surface: pygame.Surface, out_dir: Path, name: str) -> None:
    path = out_dir / f"{name}.png"
    pygame.image.save(surface, str(path))
    print(f"wrote {path}")


def settle(screen, surface, frames=25, dt=0.05):
    """Advance past deal/reveal animation windows before capturing."""
    for _ in range(frames):
        screen.update(dt)
        screen.draw(surface)


def main() -> None:
    out_dir = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("screenshots")
    out_dir.mkdir(parents=True, exist_ok=True)

    pygame.init()
    surface = pygame.display.set_mode(WINDOW_SIZE)

    # -- Launcher & difficulty select ---------------------------------
    launcher = LauncherScreen(WINDOW_SIZE, lambda key: None)
    launcher.draw(surface)
    save(surface, out_dir, "01_launcher")

    diff = DifficultySelectScreen(WINDOW_SIZE, "Go Fish", (91, 155, 213), lambda d: None, lambda: None)
    diff.draw(surface)
    save(surface, out_dir, "02_difficulty_select")

    # -- Go Fish: mid-game and game-over ------------------------------
    gf = GoFishScreen(WINDOW_SIZE, Difficulty.MEDIUM, lambda: None)
    settle(gf, surface)
    save(surface, out_dir, "03_go_fish_midgame")

    gf_end = GoFishScreen(WINDOW_SIZE, Difficulty.MEDIUM, lambda: None)
    gf_end.game.game_over = True
    gf_end.game.winner = "You"
    gf_end._on_game_over()
    settle(gf_end, surface, frames=10)
    save(surface, out_dir, "04_go_fish_gameover_celebration")

    # -- Go Fish: large overlapping hand (touch-target check) --------
    gf_big = GoFishScreen(WINDOW_SIZE, Difficulty.MEDIUM, lambda: None)
    gf_big.game.players["You"].hand.cards = [
        Card(suit=s, rank=r) for r in list(Rank)[:7] for s in [Suit.CLUBS, Suit.HEARTS]
    ]
    settle(gf_big, surface)
    save(surface, out_dir, "05_go_fish_large_hand")

    # -- Old Maid: mid-game and game-over -----------------------------
    om = OldMaidScreen(WINDOW_SIZE, Difficulty.MEDIUM, lambda: None)
    settle(om, surface)
    save(surface, out_dir, "06_old_maid_midgame")

    om_end = OldMaidScreen(WINDOW_SIZE, Difficulty.MEDIUM, lambda: None)
    om_end.game.game_over = True
    om_end.game.loser = "Fox"
    om_end._on_game_over()
    settle(om_end, surface, frames=10)
    save(surface, out_dir, "07_old_maid_gameover_celebration")

    # -- Memory: mid-game (some revealed) and game-over ---------------
    mem = MemoryScreen(WINDOW_SIZE, Difficulty.MEDIUM, lambda: None)
    settle(mem, surface)
    mem._visible = {0, 1}
    mem.draw(surface)
    save(surface, out_dir, "08_memory_midgame")

    mem_end = MemoryScreen(WINDOW_SIZE, Difficulty.MEDIUM, lambda: None)
    mem_end.game.game_over = True
    mem_end._on_game_over()
    settle(mem_end, surface, frames=10)
    save(surface, out_dir, "09_memory_gameover_celebration")

    # -- Letter Match: mid-game and completion ------------------------
    lm = LetterMatchScreen(WINDOW_SIZE, lambda: None)
    settle(lm, surface)
    save(surface, out_dir, "10_letter_match_midgame")

    lm_end = LetterMatchScreen(WINDOW_SIZE, lambda: None)
    lm_end.game.game_over = True
    lm_end._on_complete()
    settle(lm_end, surface, frames=10)
    save(surface, out_dir, "11_letter_match_completion")

    pygame.quit()
    print("done")


if __name__ == "__main__":
    main()
