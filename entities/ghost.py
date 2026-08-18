"""Ghost entity and AI (VI.3).

VI.3 leaves the chase behaviour open, so each ghost gets its own logic
and its own aggressiveness rank, from 1 (most timid) to 4 (most
relentless). No two share the same one:

    4 - Blinky, HUNTER    paths straight at the player, and moves fastest
    3 - Pinky,  AMBUSHER  aims several cells ahead of the player
    2 - Inky,   ERRATIC   alternates chasing and wandering at random
    1 - Clyde,  SHY       chases from afar, but backs off when close

All four also alternate "scatter" and "chase" phases, driven by
`game/engine.py`: without it, four simultaneous chasers can seal both
ends of a corridor and make the game unwinnable regardless of skill.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Dict, Tuple

from maze.maze_model import Maze
from maze.pathfinding import bfs_next_step, farthest_neighbour


class GhostMode(Enum):
    """A ghost's current behavioral state (VI.3)."""

    CHASE = auto()
    FRIGHTENED = auto()
    EATEN = auto()


class GhostPersonality(Enum):
    """Per-ghost chase logic; the value is its aggressiveness rank."""

    SHY = 1
    ERRATIC = 2
    AMBUSHER = 3
    HUNTER = 4


# Speed multiplier applied on top of the configured `ghost_speed`, so a
# more aggressive ghost is also felt as more dangerous, not just aimed
# differently.
SPEED_BY_PERSONALITY: Dict[GhostPersonality, float] = {
    GhostPersonality.SHY: 0.85,
    GhostPersonality.ERRATIC: 0.95,
    GhostPersonality.AMBUSHER: 1.0,
    GhostPersonality.HUNTER: 1.1,
}

# How far ahead of the player the ambusher aims, in cells.
AMBUSH_LOOKAHEAD = 4

# How close the shy ghost lets the player get before backing off, in cells.
SHY_COMFORT_RADIUS = 5

# How long the erratic ghost keeps one behaviour before switching.
ERRATIC_SWITCH_SECONDS = 3.0

# Speed factors applied by mode, whatever the personality.
FRIGHTENED_SPEED_FACTOR = 0.6
EATEN_SPEED_FACTOR = 2.0


@dataclass
class Ghost:
    """One autonomous ghost: position, home corner, personality, mode."""

    name: str
    x: float
    y: float
    corner: Tuple[int, int]
    speed_cells_per_sec: float
    personality: GhostPersonality = GhostPersonality.HUNTER
    mode: GhostMode = GhostMode.CHASE
    frightened_time_left: float = 0.0
    respawn_time_left: float = 0.0
    direction: Tuple[int, int] = (0, 0)
    _target: Tuple[int, int] = (0, 0)
    _wander_target: Tuple[int, int] = (0, 0)
    _wander_time_left: float = field(default=ERRATIC_SWITCH_SECONDS)
    _wandering: bool = False

    @property
    def aggressiveness(self) -> int:
        """Return this ghost's rank, from 1 (most timid) to 4 (most eager)."""
        return self.personality.value

    @property
    def cell(self) -> Tuple[int, int]:
        """Nearest grid cell to the current (possibly fractional) position."""
        return int(round(self.x)), int(round(self.y))

    def _is_aligned(self) -> bool:
        """True when standing exactly on a grid cell (not mid-move)."""
        return abs(self.x - round(self.x)) < 1e-6 and abs(self.y - round(self.y)) < 1e-6

    def frighten(self, duration: float) -> None:
        """Make this ghost edible for `duration` seconds (VI.4)."""
        # No-op while eaten: it must keep heading home instead.
        if self.mode != GhostMode.EATEN:
            self.mode = GhostMode.FRIGHTENED
            self.frightened_time_left = duration

    def get_eaten(self, respawn_delay: float) -> None:
        """Send this ghost home; it resumes chasing after `respawn_delay`s."""
        self.mode = GhostMode.EATEN
        self.respawn_time_left = respawn_delay
        self.frightened_time_left = 0.0

    # ------------------------------------------------------------------ #
    # Per-personality chase logic
    # ------------------------------------------------------------------ #
    def _hunter_target(self, player_cell: Tuple[int, int]) -> Tuple[int, int]:
        """Aggressiveness 4 (Blinky): go straight at the player."""
        return player_cell

    def _ambusher_target(
        self,
        maze: Maze,
        player_cell: Tuple[int, int],
        player_direction: Tuple[int, int],
    ) -> Tuple[int, int]:
        """Aggressiveness 3 (Pinky): aim where the player is heading."""
        # Targets AMBUSH_LOOKAHEAD cells ahead so the ghost cuts corners
        # instead of trailing; plain chase if the player stands still.
        dx, dy = player_direction
        if (dx, dy) == (0, 0):
            return player_cell
        ahead = (
            player_cell[0] + dx * AMBUSH_LOOKAHEAD,
            player_cell[1] + dy * AMBUSH_LOOKAHEAD,
        )
        return maze.nearest_open_cell(*ahead)

    def _erratic_target(self, player_cell: Tuple[int, int]) -> Tuple[int, int]:
        """Aggressiveness 2 (Inky): chase, then wander, then chase again."""
        if self._wandering:
            return self._wander_target
        return player_cell

    def _shy_target(self, player_cell: Tuple[int, int]) -> Tuple[int, int]:
        """Aggressiveness 1 (Clyde): brave from afar, cowardly up close."""
        cx, cy = self.cell
        distance_sq = (cx - player_cell[0]) ** 2 + (cy - player_cell[1]) ** 2
        if distance_sq > SHY_COMFORT_RADIUS ** 2:
            return player_cell
        return self.corner

    def _pick_target(
        self,
        maze: Maze,
        player_cell: Tuple[int, int],
        scatter: bool,
        player_direction: Tuple[int, int] = (0, 0),
    ) -> Tuple[int, int]:
        """Choose the cell this ghost should path toward this tick."""
        if self.mode == GhostMode.EATEN:
            return self.corner
        if self.mode == GhostMode.FRIGHTENED:
            return farthest_neighbour(maze, self.cell, player_cell)
        if scatter:
            # Scatter phase: everyone heads home, so the four ghosts stop
            # converging on the player at once.
            return self.corner

        if self.personality is GhostPersonality.HUNTER:
            return self._hunter_target(player_cell)
        if self.personality is GhostPersonality.AMBUSHER:
            return self._ambusher_target(maze, player_cell, player_direction)
        if self.personality is GhostPersonality.ERRATIC:
            return self._erratic_target(player_cell)
        return self._shy_target(player_cell)

    def _update_wandering(self, maze: Maze, dt: float) -> None:
        """Advance the erratic ghost's chase/wander alternation."""
        if self.personality is not GhostPersonality.ERRATIC:
            return
        self._wander_time_left -= dt
        if self._wander_time_left > 0:
            return
        self._wandering = not self._wandering
        self._wander_time_left = ERRATIC_SWITCH_SECONDS
        if self._wandering:
            self._wander_target = random.choice(maze.open_cells)

    def _current_speed(self) -> float:
        """Return the speed to move at, given personality and mode."""
        speed = self.speed_cells_per_sec * SPEED_BY_PERSONALITY[self.personality]
        if self.mode == GhostMode.FRIGHTENED:
            return speed * FRIGHTENED_SPEED_FACTOR
        if self.mode == GhostMode.EATEN:
            return speed * EATEN_SPEED_FACTOR
        return speed

    # ------------------------------------------------------------------ #
    # Per-frame update
    # ------------------------------------------------------------------ #
    def update(
        self,
        maze: Maze,
        dt: float,
        player_cell: Tuple[int, int],
        respawn_delay: float,
        scatter: bool = False,
        player_direction: Tuple[int, int] = (0, 0),
    ) -> None:
        """Advance this ghost by `dt` seconds: AI target, then movement."""
        if self.mode == GhostMode.FRIGHTENED:
            self.frightened_time_left -= dt
            if self.frightened_time_left <= 0:
                self.mode = GhostMode.CHASE

        if self.mode == GhostMode.EATEN and self.cell == self.corner:
            self.respawn_time_left -= dt
            if self.respawn_time_left <= 0:
                self.mode = GhostMode.CHASE
            self.direction = (0, 0)
            self.x, self.y = self.corner
            return

        self._update_wandering(maze, dt)

        if self._is_aligned():
            cx, cy = self.cell
            target = self._pick_target(maze, player_cell, scatter, player_direction)
            next_cell = bfs_next_step(maze, (cx, cy), target)
            if next_cell is None or next_cell == (cx, cy):
                self.direction = (0, 0)
            else:
                self.direction = (next_cell[0] - cx, next_cell[1] - cy)
            # Frozen at the moment of leaving an aligned cell: recomputing
            # it from the in-between float position lets entities overshoot
            # a cell and clip through a wall.
            self._target = (cx + self.direction[0], cy + self.direction[1])

        if self.direction == (0, 0):
            self.x, self.y = float(round(self.x)), float(round(self.y))
            return

        step = self._current_speed() * dt
        self.x += self.direction[0] * step
        self.y += self.direction[1] * step
        tx, ty = self._target
        if self.direction[0] > 0 and self.x >= tx:
            self.x = tx
        elif self.direction[0] < 0 and self.x <= tx:
            self.x = tx
        if self.direction[1] > 0 and self.y >= ty:
            self.y = ty
        elif self.direction[1] < 0 and self.y <= ty:
            self.y = ty
