#!/usr/bin/env python3
"""Pac-Man entry point: one config file argument, no traceback (V.1)."""

from __future__ import annotations

import logging
import sys
from pathlib import Path
from typing import List, Optional

from config.loader import ConfigError, load_config

# Config shipped inside the standalone build (chapter VII). It is only
# used when the game is started by double-clicking the packaged
# executable, where no command-line argument can be provided. Running
# from source keeps the strict "exactly one argument" rule of V.1.
BUNDLED_CONFIG_NAME = "config/config.json"


def _setup_logging() -> None:
    """Configure the root logger used by every module of the game."""
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(name)s: %(message)s",
    )


def _is_frozen() -> bool:
    """Return True when running from a PyInstaller standalone build."""
    return bool(getattr(sys, "frozen", False))


def _bundled_config_path() -> Optional[str]:
    """Return the config bundled in the packaged build, if any."""
    base = getattr(sys, "_MEIPASS", None)
    if base is None:
        return None
    candidate = Path(base) / BUNDLED_CONFIG_NAME
    if candidate.is_file():
        return str(candidate)
    return None


def _resolve_config_argument(argv: List[str]) -> Optional[str]:
    """Return the config path to load, or None if the usage is wrong."""
    if len(argv) == 2:
        return argv[1]

    # Packaged build launched with no argument (double-click on itch.io):
    # fall back to the configuration shipped inside the executable.
    if len(argv) == 1 and _is_frozen():
        return _bundled_config_path()

    return None


def main(argv: List[str]) -> int:
    """Parse the CLI arguments, load the config and run the game."""
    _setup_logging()

    config_path = _resolve_config_argument(argv)
    if config_path is None:
        program = argv[0] if argv else "pac-man.py"
        print(f"Usage: python3 {program} config.json", file=sys.stderr)
        return 1

    try:
        config = load_config(config_path)
    except ConfigError as exc:
        print(f"Configuration error: {exc}", file=sys.stderr)
        return 1

    if config.warnings:
        print(
            f"Configuration loaded with {len(config.warnings)} warning(s) "
            "(see the log above).",
            file=sys.stderr,
        )

    try:
        # Imported here so the usage/config errors above stay fast and
        # don't require a display or pygame to be available.
        from game.engine import GameEngine

        engine = GameEngine(config)
        engine.run()
    except Exception as exc:  # noqa: BLE001 - safety net, no traceback (V.1)
        print(f"Unexpected error, shutting down cleanly: {exc}", file=sys.stderr)
        logging.getLogger("pacman").debug("Error detail", exc_info=True)
        return 1

    return 0


if __name__ == "__main__":
    try:
        sys.exit(main(sys.argv))
    except KeyboardInterrupt:
        print("\nGame interrupted.")
        sys.exit(0)
