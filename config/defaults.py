"""Default configuration values, used to clamp any invalid key (V.2)."""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

MIN_LEVELS = 10  # Ref VI.7 : "The game consists of multiple levels (at least 10)."

# Bounds applied to every level's dimensions. The lower bound guarantees
# room for a player start, 4 corners and a few corridors; the upper bound
# protects against a config given at defense time asking for an absurd
# maze (V.3: "The game configuration will be updated during the defense"),
# which would otherwise hang or exhaust memory inside the generator.
MIN_LEVEL_DIMENSION = 5
MAX_LEVEL_DIMENSION = 99

# Accepted spellings for the list of levels. V.2 lists the suggested key
# as "level array of multiple levels" - singular - while the natural name
# for a list is plural, so both are read. V.3 warns that "the game
# configuration will be updated during the defense", and a config written
# from the subject's own wording must not be silently ignored.
LEVELS_KEYS: Tuple[str, ...] = ("levels", "level")

DEFAULT_LEVEL: Dict[str, int] = {"width": 13, "height": 13}

# Every level uses the same 13x13 maze; what changes from one level to the
# next is the maze itself, regenerated with a new random seed (VI.1).
DEFAULT_LEVELS: List[Dict[str, int]] = [
    dict(DEFAULT_LEVEL) for _ in range(MIN_LEVELS)
]

DEFAULT_CONFIG: Dict[str, Any] = {
    "highscore_filename": "highscores.json",
    "levels": DEFAULT_LEVELS,
    "lives": 3,
    # Number of pacgums placed per level. A 13x13 maze offers 164 usable
    # corridors, so 84 covers a bit over half of them - "most corridors"
    # as VI.1 and VI.4 require - spread evenly across the whole maze.
    "pacgum": 84,
    "points_per_pacgum": 10,
    "points_per_super_pacgum": 50,
    "points_per_ghost": 200,
    "seed": 42,
    "level_max_time": 90,
    "cell_size": 24,
    # Fullscreen by default, which is what an arcade game wants. Set it to
    # false for a resizable window, which is friendlier when the game is
    # downloaded from a store page: the player can then just close the
    # window instead of walking back through the menus.
    "fullscreen": True,
    # Speeds are tied to `level_max_time`: clearing the 84 spread pacgums
    # of a 13x13 maze takes about 190 moves, so 6 cells per second leaves
    # roughly 45 s of margin inside the 90 s limit, detours and dodging
    # included. The player is also deliberately faster than any ghost, so
    # escaping is always possible; ghosts then differ further by
    # personality (see entities/ghost.py).
    "player_speed": 6,
    "ghost_speed": 4,
    "frightened_duration": 8,
    "ghost_respawn_delay": 7,
}

# Keys that must be a non-negative int, with the default used as a clamp target.
INT_KEYS: List[str] = [
    "lives",
    "pacgum",
    "points_per_pacgum",
    "points_per_super_pacgum",
    "points_per_ghost",
    "seed",
    "level_max_time",
    "cell_size",
    "player_speed",
    "ghost_speed",
    "frightened_duration",
    "ghost_respawn_delay",
]
