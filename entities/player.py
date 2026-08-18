"""Player entity: Pac-Man moving cell to cell, walls respected (VI.2)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple

from maze.maze_model import DIRECTIONS, Maze


@dataclass
class Player:
    """Pac-Man: position, lives, current and queued direction."""

    x: float
    y: float
    lives: int
    speed_cells_per_sec: float
    direction: Tuple[int, int] = (0, 0)
    queued_direction: Tuple[int, int] = (0, 0)
    _target: Tuple[int, int] = (0, 0)

    @property
    def cell(self) -> Tuple[int, int]:
        """Return the current grid cell."""
        return int(round(self.x)), int(round(self.y))

    def _is_aligned(self) -> bool:
        """Return True when Pac-Man is exactly on a grid cell."""
        return (
            abs(self.x - round(self.x)) < 1e-6
            and abs(self.y - round(self.y)) < 1e-6
        )

    def set_direction(self, direction: Tuple[int, int]) -> None:
        """Queue a movement direction, applied at the next cell centre."""
        if direction in DIRECTIONS or direction == (0, 0):
            self.queued_direction = direction

    def respawn(self, position: Tuple[int, int]) -> None:
        """Respawn Pac-Man at the given cell, stopped."""
        self.x = float(position[0])
        self.y = float(position[1])
        self.direction = (0, 0)
        self.queued_direction = (0, 0)
        self._target = position

    def update(self, maze: Maze, dt: float) -> None:
        """Move Pac-Man by `dt` seconds without ever crossing a wall."""
        # A new decision is only taken at the centre of a cell: the queued
        # direction is applied if that corridor is open, the current one is
        # dropped if it is now blocked, and the destination cell is then
        # frozen. Recomputing the target from the in-between float position
        # is what would let Pac-Man overshoot a cell and clip through a wall.
        if self._is_aligned():
            cx, cy = self.cell

            if self.queued_direction != (0, 0):
                qdx, qdy = self.queued_direction
                if maze.can_move(cx, cy, qdx, qdy):
                    self.direction = self.queued_direction

            if self.direction != (0, 0):
                dx, dy = self.direction
                if not maze.can_move(cx, cy, dx, dy):
                    self.direction = (0, 0)

            self._target = (cx + self.direction[0], cy + self.direction[1])

        if self.direction == (0, 0):
            self.x = float(round(self.x))
            self.y = float(round(self.y))
            return

        step = self.speed_cells_per_sec * dt
        self.x += self.direction[0] * step
        self.y += self.direction[1] * step

        # Snap exactly onto the target cell instead of drifting past it.
        tx, ty = self._target
        if self.direction[0] > 0 and self.x >= tx:
            self.x = float(tx)
        elif self.direction[0] < 0 and self.x <= tx:
            self.x = float(tx)
        if self.direction[1] > 0 and self.y >= ty:
            self.y = float(ty)
        elif self.direction[1] < 0 and self.y <= ty:
            self.y = float(ty)
