"""Developer-facing diagnostic logging.

This uses the standard :mod:`logging` module and is intended for debugging the
engine, NOT for player-facing output. Logging is a cross-cutting infrastructure
concern, so systems may log without violating the "no UI in the engine" rule:
logs go to stderr/handlers, never to the player as game text.
"""
from __future__ import annotations

import logging


def get_logger(name: str) -> logging.Logger:
    """Return a configured logger for ``name`` (idempotent)."""
    logger = logging.getLogger(f"cultivation.{name}")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(logging.Formatter("[%(levelname)s] %(name)s: %(message)s"))
        logger.addHandler(handler)
        logger.setLevel(logging.WARNING)
    return logger
