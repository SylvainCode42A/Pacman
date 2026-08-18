"""Internal maze model, using A-Maze-ing's own wall-bitmask grid."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

# A-Maze-ing wall bits:
# N = 1
# E = 2
# S = 4
# W = 8

NORTH = (0, -1)
SOUTH = (0, 1)
EAST = (1, 0)
WEST = (-1, 0)

DIRECTIONS = (NORTH, SOUTH, EAST, WEST)

NORTH_BIT = 1
EAST_BIT = 2
SOUTH_BIT = 4
WEST_BIT = 8


@dataclass
class Maze:
    """Maze whose cells hold the A-Maze-ing bitmask of their closed walls."""

    width: int
    height: int
    grid: List[List[int]]

    def is_inside(self, x: int, y: int) -> bool:
        """Return True if a coordinate is inside the maze."""
        return 0 <= x < self.width and 0 <= y < self.height

    def get_cell(self, x: int, y: int) -> int:
        """Return the A-Maze-ing bitmask of a cell."""
        if not self.is_inside(x, y):
            return 15
        return self.grid[y][x]

    def has_wall(self, x: int, y: int, direction: Tuple[int, int]) -> bool:
        """Return True if the requested direction is blocked."""
        if not self.is_inside(x, y):
            return True

        dx, dy = direction

        if dx == 0 and dy == -1:
            bit = NORTH_BIT
        elif dx == 1 and dy == 0:
            bit = EAST_BIT
        elif dx == 0 and dy == 1:
            bit = SOUTH_BIT
        elif dx == -1 and dy == 0:
            bit = WEST_BIT
        else:
            return True

        return bool(self.get_cell(x, y) & bit)

    def can_move(self, x: int, y: int, dx: int, dy: int) -> bool:
        """Return True if movement from one cell to another is possible."""
        nx = x + dx
        ny = y + dy

        if not self.is_inside(nx, ny):
            return False

        direction = (dx, dy)

        # Check the wall of the current cell.
        if self.has_wall(x, y, direction):
            return False

        # Also check the opposite wall of the destination.
        opposite = (-dx, -dy)
        if self.has_wall(nx, ny, opposite):
            return False

        return True

    def is_open(self, x: int, y: int) -> bool:
        """Return True when the cell exists and can contain an entity."""
        return self.is_inside(x, y)

    @property
    def open_cells(self) -> List[Tuple[int, int]]:
        """Return every playable cell."""
        return [
            (x, y)
            for y in range(self.height)
            for x in range(self.width)
        ]

    def neighbours(self, x: int, y: int) -> List[Tuple[int, int]]:
        """Return cells directly reachable from the given cell."""
        result: List[Tuple[int, int]] = []

        for dx, dy in DIRECTIONS:
            if self.can_move(x, y, dx, dy):
                result.append((x + dx, y + dy))

        return result

    def nearest_open_cell(self, x: int, y: int) -> Tuple[int, int]:
        """Return the closest valid cell to the requested position."""
        if self.is_inside(x, y):
            return x, y

        x = max(0, min(self.width - 1, x))
        y = max(0, min(self.height - 1, y))

        return x, y

    def center(self) -> Tuple[int, int]:
        """Return the cell closest to the center of the maze."""
        return self.nearest_open_cell(
            self.width // 2,
            self.height // 2,
        )

    def corners(self) -> List[Tuple[int, int]]:
        """Return one valid cell near each corner."""
        targets = [
            (0, 0),
            (self.width - 1, 0),
            (0, self.height - 1),
            (self.width - 1, self.height - 1),
        ]

        return [
            self.nearest_open_cell(x, y)
            for x, y in targets
        ]
