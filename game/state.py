"""Game state machine (chapter IV game loop, VI.7 pause, VI.8 screens)."""

from enum import Enum, auto


class GameState(Enum):
    """Every screen the engine can be in (see `game/engine.py`)."""

    MAIN_MENU = auto()
    INSTRUCTIONS = auto()
    HIGHSCORES = auto()
    PLAYING = auto()
    PAUSED = auto()
    GAME_OVER = auto()
    VICTORY = auto()
    ENTER_NAME = auto()
    QUIT = auto()
