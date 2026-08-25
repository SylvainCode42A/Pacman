# Acceptance Test Plan
 
Feature-by-feature validation against the subject, run manually before
submission. Static analysis is part of the criteria and is re-run before
every build: `flake8 .`, `make lint` and `make lint-strict` all report
0 error.
 
## Startup and configuration (V.1 / V.3)
 
- [x] `python3 pac-man.py config/config.json` launches with no traceback.
- [x] Zero or two arguments print the usage line and exit 1.
- [x] Missing file, non-`.json` file and malformed JSON each produce a
      clear one-line message, never a traceback.
- [x] A config with `lives: -1`, `pacgum: "many"`, `seed: null` and an
      unknown key starts anyway, logging one warning per problem.
- [x] A config asking for a 400000-cell-high maze is clamped instead of
      hanging the generator.
- [x] A config with fewer than 10 levels is padded to 10 (VI.7).
- [x] `#`, `//` and `/* ... */` comments are all stripped (V.2).
- [x] The list of levels is read under both `levels` and `level`. V.2
      spells the suggested key in the singular, so a config handed over at
      the defense using the subject's own wording is honoured instead of
      being silently ignored.
## Level generation, all 10 levels (VI.1)
 
Every level is a 20x20 maze with 200 pacgums spread evenly over it. All
ten were generated and checked; the table also reports how long clearing
one actually takes, measured by simulating a greedy "always head for the
nearest remaining pacgum" walk, converting the move count at the
configured player speed, and adding 50% for detours and dodging.
 
| Level | Size | Pacgums | Fill | Realistic time | Margin on 130 s |
|---|---|---|---|---|---|
| 1 | 20x20 | 200 | 51.5% | 88 s | 42 s |
| 3 | 20x20 | 200 | 51.5% | 93 s | 37 s |
| 9 | 20x20 | 200 | 51.5% | 98 s | 32 s |
| 10 | 20x20 | 200 | 51.5% | 102 s | 28 s |
 
- [x] Every level is clearable within `level_max_time`, with at least
      28 s of margin on the worst one. **This was a real defect**: with
      an earlier 21x21-to-33x33 progression that filled every corridor,
      level 1 needed 170 s and level 10 needed 422 s of perfect play
      against a 90 s limit, making the game impossible to finish.
- [x] 200 pacgums is the floor for VI.1's "most corridors": a 20x20 maze
      has 388 usable corridors, so fewer than 194 would cover under half
      of them. Maze size and pacgum count were chosen together for that
      reason: 84 pacgums on a 20x20 maze would only be 22% of its
      corridors.
- [x] Every pacgum, the four super-pacgums and the four ghosts sit inside
      the maze region reachable from the player's start, on all 10 levels.
      This matters because the assigned package seals a "42" pattern in
      the middle of the maze: 18 cells nobody can reach, right where VI.1
      puts the player.
- [x] Every maze has loops: passages exceed the `cells - 1` of a perfect
      maze, which is what `PERFECT=False` produces (V.4).
- [x] Level 1 is identical on every run (fixed seed); levels 2-10 differ.
- [x] Player starts at the center, 4 super-pacgums in the 4 corners, one
      ghost per corner.
## Gameplay (VI.2 - VI.4, VI.6)
 
- [x] Player cannot cross a wall in any of the 4 directions.
- [x] Arrow keys and WASD both work.
- [x] Pacgum, super-pacgum and edible ghost each add their configured
      score; the score never decreases.
- [x] A super-pacgum makes every ghost edible for `frightened_duration`.
- [x] An eaten ghost returns to its corner and reappears after
      `ghost_respawn_delay`; it does not turn edible again meanwhile.
- [x] The four ghosts have four different behaviours and four different
      aggressiveness ranks (1 to 4): Blinky chases directly, Pinky aims
      4 cells ahead of the player, Inky alternates chasing and wandering
      every 3 s, Clyde retreats home within 5 cells. Each also has its
      own speed multiplier, from x0.85 to x1.10.
- [x] Touching a non-edible ghost costs a life and respawns the player at
      the maze center; losing all lives triggers Game Over.
## Progression and UI (VI.7 / VI.8)
 
- [x] Clearing all pacgums advances a level, keeping score and lives;
      clearing level 10 triggers the Victory screen.
- [x] The HUD always shows score, lives, level and remaining time.
- [x] Escape pauses; the pause menu resumes or returns to the main menu.
- [x] The time limit costs a life and restarts the level.
- [x] Name entry after Game Over **and** Victory saves to the board, and
      the score then appears under "Highscores" in the main menu.
- [x] The name field refuses non-alphanumeric characters, stops at 10.
- [x] A corrupted highscore file does not break the game.
## Cheat mode (VI.5)
 
- [x] `Z` clears the level, `E` freezes ghosts, `I` makes ghost contact
      and timeouts harmless, `L` adds a life, `P` doubles the speed.
- [x] The legend is permanently visible and fits inside the HUD bar.
## Packaging (VII)
 
- [x] `make package` produces a standalone executable that starts with no
      argument, and still accepts an explicit config path.
- [x] `mazegenerator`, the assigned A-Maze-ing package, is bundled.
- [x] The Instructions screen documents controls, rules and every config
      key, and fits on one screen at 1280x800 and above.
- [x] `pygame.quit()` runs even when an error escapes the game loop, so
      the fullscreen display is never left open (III.1).
- [x] No traceback reaches the player on any failure path tested: broken
      generator, missing A-Maze-ing package, crash inside the game loop.
- [x] Extreme mazes allowed by the clamps (5x5, 5x99, 99x5, 99x99) all
      build and render without error.
- [x] `fullscreen` accepts `true` and `false`; anything else falls back to
      `true` with a warning. Both modes start, draw every screen, and a
      windowed game rescales its maze when the window is resized.
- [ ] Uploaded to itch.io as a free restricted build (pending). The build
      is unsigned, so the itch.io page must document the macOS Gatekeeper
      and Windows SmartScreen first-launch warnings (see
      `packaging-notes.md`).
- [x] No dead code: every function and class in the project is
      referenced somewhere. Four leftovers from the removed test suite
      (`describe_backend`, `try_generate_maze`, `CheatState.any_active`,
      `Maze.is_wall`) were found by an AST scan and deleted, along with
      docstrings that still claimed they were "used by the test suite".
## Bugs found and fixed
 
1. **Entities drifting through walls.** Recomputing the movement target
   from the interpolated position let entities overshoot a cell and cross
   a wall. Fixed by freezing the target when leaving an aligned cell.
2. **Jittery ghost pathing.** Ghosts targeted the player's float
   position; switched to the rounded grid cell.
3. **Unwinnable ghost pincer.** Four shortest-path chasers could seal
   both ends of a corridor. Fixed with scatter/chase phases and a
   "PRET !" freeze on start and respawn.
4. **Segfault on macOS** from `pygame` and `pygame-ce` coexisting.
5. **Traceback leaking.** The top-level handler used
   `logging.exception`, printing a full traceback — contrary to V.1.
   Downgraded to a debug-level log.
6. **Misleading "Nouveau highscore !"** shown for scores outside the top
   10. Now conditioned on `HighscoreBoard.qualifies`.
7. **Mazes nearly empty.** Only 42 pacgums per level, under 11% of a
   20x20 maze — far from VI.1's "most corridors". Now 200, a bit over
   half of the usable corridors.
8. **Cheat legend overflowing the HUD**, drawn on top of the maze.
   Compacted to three lines.
9. **Invincibility still teleported the player** to the maze center on
   contact. Ghost contact and timeouts are now ignored outright.
10. **Absurd level dimensions accepted.** Now clamped to 5-99, which
    matters because V.3 warns the config will change at defense time.
11. **Levels were impossible to finish.** Once pacgums filled most
    corridors, a 21x21 maze needed 678 moves — 170 s of perfect play
    against a 90 s limit — and the final 33x33 needed 422 s. Measured by
    simulation, then fixed by settling on 20x20 mazes with 200 grouped
    pacgums at 5 cells per second, which leaves at least 28 s of margin
    on every level against the current 130 s `level_max_time`.