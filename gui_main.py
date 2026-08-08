"""Root-level launcher for the graphical (PySide6) UI.

Convenience wrapper so the game can be started from the repository root:

    python gui_main.py

The canonical module form also works:

    python -m game.gui_main

All game code lives under ``game/``; this shim simply delegates to the package
entry point so the layered wiring stays in one place.

Requires PySide6 (``pip install PySide6``).
"""
from __future__ import annotations

from game.gui_main import main

if __name__ == "__main__":
    main()
