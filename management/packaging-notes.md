# Packaging Notes (chapter VII)
 
## Chosen platform: itch.io
 
The subject allows "Steam/Itch.io or similar". We picked **itch.io**
because publishing is free (Steam charges a $100 fee per title) and it
natively supports **restricted** pages, which is exactly the "free but
unlisted/private build" the subject asks for.
 
## Building
 
```bash
make lint        # never ship code that does not pass the checks
make package     # -> dist/Pac-Man.app on macOS, dist/pacman/ elsewhere
```
 
`pacman.spec` at the repository root is the packaging spec required by
VII. Two details make the packaged build behave correctly:
 
1. **Hidden imports.** `maze/adapter.py` imports the A-Maze-ing package
   dynamically, through `importlib`, so PyInstaller's static analysis
   cannot see it. `mazegenerator` is therefore listed explicitly in the
   spec; without that the executable would start but fail as soon as a
   level is generated.
2. **Config without an argument.** V.1 requires exactly one CLI argument
   when running from source, and that is enforced. A frozen build is
   started by double-clicking, so `pac-man.py` falls back to the config
   embedded in the bundle **only** when `sys.frozen` is set.
3. **Writable highscore file.** An installed application folder may be
   read-only, so in a frozen build a bare `highscore_filename` is
   redirected to `~/.pacman42/`.
The *"minimal in-package instructions (controls, options, configuration)"*
required by VII are the game's own Instructions screen, reachable from
the main menu: it documents the controls, the rules, the cheat keys and
every configuration key with its current value, so the documentation
ships with the build and can never drift from it.
 
## Publishing
 
1. Create the page on <https://itch.io/game/new>: *Kind of project* =
   Downloadable, *Pricing* = No payments, *Visibility* = **Restricted**.
2. Get an API key at <https://itch.io/user/settings/api-keys>, install
   butler (<https://itch.io/docs/butler/installing.html>), run
   `butler login` once.
3. Assemble and push:
```bash
mkdir -p release/pacman-osx
cp -R dist/Pac-Man.app release/pacman-osx/      # dist/pacman/ on Linux/Windows
cp config/config.json   release/pacman-osx/
butler push release/pacman-osx <user>/<game-slug>:osx --userversion 1.0.0
```
 
The build uses PyInstaller's **one-dir** mode: the executable ships next
to its libraries rather than unpacking itself at every launch.
PyInstaller deprecates one-file together with a macOS `.app` bundle —
a bundle cannot be a single file, and the self-extraction clashes with
macOS security checks, which can prevent the app from launching at all.
 
`config/config.json` is copied next to the executable so a player can
edit the settings; a copy is also embedded inside the binary, so the
game still starts if that file is deleted.
 
### Unsigned build and macOS Gatekeeper
 
The executable is not code-signed, and signing requires a paid Apple
Developer account. On macOS, Gatekeeper therefore refuses the first
launch with *"Pac-Man cannot be opened because the developer cannot be
verified"*. This is expected for a free unlisted build and does not mean
the package is broken. Two ways around it, both to be written on the
itch.io page so a player — or a peer reviewer — is not blocked:
 
- right-click the app, choose **Open**, then confirm in the dialog; or
- run `xattr -dr com.apple.quarantine "Pac-Man.app"` once.
Windows SmartScreen shows an equivalent warning ("More info" then "Run
anyway"). Linux needs `chmod +x pacman` if the executable bit was lost
in the archive.
 
## The assigned A-Maze-ing package
 
The package assigned to us is `mazegenerator` 2.1.0. Its wheel sits at the
repository root and `make install` installs it, so `make install && make
run` is enough to play. It is used exactly as delivered — V.4 forbids
modifying it — and everything it required was absorbed on our side:
 
- its constructor takes `size=(width, height)` rather than two
  parameters, which `maze/adapter.py` handles through `inspect.signature`;
- it seals a decorative "42" pattern in the middle of the maze, where
  VI.1 puts the player, so `game/level.py` anchors the player, the ghosts
  and the pacgums inside the largest connected region.
Verified with the real package: all ten levels are fully playable, every
pacgum reachable, the four corners and the four ghosts reachable, with
28 to 42 s of margin inside the 130 s limit depending on the level.
 
If a future version changes its module or class name, no code change is
needed:
 
```bash
PACMAN_AMAZING_MODULE=their_module_name make run
```
 
The adapter calls the constructor through `inspect.signature`, so it
passes only the keyword arguments that class declares — including
`perfect=False`, as V.4 requires. There is deliberately **no** home-made
fallback generator: if the package is missing or broken, the game reports
a single clear `MazeGenerationError` and returns to the menu.
 
### If `pip install` does not make the package importable
 
Some A-Maze-ing `pyproject.toml` files declare no explicit package list,
so setuptools auto-discovery can ship the wrong directory and leave the
package non-importable. Diagnose with:
 
```bash
python3 -c "import mazegenerator"     # does the install actually work?
```
 
V.4 forbids repairing their packaging, so the workaround is to make their
source directory importable as-is:
 
```bash
PYTHONPATH=/path/to/their/package make run
```