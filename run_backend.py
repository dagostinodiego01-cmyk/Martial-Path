"""Standalone entry point for the packaged Martial Path backend.

Serves the FastAPI engine API on ``http://127.0.0.1:8000`` so the exported Godot
game can drive the Python engine with no separate Python install. This is the
script PyInstaller freezes into ``MartialPathBackend.exe`` (see ``backend.spec``);
the game auto-launches that executable on start-up.

It is a process entry point only -- it holds no game rules. The engine remains
the single source of truth (``game/api/server.py``).

For local development you normally run uvicorn directly instead:

    .venv\\Scripts\\python.exe -m uvicorn game.api.server:app --host 127.0.0.1 --port 8000
"""
from __future__ import annotations

import multiprocessing
import os
import sys

HOST = "127.0.0.1"
PORT = 8000


def _ensure_std_streams() -> None:
    """Guarantee ``sys.stdout``/``sys.stderr`` exist.

    A windowed PyInstaller build (``console=False``) leaves both set to ``None``.
    Libraries that inspect the stream -- uvicorn's log formatter calls
    ``sys.stdout.isatty()`` -- then crash on start-up. Point them at a null sink so
    the frozen server runs silently instead of raising.
    """
    if sys.stdout is None:
        sys.stdout = open(os.devnull, "w", encoding="utf-8")
    if sys.stderr is None:
        sys.stderr = open(os.devnull, "w", encoding="utf-8")


def main() -> None:
    import uvicorn

    from game.api.server import app

    # Pass the app object directly and pin the loop/protocol so the frozen build
    # never needs uvicorn's dynamic (reload/uvloop/httptools/websockets) paths.
    uvicorn.run(app, host=HOST, port=PORT, log_level="warning", loop="asyncio", http="h11")


if __name__ == "__main__":
    # Required so a frozen executable never re-bootstraps itself if a child
    # process is ever spawned (harmless no-op for the single-process server).
    multiprocessing.freeze_support()
    _ensure_std_streams()
    main()
