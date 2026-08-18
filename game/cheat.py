"""Cheat mode for peer review (VI.5).

Bindings, all shown permanently in the HUD legend and on the
Instructions screen:

    Z - Skip the current level    L - Grant one extra life
    E - Freeze / unfreeze ghosts  P - Toggle the player speed boost
    I - Toggle invincibility

Letter keys rather than F1-F5, because function keys are captured by
the system on most macOS setups used at 42.
"""

from __future__ import annotations

from dataclasses import dataclass

# Multiplier applied to the player's speed while the boost is active.
SPEED_BOOST_FACTOR = 2.0


@dataclass
class CheatState:
    """Hold the state of every cheat available during peer review."""

    ghosts_frozen: bool = False
    skip_level_requested: bool = False
    invincible: bool = False
    speed_boost: bool = False
    extra_lives_requested: int = 0

    def toggle_ghosts_frozen(self) -> None:
        """Toggle whether ghosts are frozen in place."""
        self.ghosts_frozen = not self.ghosts_frozen

    def toggle_invincible(self) -> None:
        """Toggle invincibility: ghosts and the timer stop costing lives."""
        self.invincible = not self.invincible

    def toggle_speed_boost(self) -> None:
        """Toggle the increased player speed."""
        self.speed_boost = not self.speed_boost

    def request_skip_level(self) -> None:
        """Request an immediate win of the current level."""
        self.skip_level_requested = True

    def request_extra_life(self, amount: int = 1) -> None:
        """Queue extra lives, granted on the next engine update."""
        if amount > 0:
            self.extra_lives_requested += amount

    def consume_extra_lives(self) -> int:
        """Return and reset the number of queued extra lives."""
        pending = self.extra_lives_requested
        self.extra_lives_requested = 0
        return pending

    def player_speed_multiplier(self) -> float:
        """Return the multiplier to apply to the player's base speed."""
        return SPEED_BOOST_FACTOR if self.speed_boost else 1.0
