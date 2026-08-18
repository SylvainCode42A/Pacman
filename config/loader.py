"""Configuration loading: JSON with comments, clamped values (V.1-V.3)."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List

from config.defaults import (
    DEFAULT_CONFIG,
    DEFAULT_LEVEL,
    LEVELS_KEYS,
    MAX_LEVEL_DIMENSION,
    MIN_LEVEL_DIMENSION,
    MIN_LEVELS,
)

logger = logging.getLogger("pacman.config")


class ConfigError(Exception):
    """Raised only for unrecoverable startup errors (e.g. no file at all)."""


@dataclass
class LevelConfig:
    """One maze level's dimensions."""

    width: int
    height: int


@dataclass
class GameConfig:
    """Fully validated, ready-to-use game configuration."""

    highscore_filename: str
    levels: List[LevelConfig]
    lives: int
    pacgum: int
    points_per_pacgum: int
    points_per_super_pacgum: int
    points_per_ghost: int
    seed: int
    level_max_time: int
    cell_size: int
    fullscreen: bool
    player_speed: int
    ghost_speed: int
    frightened_duration: int
    ghost_respawn_delay: int
    warnings: List[str] = field(default_factory=list)


def _strip_comments(raw_text: str) -> str:
    """Remove '#', '//' and '/* ... */' comment lines from JSON text."""
    # Only whole-line comments are stripped, which keeps this safe for
    # JSON values that legitimately contain those characters.
    cleaned_lines: List[str] = []
    in_block_comment = False
    for line in raw_text.splitlines():
        stripped = line.strip()
        if in_block_comment:
            if "*/" in stripped:
                in_block_comment = False
            continue
        if stripped.startswith("/*"):
            if "*/" not in stripped:
                in_block_comment = True
            continue
        if stripped.startswith("#") or stripped.startswith("//"):
            continue
        cleaned_lines.append(line)
    return "\n".join(cleaned_lines)


def _read_json_with_comments(path: Path) -> Dict[str, Any]:
    """Read and parse the config file, comments stripped first."""
    raw_text = path.read_text(encoding="utf-8")
    cleaned = _strip_comments(raw_text)
    data = json.loads(cleaned)
    if not isinstance(data, dict):
        raise ConfigError("The configuration file must contain a JSON object.")
    return data


def _clamp_int(
    raw: Dict[str, Any], key: str, warnings: List[str], minimum: int = 0
) -> int:
    """Read an integer key, falling back to its default when invalid."""
    default_value = int(DEFAULT_CONFIG[key])
    if key not in raw:
        return default_value
    value = raw[key]
    if not isinstance(value, int) or isinstance(value, bool):
        warnings.append(
            f"Key '{key}' is not an integer: default {default_value} used."
        )
        return default_value
    if value < minimum:
        warnings.append(
            f"Key '{key}' out of range ({value} < {minimum}): default "
            f"{default_value} used."
        )
        return default_value
    return value


def _clamp_bool(raw: Dict[str, Any], key: str, warnings: List[str]) -> bool:
    """Read a boolean key, falling back to its default when invalid."""
    default_value = bool(DEFAULT_CONFIG[key])
    if key not in raw:
        return default_value
    value = raw[key]
    if not isinstance(value, bool):
        warnings.append(
            f"Key '{key}' is not true or false: default "
            f"{str(default_value).lower()} used."
        )
        return default_value
    return value


def _clamp_string(raw: Dict[str, Any], key: str, warnings: List[str]) -> str:
    """Read a string key, falling back to its default when invalid."""
    default_value = str(DEFAULT_CONFIG[key])
    value = raw.get(key, default_value)
    if not isinstance(value, str) or not value.strip():
        warnings.append(
            f"Key '{key}' is not a non-empty string: default "
            f"'{default_value}' used."
        )
        return default_value
    return value


def _clamp_levels(raw: Dict[str, Any], warnings: List[str]) -> List[LevelConfig]:
    """Read the level list, clamping dimensions and padding to 10 levels."""
    # Read whichever spelling the file uses (see LEVELS_KEYS).
    raw_levels: Any = None
    for key in LEVELS_KEYS:
        if key in raw:
            raw_levels = raw[key]
            break
    levels: List[LevelConfig] = []

    if not isinstance(raw_levels, list) or not raw_levels:
        warnings.append("Key 'levels' missing or invalid: defaults used.")
        raw_levels = DEFAULT_CONFIG["levels"]

    def _dimension(
        raw_value: Any, default_value: int, index: int, name: str
    ) -> int:
        """Validate then clamp one level dimension into the allowed range."""
        if not isinstance(raw_value, int) or isinstance(raw_value, bool):
            warnings.append(
                f"Level {index}: '{name}' is not an integer, default "
                f"{default_value} used."
            )
            return default_value

        if raw_value < MIN_LEVEL_DIMENSION:
            warnings.append(
                f"Level {index}: '{name}' too small ({raw_value}), raised to "
                f"{MIN_LEVEL_DIMENSION}."
            )
            return MIN_LEVEL_DIMENSION

        if raw_value > MAX_LEVEL_DIMENSION:
            warnings.append(
                f"Level {index}: '{name}' too large ({raw_value}), lowered to "
                f"{MAX_LEVEL_DIMENSION}."
            )
            return MAX_LEVEL_DIMENSION

        return raw_value

    for index, entry in enumerate(raw_levels):
        width = DEFAULT_LEVEL["width"]
        height = DEFAULT_LEVEL["height"]
        if isinstance(entry, dict):
            width = _dimension(entry.get("width", width), width, index, "width")
            height = _dimension(entry.get("height", height), height, index, "height")
        else:
            warnings.append(
                f"Level {index}: invalid entry, default dimensions used."
            )
        levels.append(LevelConfig(width=width, height=height))

    if len(levels) < MIN_LEVELS:
        warnings.append(
            f"Only {len(levels)} level(s) provided: padded to the "
            f"{MIN_LEVELS} levels required by VI.7."
        )
        last = levels[-1] if levels else LevelConfig(**DEFAULT_LEVEL)
        while len(levels) < MIN_LEVELS:
            # Each generated level is slightly bigger than the previous one,
            # but never beyond the maximum allowed dimension.
            last = LevelConfig(
                width=min(last.width + 2, MAX_LEVEL_DIMENSION),
                height=min(last.height + 2, MAX_LEVEL_DIMENSION),
            )
            levels.append(last)

    return levels


def load_config(path_str: str) -> GameConfig:
    """Load, sanitize and return a GameConfig from a JSON file.

    Never raises on a merely invalid value inside the file (those are
    clamped with a logged warning, per V.3). Only raises ConfigError when
    the file itself cannot be read or parsed at all.
    """
    path = Path(path_str)

    if path.suffix.lower() != ".json":
        raise ConfigError(f"The configuration file must be a .json: {path}")

    if not path.is_file():
        raise ConfigError(f"Configuration file not found: {path}")

    try:
        raw = _read_json_with_comments(path)
    except json.JSONDecodeError as exc:
        raise ConfigError(f"Invalid JSON in '{path}': {exc}") from exc
    except OSError as exc:
        raise ConfigError(f"Cannot read '{path}': {exc}") from exc

    warnings: List[str] = []

    known_keys = set(DEFAULT_CONFIG.keys()) | set(LEVELS_KEYS)
    unknown_keys = set(raw.keys()) - known_keys
    for key in sorted(unknown_keys):
        warnings.append(f"Unknown key '{key}' ignored.")

    config = GameConfig(
        highscore_filename=_clamp_string(raw, "highscore_filename", warnings),
        levels=_clamp_levels(raw, warnings),
        lives=_clamp_int(raw, "lives", warnings, minimum=1),
        pacgum=_clamp_int(raw, "pacgum", warnings, minimum=1),
        points_per_pacgum=_clamp_int(raw, "points_per_pacgum", warnings),
        points_per_super_pacgum=_clamp_int(raw, "points_per_super_pacgum", warnings),
        points_per_ghost=_clamp_int(raw, "points_per_ghost", warnings),
        seed=_clamp_int(raw, "seed", warnings, minimum=0),
        level_max_time=_clamp_int(raw, "level_max_time", warnings, minimum=10),
        cell_size=_clamp_int(raw, "cell_size", warnings, minimum=8),
        fullscreen=_clamp_bool(raw, "fullscreen", warnings),
        player_speed=_clamp_int(raw, "player_speed", warnings, minimum=1),
        ghost_speed=_clamp_int(raw, "ghost_speed", warnings, minimum=1),
        frightened_duration=_clamp_int(
            raw, "frightened_duration", warnings, minimum=1
        ),
        ghost_respawn_delay=_clamp_int(
            raw, "ghost_respawn_delay", warnings, minimum=1
        ),
        warnings=warnings,
    )

    for warning in warnings:
        logger.warning(warning)

    return config
