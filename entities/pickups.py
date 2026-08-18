"""Pacgums and super-pacgums (VI.4)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Tuple


@dataclass
class Pickup:
    """A single pacgum or super-pacgum sitting on one maze cell."""

    position: Tuple[int, int]
    points: int
    is_super: bool = False
