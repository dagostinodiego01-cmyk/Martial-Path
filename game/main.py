"""Entry point — the composition root.

``main`` wires the layers together and starts the UI. It contains no gameplay
logic and no input/output of its own: it constructs the engine (core), the
router (application), and the CLI (UI), then hands control to the UI loop.

Swapping the frontend is a one-line change here — replace ``CLIInterface`` with
another UI that speaks the same engine contract.

Run from the workspace root:

    python -m game.main

or use the root-level launcher:

    python main.py
"""
from __future__ import annotations

from game.application.command_router import CommandRouter
from game.core.game_engine import GameEngine
from game.ui.cli_interface import CLIInterface


def main() -> None:
    """Construct the layers and run the game."""
    engine = GameEngine.new_game()      # CORE: pure logic + state
    router = CommandRouter()            # APPLICATION: input -> actions
    ui = CLIInterface(engine, router)   # UI: input/output only
    ui.run()


if __name__ == "__main__":
    main()
