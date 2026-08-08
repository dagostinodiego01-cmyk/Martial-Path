"""Graphical entry point - the composition root for the PySide6 UI.

Like ``main.py`` (the CLI entry point), this wires the layers together and starts
a frontend. It swaps ONLY the UI: the engine, systems, models, and data are used
completely unchanged, which is the whole point of the layered architecture.

Run from the workspace root:

    python -m game.gui_main

or use the root-level launcher:

    python gui_main.py

Requires PySide6 (``pip install PySide6``).
"""
from __future__ import annotations

import sys

from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QApplication

from game.core.game_engine import GameEngine
from game.ui.gui_interface import GUIInterface, martial_path_icon_path


def main() -> None:
    """Construct the Qt application, engine, and window, then run the UI loop."""
    app = QApplication(sys.argv)
    icon_path = martial_path_icon_path()
    if icon_path:
        app.setWindowIcon(QIcon(icon_path))
    engine = GameEngine.new_game()      # CORE: pure logic + state (unchanged)
    window = GUIInterface(engine)       # UI: Qt frontend over the same engine
    window.show()
    window.start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
