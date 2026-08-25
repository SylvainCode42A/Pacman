*This project has been created as part of the 42 curriculum by slidriss, thmaille.*
 
# Pac-Man
 
## Description
 
A full recreation of the classic 1980 Pac-Man arcade game in Python,
built with an object-oriented, modular architecture.
 
The player eats every pacgum of a maze to clear a level, avoiding four
autonomous ghosts that chase, flee or head home depending on their
state. Super-pacgums placed in the four corners turn the ghosts edible
for a few seconds. Ten levels, each a freshly generated maze with its own
time limit, stand between the player and the victory screen, and the ten
best scores are kept between sessions.
 
Everything the game needs is configurable through a JSON file, the mazes
themselves come from an externally assigned `A-Maze-ing` package, and a
full cheat mode is available so a peer reviewer can exercise every
feature in a couple of minutes.
 
Only the **mandatory part** of the subject is implemented.
 
## Instructions
 
### Requirements
 
- Python 3.10 or later
- `pygame-ce` (Community Edition)
`pygame-ce` is used as the graphical library rather than vanilla
`pygame`, for better support of recent Python versions. Only primitives
that have a direct MLX equivalent are used: rectangle fill, line, circle
and text blit — no sprite system, no shader, no built-in physics.
 
> **macOS note**: `pygame` and `pygame-ce` must never be installed at the
> same time — both provide the `import pygame` namespace, and mixing
> them loads two copies of SDL2, which segfaults on macOS. `make install`
> uninstalls both before reinstalling the right one, so always install
> through `make install` rather than a bare `pip install`.
 
### Install
 
```bash
make install
```
 
### Run
 
```bash
make run
# equivalent to:
python3 pac-man.py config/config.json
```
 
The program takes **exactly one argument**: the path to a `.json`
configuration file. A missing file, malformed JSON or an invalid value is
handled cleanly, with a clear message and never a Python traceback
(subject V.1/V.3).
 
### Play without installing anything
 
The packaged build is published on itch.io as a free, restricted
(unlisted) page, as chapter VII requires:
 
**<https://sylvaincode.itch.io/pacman-42>**
 
The build is not code-signed, because signing requires a paid developer
account. macOS therefore blocks the first launch with *"Apple could not
verify that Pac-Man is free of malware"*. Two ways around it:
 
- open **System Settings > Privacy & Security**, scroll down and click
  **Open Anyway**; or
- run `xattr -dr com.apple.quarantine "Pac-Man.app"` once in a terminal.
Recent macOS versions no longer accept the older right-click > **Open**
workaround for this dialog. On Linux, run `chmod +x pacman` if the
executable bit was lost in the archive.
 
### Controls
 
| Key | Action |
|---|---|
| Arrow keys or `W` `A` `S` `D` | Move Pac-Man |
| `Escape` | Pause / resume |
| `Enter` | Confirm in menus |
| `Backspace` | Erase a character while typing your name |
 
Cheat-mode keys are listed in [Cheat mode](#cheat-mode).
 
### Development commands
 
```bash
make debug          # run the game under pdb
make lint           # flake8 + mypy with the subject's mandated flags
make lint-strict    # flake8 + mypy --strict
make clean          # remove caches and the local highscore file
make package        # build the standalone executable (chapter VII)
```
 
All three currently pass with zero error: `flake8`, `mypy` with the
mandated flags, and `mypy --strict`. The feature-by-feature acceptance
checklist is in
[`management/acceptance-tests.md`](./management/acceptance-tests.md).
 
## Configuration
 
The config file is JSON, extended so that whole-line comments starting
with `#` or `//` are ignored, as well as `/* ... */` blocks (V.2).
 
Robustness follows V.3 strictly: **every key is optional**. A missing or
invalid value falls back to the documented default and logs one clear
warning; unknown keys are ignored; the game never crashes and never
prints a traceback. Only a file that cannot be read or parsed at all
stops the program, with a one-line message.
 
| Key | Type | Default | Meaning |
|---|---|---|---|
| `highscore_filename` | string | `"highscores.json"` | Where highscores are persisted |
| `levels` *(or `level`)* | array of `{width, height}` | 10 mazes of 20x20 | One entry per level; auto-padded to at least 10 (VI.7), each side clamped to 5-99. Both spellings are accepted, because V.2 lists the suggested key in the singular while the natural name for a list is plural |
| `lives` | int ≥ 1 | `3` | Starting lives |
| `pacgum` | int ≥ 1 | `200` | Pacgums placed per level. A 20x20 maze offers 388 usable corridors, so 200 covers a bit over half of them (51.5%) — "most corridors", as VI.1/VI.4 require |
| `points_per_pacgum` | int ≥ 0 | `10` | Score per pacgum eaten |
| `points_per_super_pacgum` | int ≥ 0 | `50` | Score per super-pacgum eaten |
| `points_per_ghost` | int ≥ 0 | `200` | Score per edible ghost eaten |
| `seed` | int ≥ 0 | `42` | Fixed seed for level 1 (VI.1); later levels are random |
| `level_max_time` | int ≥ 10 | `130` | Seconds allowed per level, the same for every level |
| `cell_size` | int ≥ 8 | `24` | Base cell size in pixels (the maze is then scaled to the window) |
| `fullscreen` | bool | `true` | `true` opens a fullscreen display; `false` opens a resizable window, so the game can be closed with the window button |
| `player_speed` | int ≥ 1 | `5` | Player speed, in cells per second |
| `ghost_speed` | int ≥ 1 | `4` | Base ghost speed; each ghost then applies its own multiplier (0.85 to 1.10) according to its personality |
| `frightened_duration` | int ≥ 1 | `8` | Seconds ghosts stay edible after a super-pacgum |
| `ghost_respawn_delay` | int ≥ 1 | `7` | Seconds an eaten ghost waits before coming back |
 
A ready-to-use example is provided at `config/config.json`.
 
## Highscore
 
Highscores are stored as a flat JSON array of `{"name", "score"}` objects
in the file named by `highscore_filename`, handled by
`game/highscore.py`.
 
**Why this design.** The requirement is a small, local, persistent
top-10 board. A flat JSON file needs no external dependency and no
schema migration, is human-readable and diffable (which made debugging
trivial), and reuses the `json` module already required for the config
loader. A database or a binary format would have added dependencies and
opacity for zero benefit at this scale.
 
The board:
 
- loads at game start and tolerates a missing **or corrupted** file,
  falling back to an empty board instead of crashing;
- re-sanitizes every entry **on load**, not just on write, so a
  hand-edited file cannot inject an oversized name or a negative score;
- restricts names to alphanumeric characters and spaces, 10 max;
- rejects negative and non-integer scores;
- keeps only the top 10 entries, sorted descending;
- saves to disk each time a score is added;
- is displayed in the main menu, and the name is prompted for at the end
  of **every** game, win or lose (V.5).
In a packaged build the file is redirected to `~/.pacman42/`, because an
installed application folder may be read-only.
 
## Maze Generation
 
This project **never generates a maze itself**. Per V.4, level generation
is delegated entirely to the externally assigned `A-Maze-ing` package,
and all integration lives in `maze/adapter.py` — the only file in the
whole codebase that talks to that package.
 
Because the subject requires that *"your loader must adapt to their
interface, not the opposite"*, the adapter is deliberately tolerant:
 
1. **It finds the package.** Several import paths are tried in priority
   order, the assigned `mazegenerator` first. The chosen one is logged on
   the first level load. Setting `PACMAN_AMAZING_MODULE=<module>` forces
   a specific one without touching a line of code.
2. **It adapts to the constructor.** The class is instantiated through
   `inspect.signature`, so only the keyword arguments it actually
   declares are passed — width and height under any of their common
   names or packed into a single `size` tuple, the seed, and
   `perfect=False` when such a parameter exists, as V.4 requires for
   Pac-Man-compatible corridors.
3. **It reads the grid through whatever accessor exists** — `get_grid()`,
   `grid`, `to_grid()`, `get_maze()` or the `maze` property the assigned
   package exposes.
4. **It validates and copies.** Dimensions and every cell value (a
   `N=1, E=2, S=4, W=8` bitmask, 0-15) are checked before being copied
   into this project's own `maze.maze_model.Maze`, so the rest of the
   codebase never depends on the external package's data format and
   cannot be affected by it mutating its own state later.
5. **It fails cleanly.** A missing package, an unexpected interface or a
   malformed grid all become a single, clearly-worded
   `MazeGenerationError` that reaches the player without a traceback.
   There is deliberately **no** home-made fallback generator, since V.4
   forbids writing our own.
Level 1 always uses the configured fixed `seed` (default `42`); every
subsequent level uses a fresh random seed, per VI.1.
 
The package assigned to us is **`mazegenerator` 2.1.0**, shipped as a
wheel at the repository root and installed by `make install`. Two of its
traits required work on our side, and both are handled in the adapter and
in `game/level.py` rather than by touching their code, as V.4 demands:
 
- **It takes both dimensions in a single tuple**, `size=(width, height)`,
  instead of two parameters. The adapter detects this through
  `inspect.signature` and packs them accordingly.
- **It walls off a decorative "42" pattern** — 18 sealed cells — right in
  the middle of the maze, which is exactly where VI.1 puts the player. A
  naive reading spawned Pac-Man inside a sealed cell, unable to move, and
  made every level unfinishable. The level builder now computes the
  largest connected region of the maze and anchors the player, the four
  ghosts and every pacgum inside it, so nothing can spawn walled off.
## Cheat mode
 
Available at any time during gameplay, with the full legend permanently
visible in the top-right corner of the screen and on the Instructions
screen, so a reviewer never has to look anything up. Every feature
suggested by VI.5 is implemented:
 
| Key | Cheat |
|---|---|
| `Z` | Skip the current level (counts as cleared) |
| `E` | Freeze / unfreeze every ghost |
| `I` | Toggle invincibility — no life is ever lost |
| `L` | Grant one extra life |
| `P` | Toggle the x2 player speed boost |
 
Letter keys are used rather than `F1`-`F5` because function keys are
captured by the system on most macOS setups at 42.
 
## Implementation
 
- **Language**: Python 3.10+, fully type-hinted, `pygame-ce` for
  rendering and input.
- **State machine** (`game/state.py`, `game/engine.py`): Main Menu →
  Playing → Paused / Game Over / Victory → Enter Name → back to Main
  Menu (chapter IV game loop), plus Instructions and Highscores screens.
- **Movement**: player and ghosts interpolate between grid cells at a
  configurable speed. A direction change is only accepted when the
  entity is exactly cell-aligned and the target corridor is open
  (VI.2/VI.3), and the destination cell is frozen at the moment the
  entity leaves an aligned cell — recomputing it from the in-between
  float position is what used to let entities clip through walls.
- **Pacgum placement**: `pacgum` corridors get a pacgum — 200 out of the
  388 usable cells of a 20x20 maze, so a bit over half (51.5%), which is
  what VI.1 and VI.4 mean by "in most corridors". 200 is the floor for
  that: below 194 the maze would hold pacgums in fewer than half of its
  corridors. They are **spread evenly** over the whole maze, by ordering
  the candidate cells by their distance from the player's start and
  taking one every *n* positions, so the maze reads as uniformly dotted
  instead of showing a dense blob around the start and bare outskirts.
- **Level sizing**: every level is a 20x20 maze; what changes from one
  level to the next is the maze itself, regenerated with a new random
  seed. The maze size, the pacgum count and the player speed were tuned
  together against `level_max_time` by simulating a "always head for the
  nearest remaining pacgum" walk: clearing a level takes 290 to 340
  moves depending on the layout, which at 5 cells per second leaves 28
  to 42 s of margin inside the 130 s limit once detours and dodging are
  accounted for.
- **Ghost AI** (`entities/ghost.py`, `maze/pathfinding.py`): VI.3 leaves
  the chase behaviour open, and the subject's own foreword describes the
  original ghosts as each having its own. So each of the four gets a
  distinct logic and a distinct aggressiveness rank, from 1 to 4:
  | Rank | Ghost | Behaviour | Speed |
  |---|---|---|---|
  | 4 | Blinky | BFS straight at the player's cell, relentlessly | x1.10 |
  | 3 | Pinky | aims 4 cells **ahead** of the player, to cut them off | x1.00 |
  | 2 | Inky | alternates chasing and wandering to a random cell every 3 s | x0.95 |
  | 1 | Clyde | chases from afar, retreats home within 5 cells | x0.85 |
  The multiplier applies on top of the configured `ghost_speed`, so a
  more aggressive ghost is also felt as more dangerous, not merely aimed
  differently. All four share the common states: they flee to the
  reachable neighbour furthest from the player while frightened (at 60%
  speed), and path back to their corner at double speed while eaten,
  waiting `ghost_respawn_delay` seconds there. They also alternate
  **scatter** (head home, 6 s) and **chase** (15 s) phases — without it,
  four simultaneous chasers could seal both ends of a corridor and make
  the game unwinnable regardless of skill.
- **"PRET !" start freeze**: every level start and every respawn opens
  with a short freeze (nothing moves, the level timer is paused). Not
  required by VI.7, but it mirrors the arcade's "READY!" screen and
  stops a level from ever resuming with a ghost already on the player.
- **Level timeout**: VI.7 leaves this open ("you can decide what
  happens"). The choice here is to cost one life and restart the same
  level, exactly like touching a ghost — ending a 10-level run on a
  single timeout felt disproportionate.
- **Error handling**: `pac-man.py` wraps the whole engine in a top-level
  safety net that prints a one-line message and exits `1`. The detailed
  traceback is only emitted at debug log level, so the player never sees
  one (V.1).
- **Packaging**: PyInstaller spec at the repository root, embedding the
  default config so the built executable can be launched by
  double-clicking. See [Project Management](#project-management).
## General Software Architecture
 
```
pac-man.py             entry point: CLI parsing, config load, error safety net
config/                JSON-with-comments loader, validation/clamping, defaults
  loader.py              GameConfig, LevelConfig, load_config()
  defaults.py            DEFAULT_CONFIG, MIN_LEVELS
maze/                  everything maze-related
  adapter.py             ONLY file importing the external A-Maze-ing package
  maze_model.py          internal Maze (A-Maze-ing bitmask grid) + helpers
  pathfinding.py         BFS next-step and flee helpers
entities/              Player, Ghost (+ GhostMode), Pickup
game/                  GameState enum, Level builder, GameEngine (loop + rules),
                       HighscoreBoard, CheatState
ui/                    Renderer (pygame primitives only), menu screens,
                       HUD / pause / end-game / name-entry screens
management/            project management artifacts
```
 
**Dependency direction** is strictly one-way, which is what keeps the
project modular:
 
```
pac-man.py  ->  game.engine  ->  game.level  ->  maze.adapter  ->  A-Maze-ing
                    |               |
                    |               +->  entities.*  ->  maze.maze_model
                    +->  ui.*       +->  maze.maze_model
                    +->  game.highscore / game.cheat
```
 
`GameEngine` is the single orchestrator: it owns the current
`GameState`, delegates drawing to `ui/`, physics and AI updates to
`entities/`, level assembly to `game/level.py` (which itself calls
`maze/adapter.py`), and score persistence to `game/highscore.py`.
Nothing outside `maze/adapter.py` ever imports the external `A-Maze-ing`
package, so V.4's "adapt to their interface" constraint stays isolated
to one file, and nothing outside `ui/` ever imports `pygame`.
 
## Project Management
 
See [`management/`](./management) for the full set of documents:
 
| Document | Content |
|---|---|
| [`timeline.md`](./management/timeline.md) | Planned phases, actual duration, variance analysis, remaining work |
| [`team-organization.md`](./management/team-organization.md) | Who did what, how decisions were made and how issues were handled |
| [`risk-analysis.md`](./management/risk-analysis.md) | Risks, likelihood, impact and the mitigation actually in place |
| [`acceptance-tests.md`](./management/acceptance-tests.md) | Test plan, feature-by-feature checklist, bugs found and fixed |
| [`blocking-points.md`](./management/blocking-points.md) | Real blocking issues hit during development |
| [`packaging-notes.md`](./management/packaging-notes.md) | Platform choice, how to rebuild and publish, how to swap in the assigned A-Maze-ing package |
 
### Packaging (chapter VII)
 
The target platform is **itch.io**, because publishing there is free and
it natively supports *restricted* (unlisted) pages, which is exactly the
"free but unlisted/private build" the subject asks for.
 
```bash
make package     # standalone executable in dist/
```
 
The packaging spec (`pacman.spec`) is at the repository root, as
required. The *"minimal in-package instructions (controls, options,
configuration)"* are the game's own Instructions screen, reachable from
the main menu: it documents the controls, the rules, the cheat keys and
every configuration key with its current value, so the documentation
ships with the build and can never drift from it.
 
The published page is <https://sylvaincode.itch.io/pacman-42>. To
reproduce or update it: create the page (Downloadable / No payments /
**Restricted**), run `butler login` once, then
 
```bash
make lint && make package
rm -rf release && mkdir -p release/pacman-osx
cp -R dist/Pac-Man.app release/pacman-osx/
cp config/config.json   release/pacman-osx/
butler push release/pacman-osx sylvaincode/pacman-42:osx --userversion 1.0.0
```
 
PyInstaller cannot cross-compile, so each operating system is built on
that system and pushed to its own itch.io channel: `:osx` from macOS and
`:linux` from Linux, where `dist/pacman/` replaces `dist/Pac-Man.app`.
itch.io then serves the right download to each visitor.
 
## Resources
 
- [Pac-Man ghost behaviour — The Pac-Man Dossier](https://pacman.holenet.info/)
  for the scatter/chase alternation and the original ghost personalities.
- [Maze generation algorithms — Wikipedia](https://en.wikipedia.org/wiki/Maze_generation_algorithm)
  for understanding the wall-bitmask representation A-Maze-ing produces.
- [Breadth-first search — Wikipedia](https://en.wikipedia.org/wiki/Breadth-first_search)
  for the ghost pathfinding.
- [pygame-ce documentation](https://pyga.me/docs/) — event loop, drawing
  primitives, font rendering.
- [Python `dataclasses`](https://docs.python.org/3/library/dataclasses.html),
  [`typing`](https://docs.python.org/3/library/typing.html) and
  [`inspect`](https://docs.python.org/3/library/inspect.html) documentation —
  the last one for signature-based adaptation in `maze/adapter.py`.
- [PEP 257 — Docstring conventions](https://peps.python.org/pep-0257/).
- [PyInstaller documentation](https://pyinstaller.org/en/stable/) and
  [itch.io butler](https://itch.io/docs/butler/) for chapter VII.
### AI usage
 
The gameplay core was written by us: ghost AI, player movement, the maze
model, BFS pathfinding and the rendering layer, along with every
game-design choice the subject leaves open (chase behaviour, timeout
behaviour, highscore format, isolating A-Maze-ing in a single adapter).
 
An AI assistant was used for: boilerplate in the config loader, the
signature-introspection code inside `maze/adapter.py`, the safe bounds
applied to configuration values, the PyInstaller spec, and part of this
README and of the `management/` documents. It was also used to review
the finished project against the subject, which is how the pacgum
density, an unbounded maze dimension and a leaking traceback were found.
 
Every AI-drafted block was read, adapted and validated by `flake8` and
`mypy --strict` before being kept.
 