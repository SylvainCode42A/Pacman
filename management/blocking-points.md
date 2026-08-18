# Blocking Points Encountered

Real issues hit during development, kept here as required by chapter VIII.

1. **`pygame` broken on our Python version.** The available `pygame`
   wheel did not fully support the Python release we were on, crashing
   on `pygame.font.init()`. Fixed by switching to `pygame-ce`, a drop-in
   replacement, with no code change beyond `requirements.txt`.

2. **Segmentation fault from mixing `pygame` and `pygame-ce`.** After
   the switch, `make install` silently reinstalled vanilla `pygame` from
   an outdated `requirements.txt`, leaving two SDL2 copies loaded at
   once and crashing hard on macOS. Fixed by pinning `pygame-ce` only
   and making `make install` uninstall both variants first, so they can
   never coexist again.

3. **Ghost pincer made the game unwinnable.** With four ghosts running a
   pure shortest-path chase, the player could be trapped in a corridor
   with a ghost closing in from each end, with no escape regardless of
   skill. Fixed by alternating scatter and chase phases, and by a
   "PRET !" freeze on every level start and respawn so a level never
   resumes with a ghost on top of the player.

4. **Entities clipping through walls.** Movement is interpolated between
   cells, and the first implementation recomputed the destination from
   the current float position every frame. At high speed an entity could
   overshoot and compute a destination on the far side of a wall. Fixed
   by committing the destination once, when leaving an aligned cell. The
   comment explaining this is kept in `entities/player.py`, because it
   is the kind of bug a well-meaning refactor reintroduces.

5. **Linting third-party code.** `make lint` runs `flake8 .` and
   `mypy .` over the whole repository, which includes the assigned
   A-Maze-ing package. That code is not ours and V.4 forbids modifying
   it, yet it made our own lint fail. Resolved by excluding `amazing/`
   in `setup.cfg`, keeping the mandated flags untouched for our code —
   which now also passes `mypy --strict`.

6. **The assigned package spawned the player inside a wall.**
   `mazegenerator` 2.1.0 seals a decorative "42" pattern of 18 cells in
   the middle of the maze — precisely where VI.1 requires the player to
   start. Taking the geometric centre spawned Pac-Man in a sealed cell:
   he could not move, no pacgum was reachable, and all ten levels were
   unfinishable. It was caught by a reachability check rather than by
   playing, which would have looked like a movement bug. Fixed by
   computing the largest connected region of the maze and anchoring the
   player, the four ghosts and every pacgum inside it — their package is
   untouched, as V.4 demands.

7. **The same package takes its dimensions as a tuple.** Its constructor
   is `MazeGenerator(size=(width, height), ...)`, not two separate
   parameters, so our adapter silently fell back to the default 15x15
   whatever the config asked for. `maze/adapter.py` now detects a
   `size`-style parameter through `inspect.signature` and packs both
   dimensions into it.
