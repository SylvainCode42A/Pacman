"""BFS helpers over the maze grid: ghost pathfinding and level layout."""

from __future__ import annotations

from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from maze.maze_model import Maze

Cell = Tuple[int, int]


def bfs_next_step(maze: Maze, start: Cell, goal: Cell) -> Optional[Cell]:
    """Return the first cell to move to on a shortest path start->goal."""
    if start == goal:
        return start
    if not maze.is_open(*goal):
        return None

    visited = {start}
    came_from: Dict[Cell, Cell] = {}
    queue: "deque[Cell]" = deque([start])

    while queue:
        current = queue.popleft()
        if current == goal:
            break
        for neighbour in maze.neighbours(*current):
            if neighbour not in visited:
                visited.add(neighbour)
                came_from[neighbour] = current
                queue.append(neighbour)

    if goal not in came_from and goal != start:
        return None

    # Walk the path back from goal to start to find the first step.
    step = goal
    while came_from.get(step) != start and step in came_from:
        step = came_from[step]
    return step


def distances_from(maze: Maze, start: Cell) -> Dict[Cell, int]:
    """Return the number of moves from `start` to every reachable cell."""
    distances: Dict[Cell, int] = {start: 0}
    queue: "deque[Cell]" = deque([start])

    while queue:
        current = queue.popleft()
        for neighbour in maze.neighbours(*current):
            if neighbour not in distances:
                distances[neighbour] = distances[current] + 1
                queue.append(neighbour)

    return distances


def largest_open_region(maze: Maze) -> Set[Cell]:
    """Return the biggest set of mutually reachable cells.

    A maze is not necessarily one connected area: the assigned A-Maze-ing
    package seals a decorative "42" pattern in the middle, exactly where
    VI.1 asks the player to start. Everything a level places is anchored
    inside this region, so nothing can spawn walled off.
    """
    seen: Set[Cell] = set()
    best: Set[Cell] = set()

    for start in maze.open_cells:
        if start in seen:
            continue
        region: Set[Cell] = {start}
        queue: "deque[Cell]" = deque([start])
        while queue:
            current = queue.popleft()
            for neighbour in maze.neighbours(*current):
                if neighbour not in region:
                    region.add(neighbour)
                    queue.append(neighbour)
        seen |= region
        if len(region) > len(best):
            best = region

    return best


def nearest_in_region(region: Set[Cell], target: Cell) -> Cell:
    """Return the cell of `region` closest to `target` as the crow flies."""
    return min(
        region,
        key=lambda c: ((c[0] - target[0]) ** 2 + (c[1] - target[1]) ** 2, c),
    )


def farthest_neighbour(maze: Maze, current: Cell, from_cell: Cell) -> Cell:
    """Return the reachable neighbour furthest from `from_cell` (VI.3)."""
    candidates: List[Cell] = maze.neighbours(*current) or [current]
    return max(
        candidates,
        key=lambda c: (c[0] - from_cell[0]) ** 2 + (c[1] - from_cell[1]) ** 2,
    )
