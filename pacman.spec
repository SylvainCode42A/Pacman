# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller spec for the standalone build (chapter VII).

Built with `make package`. Two points matter:

* `maze/adapter.py` imports the assigned A-Maze-ing package dynamically
  through `importlib`, which PyInstaller's static analysis cannot see, so
  `mazegenerator` is listed in `hiddenimports`. Without it the executable
  would start but fail on the first level.
* `config/config.json` is embedded, so the executable starts with no
  command-line argument, which is how a player launches it from the
  store page (see `pac-man.py::_bundled_config_path`).
"""

import sys

IS_MACOS = sys.platform == "darwin"

a = Analysis(
    ["pac-man.py"],
    pathex=[],
    binaries=[],
    datas=[
        # Default configuration, used when the packaged game is launched
        # without an argument (double-click). The in-package instructions
        # required by chapter VII are the game's own Instructions screen
        # (see ui/menu.py), so there is no documentation file to embed.
        ("config/config.json", "config"),
    ],
    hiddenimports=[
        # Assigned A-Maze-ing package (V.4) and its internal module.
        "mazegenerator",
        "mazegenerator.mazegenerator",
        # Project modules reached only through the state machine.
        "game.engine",
        "ui.renderer",
        "ui.menu",
        "ui.hud",
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[
        # Terminal front-end of A-Maze-ing: never imported by the game.
        "readchar",
        "tkinter",
        "mypy",
        "flake8",
    ],
    noarchive=False,
    optimize=0,
)

pyz = PYZ(a.pure)

# One-dir build: the executable sits next to its libraries instead of
# unpacking itself at launch. PyInstaller deprecates one-file together
# with a macOS .app bundle, because a bundle cannot be a single file and
# the self-extraction clashes with macOS security checks.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="pacman",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    # The game opens its own fullscreen window, so no terminal is shown to
    # the player. Startup problems are still reported cleanly (never as a
    # traceback) when the executable is launched from a shell.
    console=False,
    disable_windowed_traceback=True,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="pacman",
)

if IS_MACOS:
    app = BUNDLE(
        coll,
        name="Pac-Man.app",
        bundle_identifier="fr.42.pacman",
        info_plist={
            "CFBundleName": "Pac-Man",
            "CFBundleDisplayName": "Pac-Man",
            "CFBundleShortVersionString": "1.0.0",
            "CFBundleVersion": "1.0.0",
            "NSHighResolutionCapable": True,
            "LSApplicationCategoryType": "public.app-category.arcade-games",
        },
    )
