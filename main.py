"""Root-level launcher for the CLI version of Martial Path.

Convenience wrapper so the game can be started from the repository root:

    python main.py

The canonical module form also works:

    python -m game.main

All game code lives under ``game/``; this shim simply delegates to the package
entry point so the layered wiring stays in one place.
"""
from __future__ import annotations

from game.main import main

if __name__ == "__main__":
    main()
