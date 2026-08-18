"""Main game engine: state machine and game loop (chapter IV, VI.7)."""

from __future__ import annotations

import logging
from typing import Optional, Tuple

import pygame

from config.loader import GameConfig
from entities.ghost import GhostMode
from entities.player import Player
from game.cheat import CheatState
from game.highscore import HighscoreBoard
from game.level import Level, build_level
from game.state import GameState
from ui import hud, menu
from ui.renderer import Renderer

logger = logging.getLogger("pacman.engine")

HUD_HEIGHT = 60
# Empty border kept around the maze, in pixels.
MARGIN = 30
COLLISION_THRESHOLD = 0.5
SCATTER_DURATION = 6.0
CHASE_DURATION = 15.0
READY_DURATION = 2.5


class GameEngine:
    """Own the state machine and tie every other module together."""

    def __init__(self, config: GameConfig) -> None:
        """Set up the window, renderer, highscore board and initial state."""
        self.config = config
        pygame.init()

        self.renderer = Renderer(config.cell_size)
        if config.fullscreen:
            self.screen = pygame.display.set_mode((0, 0), pygame.FULLSCREEN)
        else:
            # A resizable window lets a player close the game with the
            # window button instead of walking back through the menus,
            # which matters once the build is downloaded from a store.
            self.screen = pygame.display.set_mode(
                self._windowed_size(), pygame.RESIZABLE
            )
        self.window_size = self.screen.get_size()
        pygame.display.set_caption("Pac-Man - 42")
        self.clock = pygame.time.Clock()

        self.highscores = HighscoreBoard(config.highscore_filename)
        self.cheat = CheatState()

        self.state = GameState.MAIN_MENU
        self.menu_selection = 0
        self.pause_selection = 0

        self.level_index = 0
        self.level: Optional[Level] = None
        self.player: Optional[Player] = None
        self.score = 0
        self.lives = config.lives
        self.time_left = 0.0
        self.was_victory = False
        self.name_buffer = ""
        # Scatter/chase phase cycling for ghost AI (see entities/ghost.py).
        self.scatter_active = True
        self.phase_time_left = SCATTER_DURATION
        # Brief "READY!" freeze before gameplay starts or resumes, so the
        # level never begins with ghosts already bearing down on the
        # player. VI.7 doesn't require it; it matches the original arcade
        # and gives the player a fair start.
        self.ready_time_left = READY_DURATION

    # ------------------------------------------------------------------ #
    # Setup / level flow
    # ------------------------------------------------------------------ #
    def start_new_game(self) -> None:
        """Reset score/lives, load level 1, and switch to PLAYING."""
        self.score = 0
        self.lives = self.config.lives
        self.level_index = 0
        self.cheat = CheatState()
        self._load_level(self.level_index)
        self.state = GameState.PLAYING

    def _load_level(self, index: int) -> None:
        level_config = self.config.levels[index]
        try:
            self.level = build_level(index, level_config, self.config)
        except Exception as exc:  # noqa: BLE001 - never crash on level build
            logger.error("Failed to generate level %d: %s", index, exc)
            self.state = GameState.MAIN_MENU
            return
        start = self.level.player_start
        self.player = Player(
            x=float(start[0]),
            y=float(start[1]),
            lives=self.lives,
            speed_cells_per_sec=float(self.config.player_speed),
        )
        self.time_left = self.level.time_limit
        self.scatter_active = True
        self.phase_time_left = SCATTER_DURATION
        self.ready_time_left = READY_DURATION
        self._resize_window()

    def _windowed_size(self) -> Tuple[int, int]:
        """Return a window fitting the largest level, capped to the desktop."""
        widest = max(level.width for level in self.config.levels)
        tallest = max(level.height for level in self.config.levels)
        desktop = pygame.display.Info()
        width = min(
            widest * self.config.cell_size + 2 * MARGIN, desktop.current_w
        )
        height = min(
            tallest * self.config.cell_size + HUD_HEIGHT + 2 * MARGIN,
            desktop.current_h,
        )
        return width, height

    def _resize_window(self) -> None:
        """Scale the maze to fill whatever window size is current."""
        screen_w, screen_h = self.screen.get_size()
        self.window_size = (screen_w, screen_h)

        if self.level is None:
            return

        available_w = screen_w - 2 * MARGIN
        available_h = screen_h - HUD_HEIGHT - 2 * MARGIN

        maze_width = self.level.maze.width
        maze_height = self.level.maze.height

        # Biggest square cell that allows the whole maze to fit.
        cell_size = min(
            available_w // maze_width,
            available_h // maze_height,
        )

        self.renderer.cell_size = max(8, cell_size)

        logger.info(
            "Window: %dx%d | Maze: %dx%d | Cell: %d",
            screen_w,
            screen_h,
            maze_width,
            maze_height,
            self.renderer.cell_size,
        )

    def _respawn_player_and_ghosts(self) -> None:
        if self.level is None or self.player is None:
            return
        self.player.respawn(self.level.player_start)
        self.scatter_active = True
        self.phase_time_left = SCATTER_DURATION
        self.ready_time_left = READY_DURATION
        for ghost in self.level.ghosts:
            ghost.x, ghost.y = float(ghost.corner[0]), float(ghost.corner[1])
            ghost.mode = GhostMode.CHASE
            ghost.direction = (0, 0)

    def _lose_life(self) -> None:
        self.lives -= 1
        if self.lives <= 0:
            self.was_victory = False
            self.state = GameState.GAME_OVER
        else:
            self._respawn_player_and_ghosts()

    def _advance_level(self) -> None:
        self.level_index += 1
        if self.level_index >= len(self.config.levels):
            self.was_victory = True
            self.state = GameState.VICTORY
        else:
            self._load_level(self.level_index)

    # ------------------------------------------------------------------ #
    # Main loop
    # ------------------------------------------------------------------ #
    def run(self) -> None:
        """Main loop: tick the clock, handle input, update, draw, repeat."""
        # `try/finally` so `pygame.quit()` always runs: without it, an
        # error escaping an update would leave the fullscreen display open
        # while pac-man.py reports it (III.1: always release resources).
        try:
            while self.state != GameState.QUIT:
                dt = self.clock.tick(60) / 1000.0
                self._handle_events()
                self._update(dt)
                self._draw()
                pygame.display.flip()
        finally:
            pygame.quit()

    # ------------------------------------------------------------------ #
    # Events
    # ------------------------------------------------------------------ #
    def _handle_events(self) -> None:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.state = GameState.QUIT
                return
            if event.type == pygame.VIDEORESIZE and not self.config.fullscreen:
                self.screen = pygame.display.set_mode(
                    (event.w, event.h), pygame.RESIZABLE
                )
                self._resize_window()
                continue
            if event.type != pygame.KEYDOWN:
                continue

            if self.state == GameState.MAIN_MENU:
                self._handle_main_menu_key(event.key)
            elif self.state in (GameState.INSTRUCTIONS, GameState.HIGHSCORES):
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE):
                    self.state = GameState.MAIN_MENU
            elif self.state == GameState.PLAYING:
                self._handle_playing_key(event.key)
            elif self.state == GameState.PAUSED:
                self._handle_pause_key(event.key)
            elif self.state in (GameState.GAME_OVER, GameState.VICTORY):
                if event.key == pygame.K_RETURN:
                    self.name_buffer = ""
                    self.state = GameState.ENTER_NAME
            elif self.state == GameState.ENTER_NAME:
                self._handle_enter_name_key(event)

    def _handle_main_menu_key(self, key: int) -> None:
        if key in (pygame.K_UP, pygame.K_w):
            self.menu_selection = (self.menu_selection - 1) % len(
                menu.MAIN_MENU_OPTIONS
            )
        elif key in (pygame.K_DOWN, pygame.K_s):
            self.menu_selection = (self.menu_selection + 1) % len(
                menu.MAIN_MENU_OPTIONS
            )
        elif key == pygame.K_RETURN:
            choice = menu.MAIN_MENU_OPTIONS[self.menu_selection]
            if choice == "Start Game":
                self.start_new_game()
            elif choice == "Highscores":
                self.state = GameState.HIGHSCORES
            elif choice == "Instructions":
                self.state = GameState.INSTRUCTIONS
            elif choice == "Exit":
                self.state = GameState.QUIT

    def _handle_playing_key(self, key: int) -> None:
        direction_map = {
            pygame.K_UP: (0, -1),
            pygame.K_w: (0, -1),
            pygame.K_DOWN: (0, 1),
            pygame.K_s: (0, 1),
            pygame.K_LEFT: (-1, 0),
            pygame.K_a: (-1, 0),
            pygame.K_RIGHT: (1, 0),
            pygame.K_d: (1, 0),
        }
        if key in direction_map and self.player is not None:
            self.player.set_direction(direction_map[key])
        elif key == pygame.K_ESCAPE:
            self.pause_selection = 0
            self.state = GameState.PAUSED
        # Cheat mode (VI.5) - every binding is listed in the HUD legend.
        elif key == pygame.K_z:
            self.cheat.request_skip_level()
        elif key == pygame.K_e:
            self.cheat.toggle_ghosts_frozen()
        elif key == pygame.K_i:
            self.cheat.toggle_invincible()
        elif key == pygame.K_l:
            self.cheat.request_extra_life()
        elif key == pygame.K_p:
            self.cheat.toggle_speed_boost()

    def _handle_pause_key(self, key: int) -> None:
        if key in (pygame.K_UP, pygame.K_w, pygame.K_DOWN, pygame.K_s):
            self.pause_selection = 1 - self.pause_selection
        elif key == pygame.K_ESCAPE:
            self.state = GameState.PLAYING
        elif key == pygame.K_RETURN:
            if self.pause_selection == 0:
                self.state = GameState.PLAYING
            else:
                self.state = GameState.MAIN_MENU
                self.menu_selection = 0

    def _handle_enter_name_key(self, event: pygame.event.Event) -> None:
        if event.key == pygame.K_RETURN:
            self.highscores.add_score(self.name_buffer or "PLAYER", self.score)
            self.state = GameState.MAIN_MENU
            self.menu_selection = 0
        elif event.key == pygame.K_BACKSPACE:
            self.name_buffer = self.name_buffer[:-1]
        elif event.unicode and (event.unicode.isalnum() or event.unicode == " "):
            if len(self.name_buffer) < 10:
                self.name_buffer += event.unicode

    # ------------------------------------------------------------------ #
    # Update
    # ------------------------------------------------------------------ #
    def _update(self, dt: float) -> None:
        if self.state != GameState.PLAYING:
            return
        if self.level is None or self.player is None:
            return

        effective_dt = dt

        # Cheat mode (VI.5): grant any queued extra lives and keep the
        # player's speed in sync with the speed-boost toggle.
        pending_lives = self.cheat.consume_extra_lives()
        if pending_lives:
            self.lives += pending_lives
            self.player.lives = self.lives
        self.player.speed_cells_per_sec = (
            float(self.config.player_speed) * self.cheat.player_speed_multiplier()
        )

        if self.ready_time_left > 0:
            # "READY!" freeze: nothing moves and the level timer does not
            # run yet, so the level never starts with ghosts already on
            # top of the player (see READY_DURATION above).
            self.ready_time_left -= dt
            if self.cheat.skip_level_requested:
                self.cheat.skip_level_requested = False
                self._advance_level()
            return

        self.player.update(self.level.maze, effective_dt)

        if not self.cheat.ghosts_frozen:
            self.phase_time_left -= dt
            if self.phase_time_left <= 0:
                self.scatter_active = not self.scatter_active
                self.phase_time_left = (
                    SCATTER_DURATION if self.scatter_active else CHASE_DURATION
                )
            for ghost in self.level.ghosts:
                ghost.update(
                    self.level.maze,
                    effective_dt,
                    self.player.cell,
                    self.config.ghost_respawn_delay,
                    scatter=self.scatter_active,
                    # The ambusher aims ahead of the player, so it needs
                    # to know where they are heading (see ghost.py).
                    player_direction=self.player.direction,
                )

        self._handle_pickups()
        self._handle_ghost_collisions()

        if self.cheat.skip_level_requested:
            self.cheat.skip_level_requested = False
            self._advance_level()
            return

        if self.level.remaining_pacgums() == 0:
            self._advance_level()
            return

        # VI.7 leaves the timeout behaviour open ("you can decide what
        # happens"): the choice here is to cost one life and restart the
        # same level, exactly like touching a ghost.
        self.time_left -= effective_dt
        if self.time_left <= 0:
            if self.cheat.invincible:
                # Invincibility also neutralises the timer, otherwise a
                # reviewer inspecting a level would still be interrupted.
                self.time_left = self.level.time_limit
                return
            # _lose_life already respawns the player when lives remain.
            self._lose_life()
            if self.state == GameState.PLAYING:
                self.time_left = self.level.time_limit

    def _handle_pickups(self) -> None:
        if self.level is None or self.player is None:
            return
        cell = self.player.cell
        pickup = self.level.pickups.pop(cell, None)
        if pickup is None:
            return
        self.score += pickup.points
        if pickup.is_super:
            for ghost in self.level.ghosts:
                ghost.frighten(self.config.frightened_duration)

    def _handle_ghost_collisions(self) -> None:
        if self.level is None or self.player is None:
            return
        for ghost in self.level.ghosts:
            dist_sq = (ghost.x - self.player.x) ** 2 + (ghost.y - self.player.y) ** 2
            if dist_sq > COLLISION_THRESHOLD ** 2:
                continue
            if ghost.mode == GhostMode.EATEN:
                continue
            if ghost.mode == GhostMode.FRIGHTENED:
                self.score += self.config.points_per_ghost
                ghost.get_eaten(self.config.ghost_respawn_delay)
            elif self.cheat.invincible:
                # VI.5 "Invincibility (no life lost; ghosts cannot eat the
                # player)": the contact is ignored entirely - the player is
                # not even sent back to the center, so a reviewer can walk
                # through the ghosts to inspect the level.
                continue
            else:
                self._lose_life()
                return

    # ------------------------------------------------------------------ #
    # Draw
    # ------------------------------------------------------------------ #
    def _draw(self) -> None:
        if self.state == GameState.MAIN_MENU:
            menu.draw_main_menu(self.screen, self.renderer, self.menu_selection)
        elif self.state == GameState.INSTRUCTIONS:
            menu.draw_instructions(self.screen, self.renderer, self.config)
        elif self.state == GameState.HIGHSCORES:
            menu.draw_highscores(self.screen, self.renderer, self.highscores.top())
        elif self.state in (GameState.PLAYING, GameState.PAUSED):
            self._draw_gameplay()
            if self.state == GameState.PAUSED:
                hud.draw_pause_menu(self.screen, self.renderer, self.pause_selection)
        elif self.state in (GameState.GAME_OVER, GameState.VICTORY):
            hud.draw_end_screen(
                self.screen,
                self.renderer,
                victory=self.state == GameState.VICTORY,
                score=self.score,
            )
        elif self.state == GameState.ENTER_NAME:
            hud.draw_enter_name(
                self.screen,
                self.renderer,
                self.name_buffer,
                self.score,
                # Only claim "new highscore" when the score really makes
                # the top 10; the name is still asked for either way (V.5).
                is_highscore=self.highscores.qualifies(self.score),
            )

    def _draw_gameplay(self) -> None:
        if self.level is None or self.player is None:
            return
        maze_w, maze_h = self.renderer.maze_pixel_size(self.level.maze)
        offset = ((self.window_size[0] - maze_w) // 2, HUD_HEIGHT)

        self.screen.fill((0, 0, 0))
        self.renderer.draw_maze(self.screen, self.level.maze, offset)
        self.renderer.draw_pickups(self.screen, self.level.pickups, offset)
        self.renderer.draw_ghosts(self.screen, self.level.ghosts, offset)
        self.renderer.draw_player(self.screen, self.player.x, self.player.y, offset)

        hud_rect = pygame.Rect(0, 0, self.window_size[0], HUD_HEIGHT)
        hud.draw_hud(
            self.screen,
            self.renderer,
            self.score,
            self.lives,
            self.level_index + 1,
            len(self.config.levels),
            self.time_left,
            hud_rect,
        )
        hud.draw_cheat_legend(self.screen, self.renderer, self.cheat, hud_rect)
        if self.ready_time_left > 0:
            hud.draw_ready_overlay(self.screen, self.renderer)
