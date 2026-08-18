"""Adapter between the assigned A-Maze-ing package and Pac-Man (V.4).

The ONLY module of the project that talks to the external package.
Because V.4 says "your loader must adapt to their interface, not the
opposite", the lookup is deliberately tolerant: several import paths are
tried, the constructor is called through `inspect.signature` so only the
parameters it declares are passed, and the grid is read through whichever
accessor the class provides. There is no home-made fallback generator:
any failure becomes a single clear `MazeGenerationError`.
"""

from __future__ import annotations

import importlib
import inspect
import logging
import os
from typing import Any, Callable, Dict, List, Sequence, Tuple

from maze.maze_model import Maze

logger = logging.getLogger("pacman.maze")

# Escape hatch for the defense: `PACMAN_AMAZING_MODULE=their_package make run`
# forces one specific import path without touching a single line of code.
MODULE_ENV_VAR = "PACMAN_AMAZING_MODULE"

# Import paths tried in order. The package assigned to us is
# `mazegenerator` 2.1.0, pip-installed from the wheel at the repository
# root; the other names are kept so a differently-named A-Maze-ing
# package is still picked up without a code change.
CANDIDATE_MODULES: Tuple[str, ...] = (
    "mazegenerator",
    "mazegenerator.mazegenerator",
    "mazegen",
    "mazegen.generator",
    "a_maze_ing",
    "amazing",
    "amazing.mazegen",
    "amazing.mazegen.generator",
)

# Class names an A-Maze-ing package may expose.
CANDIDATE_CLASSES: Tuple[str, ...] = (
    "MazeGenerator",
    "Generator",
    "AMazeIng",
    "Maze",
)

# Accessors tried, in order, to read the generated grid out of an instance.
CANDIDATE_GRID_ACCESSORS: Tuple[str, ...] = (
    "get_grid",
    "grid",
    "to_grid",
    "get_maze",
    "maze",
)

# Constructor keyword aliases: our value -> names the package may use.
WIDTH_ALIASES: Tuple[str, ...] = ("width", "w", "cols", "columns", "x")
HEIGHT_ALIASES: Tuple[str, ...] = ("height", "h", "rows", "y")
SEED_ALIASES: Tuple[str, ...] = ("seed", "random_seed", "rng_seed")
PERFECT_ALIASES: Tuple[str, ...] = ("perfect", "is_perfect", "PERFECT")

# Some packages take both dimensions as a single (width, height) tuple
# instead of two separate parameters.
SIZE_ALIASES: Tuple[str, ...] = ("size", "dimensions", "shape")

MAX_CELL_VALUE = 15

# Smallest maze that can still hold a player start, 4 corners and a few
# corridors. The config loader already clamps level dimensions, but the
# adapter re-checks so a bad call can never produce a degenerate level.
MIN_DIMENSION = 5


class MazeGenerationError(Exception):
    """Raised when the assigned A-Maze-ing package cannot provide a maze."""


def _resolve_generator_class() -> Tuple[Any, str]:
    """Locate the assigned A-Maze-ing generator class and its dotted name."""
    attempts: List[str] = []

    forced = os.environ.get(MODULE_ENV_VAR, "").strip()
    module_names: Tuple[str, ...] = CANDIDATE_MODULES
    if forced:
        module_names = (forced,) + CANDIDATE_MODULES

    for module_name in module_names:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:  # noqa: BLE001 - any import problem is skippable
            attempts.append(f"{module_name} ({exc.__class__.__name__})")
            continue

        for class_name in CANDIDATE_CLASSES:
            candidate = getattr(module, class_name, None)
            if inspect.isclass(candidate):
                return candidate, f"{module_name}.{class_name}"

        attempts.append(f"{module_name} (no generator class)")

    raise MazeGenerationError(
        "A-Maze-ing package not found: no usable generator class among "
        + ", ".join(attempts)
        + ". Install the assigned package (e.g. "
        "`pip install mazegenerator-2.1.0-py3-none-any.whl`)."
    )


def _build_kwargs(
    generator_class: Any,
    width: int,
    height: int,
    seed: int,
) -> Dict[str, Any]:
    """Map our parameters onto the names the assigned constructor declares."""
    try:
        parameters = inspect.signature(generator_class.__init__).parameters
    except (TypeError, ValueError):  # pragma: no cover - exotic C classes
        return {"width": width, "height": height, "seed": seed}

    accepted = set(parameters) - {"self"}
    takes_kwargs = any(
        param.kind is inspect.Parameter.VAR_KEYWORD
        for param in parameters.values()
    )

    kwargs: Dict[str, Any] = {}

    def _assign(aliases: Sequence[str], value: Any) -> bool:
        """Set the first alias the constructor declares. True if it did."""
        for alias in aliases:
            if alias in accepted:
                kwargs[alias] = value
                return True
        return False

    got_width = _assign(WIDTH_ALIASES, width)
    got_height = _assign(HEIGHT_ALIASES, height)
    if not (got_width and got_height):
        # No separate width/height parameter: the package may expect the
        # two dimensions packed in a single tuple, as the assigned
        # A-Maze-ing package does with `size=(width, height)`.
        _assign(SIZE_ALIASES, (width, height))
    _assign(SEED_ALIASES, seed)
    # V.4: "The parameter PERFECT will be set to False to produce
    # Pac-Man-compatible corridors". Only sent when the package has it;
    # packages that always break walls simply do not declare it.
    _assign(PERFECT_ALIASES, False)

    if takes_kwargs and "seed" not in kwargs:
        kwargs["seed"] = seed

    return kwargs


def _extract_grid(instance: Any) -> Any:
    """Read the raw grid out of a generator instance, trying each accessor."""
    for accessor_name in CANDIDATE_GRID_ACCESSORS:
        accessor = getattr(instance, accessor_name, None)
        if accessor is None:
            continue
        if callable(accessor):
            method: Callable[[], Any] = accessor
            return method()
        return accessor

    raise MazeGenerationError(
        "The A-Maze-ing package exposes no known grid accessor "
        f"(tried: {', '.join(CANDIDATE_GRID_ACCESSORS)})."
    )


def _normalize_grid(raw_grid: Any, width: int, height: int) -> List[List[int]]:
    """Validate the package's grid and copy it into our own structure.

    A-Maze-ing cell format: N = 1, E = 2, S = 4, W = 8, a set bit meaning
    the wall is closed. The grid is copied rather than referenced, so the
    game cannot be affected by the package mutating its own state later.
    """
    if not isinstance(raw_grid, (list, tuple)):
        raise MazeGenerationError("A-Maze-ing did not return a list of rows.")

    if len(raw_grid) != height:
        raise MazeGenerationError(
            f"Invalid maze height: {height} expected, {len(raw_grid)} received."
        )

    grid: List[List[int]] = []

    for row in raw_grid:
        if not isinstance(row, (list, tuple)):
            raise MazeGenerationError("A-Maze-ing returned an invalid grid row.")

        if len(row) != width:
            raise MazeGenerationError(
                f"Invalid maze width: {width} expected, {len(row)} received."
            )

        cells: List[int] = []
        for cell in row:
            if isinstance(cell, bool) or not isinstance(cell, int):
                raise MazeGenerationError(
                    "A-Maze-ing returned a non-integer cell."
                )
            if cell < 0 or cell > MAX_CELL_VALUE:
                raise MazeGenerationError(
                    f"Invalid A-Maze-ing cell value: {cell} "
                    f"(expected between 0 and {MAX_CELL_VALUE})."
                )
            cells.append(int(cell))

        grid.append(cells)

    return grid


def generate_maze(width: int, height: int, seed: int) -> Maze:
    """Generate one maze with the assigned A-Maze-ing package.

    Raises MazeGenerationError on any failure - missing package,
    unexpected interface or malformed grid. Never falls back to a
    home-made generator, which V.4 forbids.
    """
    if width < MIN_DIMENSION or height < MIN_DIMENSION:
        raise MazeGenerationError(
            f"Maze dimensions too small: {width}x{height} "
            f"(minimum {MIN_DIMENSION}x{MIN_DIMENSION})."
        )

    generator_class, dotted_name = _resolve_generator_class()
    kwargs = _build_kwargs(generator_class, width, height, seed)

    try:
        instance = generator_class(**kwargs)
        raw_grid = _extract_grid(instance)
    except MazeGenerationError:
        raise
    except Exception as exc:  # noqa: BLE001 - external package, any failure
        logger.error("A-Maze-ing generation failed (%s): %s", dotted_name, exc)
        raise MazeGenerationError(
            f"Cannot generate the maze with A-Maze-ing ({dotted_name}): {exc}"
        ) from exc

    grid = _normalize_grid(raw_grid, width, height)

    logger.info(
        "Maze %sx%s generated by %s (seed=%s, args=%s)",
        width,
        height,
        dotted_name,
        seed,
        sorted(kwargs),
    )

    return Maze(width=width, height=height, grid=grid)
