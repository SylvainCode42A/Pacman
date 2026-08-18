# Team Organization

Project carried out as a pair at 42: **slidriss** and **bgranier** — the
same pair that delivered the `A-Maze-ing` project, which made the maze
integration easier to reason about since both of us already knew the
wall-bitmask format.

## Who did what

| Member | Responsibilities |
|---|---|
| slidriss | Config loader and validation (V.2/V.3), maze adapter and internal maze model (V.4), highscore persistence (V.5), Makefile, packaging (VII) |
| bgranier | Game engine and state machine (IV/VI.7), player and ghost entities and AI (VI.2/VI.3), rendering and UI screens (VI.8), cheat mode (VI.5) |
| both | Architecture, code review of every module, acceptance testing, README and project-management documents |

## How decisions were made

The choices the subject leaves open were discussed between us before any
code was written, and the reasoning was recorded in the source as a
comment and in the README:

- **Ghost chase behaviour** (VI.3): BFS pathfinding as the shared base,
  for being deterministic and easy to explain, then one distinct logic
  and one distinct aggressiveness rank per ghost — the subject's own
  foreword describes the original four as behaving differently. The
  scatter/chase alternation was added later to fix a real playability
  bug.
- **Maze size, pacgum count and speeds**: tuned together rather than
  guessed. We simulated the number of moves needed to clear a level for
  several maze sizes, pacgum counts and layouts, and settled on 20x20
  mazes with 200 grouped pacgums at 8 cells per second, so that every
  level fits inside the 90 s limit with about 30 s of margin.
- **Level timeout** (VI.7): "lose one life and restart the level" rather
  than "end the game", which felt disproportionate over a 10-level run.
- **Highscore storage** (V.5): a flat JSON file — no dependency, human
  readable, and it reuses the `json` module the config loader needs.
- **Graphical library**: `pygame-ce`, restricted to primitives that all
  have a direct MLX equivalent.

## How issues were handled

Each problem was fixed by whoever owned the module, then reviewed by the
other before being merged. The blocking ones are documented in
[`blocking-points.md`](./blocking-points.md).

Both of us used an AI assistant, for scaffolding and review only, never
for game-design decisions. Every generated block was read, adapted and
tested by the member who owned that module, then re-explained to the
other during review. The disclosure required by chapter IX is in the
README.
