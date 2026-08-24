"""Main menu, instructions and highscores screens (VI.8).

The Instructions screen is also the in-package documentation required by
chapter VII: it ships inside the build by construction and documents the
controls, the rules and every configuration key.
"""

from __future__ import annotations

from typing import List, Sequence, Tuple

import pygame

from config.loader import GameConfig
from game.highscore import HighscoreEntry
from ui.renderer import ACCENT_COLOR, DIM_TEXT_COLOR, Renderer, TEXT_COLOR

MAIN_MENU_OPTIONS = ["Start Game", "Highscores", "Instructions", "Exit"]

# Vertical spacing between two lines of the Instructions screen.
INSTRUCTIONS_LINE_HEIGHT = 22
INSTRUCTIONS_TOP = 110


def draw_main_menu(surface: pygame.Surface, renderer: Renderer, selected: int) -> None:
    """Draw the main menu (Start/Highscores/Instructions/Exit), VI.8."""
    surface.fill((0, 0, 0))
    center = surface.get_rect().center
    renderer.draw_text(
        surface, "PAC-MAN", (center[0], center[1] - 140), renderer.font_large,
        ACCENT_COLOR, center=True,
    )
    for i, option in enumerate(MAIN_MENU_OPTIONS):
        color = ACCENT_COLOR if i == selected else TEXT_COLOR
        prefix = "> " if i == selected else "  "
        renderer.draw_text(
            surface,
            f"{prefix}{option}",
            (center[0], center[1] - 30 + i * 36),
            renderer.font_medium,
            color,
            center=True,
        )
    renderer.draw_text(
        surface,
        "Arrows/WASD to navigate, Enter to confirm",
        (center[0], center[1] + 160),
        renderer.font_small,
        DIM_TEXT_COLOR,
        center=True,
    )


def _gameplay_lines(config: GameConfig) -> List[str]:
    """Return the left column: goal, controls, rules and cheat mode."""
    # Values are read from the loaded configuration rather than
    # hard-coded, so the screen always describes the game actually being
    # played, even with the config handed over at defense time (V.3).
    return [
        "History of the game:",
        "  A full recreation of the classic 1980 Pac-Man",
        "  arcade game in Python, built with an object-oriented,",
        "  modular architecture.",
        "",
        "Goal:",
        "  Eat every pacgum of each level without",
        "  getting caught by the ghosts.",
        f"  {len(config.levels)} levels, {config.lives} lives, "
        f"{config.level_max_time} s per level.",
        "",
        "Controls:",
        "  Arrows or WASD      move Pac-Man",
        "  Escape              pause / resume",
        "  Enter               confirm in menus",
        "  Backspace           erase a letter of your name",
        "",
        "The 4 ghosts:",
        "  Blinky     charges straight at you (fastest)",
        "  Pinky      aims ahead of you to cut you off",
        "  Inky       alternates chasing and wandering",
        "  Clyde      follows from afar, flees up close",
        "",
        "Rules:",
        f"  Pacgum              +{config.points_per_pacgum} points",
        f"  Super-pacgum        +{config.points_per_super_pacgum} points,"
        f" ghosts edible {config.frightened_duration} s",
        f"  Edible ghost        +{config.points_per_ghost} points,"
        " it returns to its corner",
        "  Normal ghost        you lose a life",
        "  Time out            you lose a life, level restarts",
        "  All pacgums eaten   next level",
        "",
        "Cheat mode (for peer review):",
        "  Z  skip the level         I  invincibility",
        "  E  freeze the ghosts      L  extra life",
        "  P  speed x2",
    ]


def _configuration_lines(config: GameConfig) -> List[str]:
    """Return the right column: configuration keys and highscore storage."""
    # This is what makes the Instructions screen satisfy chapter VII's
    # "minimal in-package instructions (controls, options, configuration)"
    # without shipping a separate documentation file alongside the build.
    return [
        "Configuration:",
        "  The game is launched with a JSON file:",
        "    python3 pac-man.py config.json",
        "  Comments # and // are accepted.",
        "  Any missing or invalid key falls back to",
        "  its default without ever crashing.",
        "",
        "  highscore_filename       score file",
        "  levels                   [{width, height}, ...]",
        f"  lives                    {config.lives}",
        f"  pacgum                   {config.pacgum} (cap)",
        f"  points_per_pacgum        {config.points_per_pacgum}",
        f"  points_per_super_pacgum  {config.points_per_super_pacgum}",
        f"  points_per_ghost         {config.points_per_ghost}",
        f"  seed                     {config.seed}",
        f"  level_max_time           {config.level_max_time}",
        f"  cell_size                {config.cell_size}",
        f"  fullscreen               {str(config.fullscreen).lower()}",
        f"  player_speed             {config.player_speed}",
        f"  ghost_speed              {config.ghost_speed}",
        f"  frightened_duration      {config.frightened_duration}",
        f"  ghost_respawn_delay      {config.ghost_respawn_delay}",
        "",
        "Highscores:",
        f"  Top 10 kept in {config.highscore_filename}.",
        "  Name: 10 alphanumeric characters max.",
        "",
        "Mazes:",
        "  Generated by the external A-Maze-ing package.",
    ]


def _draw_column(
    surface: pygame.Surface,
    renderer: Renderer,
    lines: Sequence[str],
    origin: Tuple[int, int],
) -> None:
    """Draw one column of the Instructions screen."""
    # An unindented line ending with ':' is a heading, drawn in the accent
    # colour; everything else is indented body text.
    x, y = origin
    for line in lines:
        is_heading = line.endswith(":") and not line.startswith(" ")
        color = ACCENT_COLOR if is_heading else TEXT_COLOR
        renderer.draw_text(surface, line, (x, y), renderer.font_small, color)
        y += INSTRUCTIONS_LINE_HEIGHT


def draw_instructions(
    surface: pygame.Surface, renderer: Renderer, config: GameConfig
) -> None:
    """Draw the Instructions screen: controls, rules and configuration."""
    surface.fill((0, 0, 0))
    width, height = surface.get_size()
    center_x = width // 2

    renderer.draw_text(
        surface, "INSTRUCTIONS", (center_x, 60), renderer.font_large,
        ACCENT_COLOR, center=True,
    )

    _draw_column(
        surface, renderer, _gameplay_lines(config), (60, INSTRUCTIONS_TOP)
    )
    _draw_column(
        surface, renderer, _configuration_lines(config),
        (center_x + 40, INSTRUCTIONS_TOP),
    )

    renderer.draw_text(
        surface,
        "Enter or Escape to go back to the menu",
        (center_x, height - 50),
        renderer.font_small,
        DIM_TEXT_COLOR,
        center=True,
    )


def draw_highscores(
    surface: pygame.Surface, renderer: Renderer, entries: List[HighscoreEntry]
) -> None:
    """Draw the top-10 highscore board (V.5, VI.8)."""
    surface.fill((0, 0, 0))
    center_x = surface.get_rect().centerx
    renderer.draw_text(
        surface, "HIGHSCORES", (center_x, 60), renderer.font_large, ACCENT_COLOR,
        center=True,
    )
    if not entries:
        renderer.draw_text(
            surface,
            "No score recorded yet.",
            (center_x, 140),
            renderer.font_small,
            DIM_TEXT_COLOR,
            center=True,
        )
    y = 130
    for i, entry in enumerate(entries):
        renderer.draw_text(
            surface,
            f"{i + 1:2d}. {entry.name:<10} {entry.score}",
            (center_x, y),
            renderer.font_medium,
            TEXT_COLOR,
            center=True,
        )
        y += 34
    renderer.draw_text(
        surface,
        "Enter or Escape to go back to the menu",
        (center_x, y + 20),
        renderer.font_small,
        DIM_TEXT_COLOR,
        center=True,
    )
