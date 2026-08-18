"""One playable level: maze, pickups, ghosts and player start (VI.1)."""

from __future__ import annotations

import random
from dataclasses import dataclass, field
from typing import Dict, List, Tuple

from config.loader import GameConfig, LevelConfig
from entities.ghost import Ghost, GhostPersonality
from entities.pickups import Pickup
from maze.adapter import generate_maze
from maze.pathfinding import (
    distances_from,
    largest_open_region,
    nearest_in_region,
)
from maze.maze_model import Maze

# The four ghosts, each with its own chase logic and its own
# aggressiveness rank from 4 (most relentless) down to 1 (most timid).
# See entities/ghost.py for what each personality actually does.
GHOSTS: List[Tuple[str, GhostPersonality]] = [
    ("Blinky", GhostPersonality.HUNTER),
    ("Pinky", GhostPersonality.AMBUSHER),
    ("Inky", GhostPersonality.ERRATIC),
    ("Clyde", GhostPersonality.SHY),
]

GHOST_NAMES = [name for name, _ in GHOSTS]


@dataclass
class Level:
    """One fully assembled, playable level (maze, pickups, ghosts)."""

    index: int
    maze: Maze
    pickups: Dict[Tuple[int, int], Pickup]
    ghosts: List[Ghost]
    player_start: Tuple[int, int]
    time_limit: float
    total_pacgums: int = field(init=False)

    def __post_init__(self) -> None:
        """Record how many pacgums the level started with."""
        self.total_pacgums = sum(1 for p in self.pickups.values() if not p.is_super)

    def remaining_pacgums(self) -> int:
        """Count pacgums (not super-pacgums) not yet eaten."""
        return sum(1 for p in self.pickups.values() if not p.is_super)


def build_level(
    index: int,
    level_config: LevelConfig,
    config: GameConfig,
) -> Level:
    """Build level `index` (0-based). Level 0 uses the fixed seed (VI.1)."""
    if index == 0:
        seed = config.seed
    else:
        seed = random.SystemRandom().randint(0, 2**32 - 1)
    maze = generate_maze(level_config.width, level_config.height, seed)

    # Anchor everything inside the biggest connected area of the maze.
    # The assigned A-Maze-ing package walls off a decorative "42" pattern
    # right in the middle, which is where VI.1 puts the player, so taking
    # the geometric centre blindly would spawn Pac-Man inside a sealed
    # cell with no way out. Snapping to the nearest cell of the region
    # keeps the player "in the middle" while guaranteeing they can move.
    region = largest_open_region(maze)
    player_start = nearest_in_region(region, maze.center())
    corners = [nearest_in_region(region, c) for c in maze.corners()]

    # VI.1 / VI.4: "Pacgums (small dots) in most corridors". `config.pacgum`
    # corridors receive one, excluding the player's start cell and the 4
    # corners, which are reserved for the super-pacgums.
    #
    # They are spread evenly over the whole maze rather than packed
    # around the start: candidates are ordered by their distance from the
    # player, then one is taken every `step` positions. Walking that
    # ordered list outwards picks cells from every distance ring, so the
    # maze reads as uniformly dotted instead of showing a dense blob and
    # bare outskirts. Ordering on `(distance, cell)` also keeps the layout
    # reproducible for a given seed, which VI.1 needs for level 1.
    excluded = {player_start, *corners}
    distances = distances_from(maze, player_start)
    candidate_cells = sorted(
        (c for c in region if c not in excluded),
        key=lambda c: (distances[c], c),
    )

    pacgum_count = min(config.pacgum, len(candidate_cells))
    step = len(candidate_cells) / pacgum_count if pacgum_count else 1.0
    chosen_cells = [
        candidate_cells[min(int(i * step), len(candidate_cells) - 1)]
        for i in range(pacgum_count)
    ]

    pickups: Dict[Tuple[int, int], Pickup] = {}
    for cell in chosen_cells:
        pickups[cell] = Pickup(
            position=cell, points=config.points_per_pacgum, is_super=False
        )
    for corner in corners:
        pickups[corner] = Pickup(
            position=corner, points=config.points_per_super_pacgum, is_super=True
        )

    ghosts = [
        Ghost(
            name=GHOSTS[i % len(GHOSTS)][0],
            x=float(corner[0]),
            y=float(corner[1]),
            corner=corner,
            speed_cells_per_sec=float(config.ghost_speed),
            personality=GHOSTS[i % len(GHOSTS)][1],
        )
        for i, corner in enumerate(corners)
    ]

    return Level(
        index=index,
        maze=maze,
        pickups=pickups,
        ghosts=ghosts,
        player_start=player_start,
        time_limit=float(config.level_max_time),
    )
