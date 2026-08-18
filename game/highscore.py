"""Persistent top-10 highscore board, stored as a JSON file (V.5)."""

from __future__ import annotations

import json
import logging
import sys
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import List

logger = logging.getLogger("pacman.highscore")

MAX_ENTRIES = 10
MAX_NAME_LENGTH = 10

# Directory used for the highscore file when the game runs as a packaged
# build (chapter VII). A frozen executable is often installed in a
# read-only location, so scores go to the user's home directory instead.
PACKAGED_DATA_DIR = ".pacman42"


def resolve_highscore_path(filename: str) -> Path:
    """Return the real path the highscore file must be read/written at."""
    path = Path(filename).expanduser()

    if path.is_absolute() or path.parent != Path("."):
        return path

    if getattr(sys, "frozen", False):
        directory = Path.home() / PACKAGED_DATA_DIR
        try:
            directory.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            logger.warning(
                "Cannot create the save directory (%s): %s", directory, exc
            )
            return path
        return directory / path.name

    return path


@dataclass
class HighscoreEntry:
    """One row of the highscore board: a sanitized name and a score."""

    name: str
    score: int


def sanitize_name(raw_name: str) -> str:
    """Keep only alphanumeric characters and spaces, max 10 chars."""
    cleaned = "".join(ch for ch in raw_name if ch.isalnum() or ch == " ").strip()
    if not cleaned:
        cleaned = "PLAYER"
    return cleaned[:MAX_NAME_LENGTH]


class HighscoreBoard:
    """Persistent top-10 highscore board backed by a JSON file (V.5)."""

    def __init__(self, filename: str):
        """Create the board and immediately load `filename` from disk."""
        self.filename = filename
        self.path = resolve_highscore_path(filename)
        self.entries: List[HighscoreEntry] = []
        self.load()

    def load(self) -> None:
        """(Re)load entries from disk, tolerating a missing/corrupt file."""
        path = self.path
        if not path.is_file():
            logger.info("No highscore file yet, starting from an empty board.")
            self.entries = []
            return
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            if not isinstance(raw, list):
                raise ValueError("the file must contain a list")
            entries = []
            for item in raw:
                if not isinstance(item, dict):
                    continue
                name = sanitize_name(str(item.get("name", "")))
                score = item.get("score", 0)
                if not isinstance(score, int) or isinstance(score, bool) or score < 0:
                    continue
                entries.append(HighscoreEntry(name=name, score=score))
            entries.sort(key=lambda e: e.score, reverse=True)
            self.entries = entries[:MAX_ENTRIES]
        except (json.JSONDecodeError, OSError, ValueError) as exc:
            logger.warning(
                "Unreadable or corrupted highscore file (%s): starting empty.",
                exc,
            )
            self.entries = []

    def save(self) -> None:
        """Write the current top entries to disk, logging on failure."""
        try:
            path = self.path
            path.write_text(
                json.dumps([asdict(e) for e in self.entries], indent=2),
                encoding="utf-8",
            )
        except OSError as exc:
            logger.warning("Cannot write the highscore file (%s).", exc)

    def add_score(self, raw_name: str, score: int) -> None:
        """Sanitize the name, insert the score, trim to top 10 and save."""
        if not isinstance(score, int) or score < 0:
            score = 0
        name = sanitize_name(raw_name)
        self.entries.append(HighscoreEntry(name=name, score=score))
        self.entries.sort(key=lambda e: e.score, reverse=True)
        self.entries = self.entries[:MAX_ENTRIES]
        self.save()

    def top(self) -> List[HighscoreEntry]:
        """Return a copy of the current top entries, highest score first."""
        return list(self.entries)

    def qualifies(self, score: int) -> bool:
        """Return True if `score` would make it onto the top-10 board."""
        if len(self.entries) < MAX_ENTRIES:
            return True
        return score > self.entries[-1].score
