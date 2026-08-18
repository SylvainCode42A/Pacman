# Project Timeline and Progress Tracking

## Planned phases

| # | Phase | Content | Status |
|---|---|---|---|
| 1 | Setup | Repo structure, Makefile, `.gitignore`, config loader (V.2/V.3) | Done |
| 2 | Maze integration | Internal `Maze` model, A-Maze-ing adapter, BFS helpers (V.4) | Done |
| 3 | Core entities | Player movement, ghost AI, pickups (VI.2-VI.4) | Done |
| 4 | Game loop | State machine, levels, scoring, lives, timer (IV, VI.6, VI.7) | Done |
| 5 | UI | Menu, HUD, pause, game over / victory, name entry (VI.8) | Done |
| 6 | Highscore | Persistent JSON board, sanitization, top-10 (V.5) | Done |
| 7 | Cheat mode | Five toggles for peer review (VI.5) | Done |
| 8 | Quality | flake8 / mypy clean, acceptance checklist (III.1-III.3) | Done |
| 9 | Packaging | PyInstaller spec, itch.io deployment (VII) | Build done, upload pending |
| 10 | Review prep | Re-test with the officially assigned A-Maze-ing package | Pending |

## Variance against the plan

Phases 2 and 3 took longer than planned. Moving entities between cells
was the hard part: recomputing the destination from the interpolated
position let the player and the ghosts cross walls at high speed, and
fixing it required rethinking how a move is committed (see
`blocking-points.md`).

Phase 5 was faster than expected, because the renderer only needed
MLX-equivalent primitives — rectangle, line, circle, text — so there was
nothing complex to build.

Phase 8 also overran, mostly on reaching `mypy --strict` compliance and
on excluding the third-party `amazing/` package from our own lint scope
without weakening the checks on our code.

## Remaining work

1. **Upload to itch.io.** The build is finished and reproducible
   (`make lint && make package`); what is left is the account-level part
   that cannot be scripted — creating the page as a free *restricted*
   project and running `butler login` once. Commands in the README.
2. **Swap in the assigned A-Maze-ing package.** Not attributed to us yet.
   `maze/adapter.py` is written to pick it up with no code change; the
   procedure is in the README's "Maze Generation" section.
