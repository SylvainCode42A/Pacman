"""Rendering layer for Pac-Man."""

from __future__ import annotations

from typing import Dict, List, Tuple

import pygame

from entities.ghost import Ghost, GhostMode
from entities.pickups import Pickup
from maze.maze_model import (
    Maze,
    NORTH_BIT,
    EAST_BIT,
    SOUTH_BIT,
    WEST_BIT,
)

WALL_COLOR = (33, 33, 176)
FLOOR_COLOR = (5, 5, 5)

PACGUM_COLOR = (255, 222, 130)
SUPER_PACGUM_COLOR = (255, 120, 120)

PLAYER_COLOR = (255, 221, 0)

GHOST_COLORS = {
    "Blinky": (220, 40, 40),
    "Pinky": (255, 153, 210),
    "Inky": (110, 220, 255),
    "Clyde": (255, 170, 60),
}

FRIGHTENED_COLOR = (60, 60, 220)
EATEN_COLOR = (200, 200, 200)

TEXT_COLOR = (255, 255, 255)
DIM_TEXT_COLOR = (170, 170, 170)
ACCENT_COLOR = (255, 221, 0)


class Renderer:
    """Draw the maze, pickups, player and ghosts."""

    def __init__(self, cell_size: int) -> None:
        """Initialize renderer fonts and cell size."""
        self.cell_size = cell_size

        pygame.font.init()

        self.font_small = pygame.font.SysFont(
            "consolas",
            16,
        )
        self.font_medium = pygame.font.SysFont(
            "consolas",
            24,
        )
        self.font_large = pygame.font.SysFont(
            "consolas",
            40,
        )

    def maze_pixel_size(self, maze: Maze) -> Tuple[int, int]:
        """Return the pixel size of the maze."""
        return (
            maze.width * self.cell_size,
            maze.height * self.cell_size,
        )

    def draw_maze(
        self,
        surface: pygame.Surface,
        maze: Maze,
        offset: Tuple[int, int],
    ) -> None:
        """Draw the maze using A-Maze-ing wall bitmasks."""

        ox, oy = offset

        surface.fill(FLOOR_COLOR)

        wall_width = max(2, self.cell_size // 10)

        for y in range(maze.height):
            for x in range(maze.width):
                cell = maze.get_cell(x, y)

                left = ox + x * self.cell_size
                top = oy + y * self.cell_size

                right = left + self.cell_size
                bottom = top + self.cell_size

                # North wall
                if cell & NORTH_BIT:
                    pygame.draw.line(
                        surface,
                        WALL_COLOR,
                        (left, top),
                        (right, top),
                        wall_width,
                    )

                # East wall
                if cell & EAST_BIT:
                    pygame.draw.line(
                        surface,
                        WALL_COLOR,
                        (right, top),
                        (right, bottom),
                        wall_width,
                    )

                # South wall
                if cell & SOUTH_BIT:
                    pygame.draw.line(
                        surface,
                        WALL_COLOR,
                        (left, bottom),
                        (right, bottom),
                        wall_width,
                    )

                # West wall
                if cell & WEST_BIT:
                    pygame.draw.line(
                        surface,
                        WALL_COLOR,
                        (left, top),
                        (left, bottom),
                        wall_width,
                    )

    def draw_pickups(
        self,
        surface: pygame.Surface,
        pickups: Dict[Tuple[int, int], Pickup],
        offset: Tuple[int, int],
    ) -> None:
        """Draw Pac-Gums and Super Pac-Gums."""

        ox, oy = offset

        for (x, y), pickup in pickups.items():
            cx = (
                ox
                + x * self.cell_size
                + self.cell_size // 2
            )

            cy = (
                oy
                + y * self.cell_size
                + self.cell_size // 2
            )

            if pickup.is_super:
                radius = max(4, self.cell_size // 5)
                color = SUPER_PACGUM_COLOR
            else:
                radius = max(2, self.cell_size // 10)
                color = PACGUM_COLOR

            pygame.draw.circle(
                surface,
                color,
                (cx, cy),
                radius,
            )

    def draw_player(
        self,
        surface: pygame.Surface,
        x: float,
        y: float,
        offset: Tuple[int, int],
    ) -> None:
        """Draw Pac-Man."""

        ox, oy = offset

        cx = int(
            ox
            + (x + 0.5) * self.cell_size
        )

        cy = int(
            oy
            + (y + 0.5) * self.cell_size
        )

        radius = int(
            self.cell_size * 0.4
        )

        pygame.draw.circle(
            surface,
            PLAYER_COLOR,
            (cx, cy),
            radius,
        )

    def draw_ghosts(
        self,
        surface: pygame.Surface,
        ghosts: List[Ghost],
        offset: Tuple[int, int],
    ) -> None:
        """Draw all ghosts."""

        ox, oy = offset

        for ghost in ghosts:
            cx = int(
                ox
                + (ghost.x + 0.5) * self.cell_size
            )

            cy = int(
                oy
                + (ghost.y + 0.5) * self.cell_size
            )

            radius = int(
                self.cell_size * 0.4
            )

            if ghost.mode == GhostMode.FRIGHTENED:
                color = FRIGHTENED_COLOR

            elif ghost.mode == GhostMode.EATEN:
                color = EATEN_COLOR

            else:
                color = GHOST_COLORS.get(
                    ghost.name,
                    (200, 200, 200),
                )

            pygame.draw.circle(
                surface,
                color,
                (cx, cy),
                radius,
            )

    def draw_text(
        self,
        surface: pygame.Surface,
        text: str,
        pos: Tuple[int, int],
        font: pygame.font.Font,
        color: Tuple[int, int, int] = TEXT_COLOR,
        center: bool = False,
    ) -> pygame.Rect:
        """Draw text and return its rectangle."""

        rendered = font.render(
            text,
            True,
            color,
        )

        rect = rendered.get_rect()

        if center:
            rect.center = pos
        else:
            rect.topleft = pos

        surface.blit(
            rendered,
            rect,
        )

        return rect
