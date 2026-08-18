"""In-game HUD, pause menu, end screens and name entry (VI.8)."""

from __future__ import annotations

import pygame

from game.cheat import CheatState
from ui.renderer import ACCENT_COLOR, DIM_TEXT_COLOR, Renderer, TEXT_COLOR


def draw_ready_overlay(surface: pygame.Surface, renderer: Renderer) -> None:
    """Draw the brief "READY!" freeze shown before gameplay starts."""
    center = surface.get_rect().center
    renderer.draw_text(
        surface,
        "READY!",
        center,
        renderer.font_large,
        ACCENT_COLOR,
        center=True,
    )


def draw_hud(
    surface: pygame.Surface,
    renderer: Renderer,
    score: int,
    lives: int,
    level_number: int,
    total_levels: int,
    time_left: float,
    hud_rect: pygame.Rect,
) -> None:
    """Draw the always-visible HUD bar: score, lives, level and time."""
    pygame.draw.rect(surface, (15, 15, 15), hud_rect)
    y = hud_rect.top + 8
    renderer.draw_text(
        surface, f"Score: {score}", (hud_rect.left + 12, y), renderer.font_small
    )
    renderer.draw_text(
        surface,
        f"Lives: {lives}",
        (hud_rect.left + 12, y + 22),
        renderer.font_small,
    )
    renderer.draw_text(
        surface,
        f"Level: {level_number}/{total_levels}",
        (hud_rect.centerx - 70, y),
        renderer.font_small,
    )
    renderer.draw_text(
        surface,
        f"Time: {max(0, int(time_left))}s",
        (hud_rect.centerx - 70, y + 22),
        renderer.font_small,
    )


def draw_cheat_legend(
    surface: pygame.Surface, renderer: Renderer, cheat: CheatState, rect: pygame.Rect
) -> None:
    """Draw the always-visible cheat-mode legend with each cheat's state."""
    def _state(active: bool) -> str:
        return "ON" if active else "off"

    # Kept to three compact lines so the legend always fits inside the HUD
    # bar and never overlaps the maze drawn underneath it.
    lines = [
        "-- CHEATS --",
        f"[Z] skip   [E] freeze:{_state(cheat.ghosts_frozen)}"
        f"   [I] invinc:{_state(cheat.invincible)}",
        f"[L] +1 life   [P] speed x2:{_state(cheat.speed_boost)}",
    ]
    y = rect.top + 4
    for index, line in enumerate(lines):
        color = ACCENT_COLOR if index == 0 else DIM_TEXT_COLOR
        renderer.draw_text(
            surface, line, (rect.right - 400, y), renderer.font_small, color
        )
        y += 17


def draw_pause_menu(surface: pygame.Surface, renderer: Renderer, selected: int) -> None:
    """Draw the pause overlay with Resume / Return-to-menu options."""
    overlay = pygame.Surface(surface.get_size(), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))
    center = surface.get_rect().center
    renderer.draw_text(
        surface, "PAUSE", (center[0], center[1] - 60), renderer.font_large,
        ACCENT_COLOR, center=True,
    )
    options = ["Resume the game", "Return to the main menu"]
    for i, option in enumerate(options):
        color = ACCENT_COLOR if i == selected else TEXT_COLOR
        renderer.draw_text(
            surface,
            option,
            (center[0], center[1] + i * 34),
            renderer.font_medium,
            color,
            center=True,
        )


def draw_end_screen(
    surface: pygame.Surface,
    renderer: Renderer,
    victory: bool,
    score: int,
) -> None:
    """Draw the Game Over or Victory screen with the final score."""
    surface.fill((0, 0, 0))
    center = surface.get_rect().center
    title = "VICTORY!" if victory else "GAME OVER"
    color = ACCENT_COLOR if victory else (220, 60, 60)
    renderer.draw_text(
        surface, title, (center[0], center[1] - 80), renderer.font_large, color,
        center=True,
    )
    if victory:
        renderer.draw_text(
            surface,
            "Every level cleared, congratulations!",
            (center[0], center[1] - 40),
            renderer.font_small,
            TEXT_COLOR,
            center=True,
        )
    renderer.draw_text(
        surface,
        f"Final score: {score}",
        (center[0], center[1]),
        renderer.font_medium,
        TEXT_COLOR,
        center=True,
    )
    renderer.draw_text(
        surface,
        "Enter to continue",
        (center[0], center[1] + 60),
        renderer.font_small,
        DIM_TEXT_COLOR,
        center=True,
    )


def draw_enter_name(
    surface: pygame.Surface,
    renderer: Renderer,
    current_name: str,
    score: int,
    is_highscore: bool = True,
) -> None:
    """Draw the name-entry prompt shown after a Game Over or a Victory."""
    # `is_highscore` only changes the headline: V.5 asks for the name in
    # both cases, whether or not the score reaches the top 10.
    surface.fill((0, 0, 0))
    center = surface.get_rect().center
    title = "New highscore!" if is_highscore else "Save your score"
    renderer.draw_text(
        surface,
        title,
        (center[0], center[1] - 80),
        renderer.font_medium,
        ACCENT_COLOR,
        center=True,
    )
    renderer.draw_text(
        surface,
        f"Score: {score}",
        (center[0], center[1] - 40),
        renderer.font_small,
        TEXT_COLOR,
        center=True,
    )
    renderer.draw_text(
        surface,
        f"Name: {current_name}_",
        (center[0], center[1]),
        renderer.font_medium,
        TEXT_COLOR,
        center=True,
    )
    renderer.draw_text(
        surface,
        "(alphanumeric, 10 characters max, Enter to confirm)",
        (center[0], center[1] + 40),
        renderer.font_small,
        DIM_TEXT_COLOR,
        center=True,
    )
