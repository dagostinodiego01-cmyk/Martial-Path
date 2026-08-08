"""Application layer: translation between human input and engine commands.

This layer is deliberately thin. It knows the *vocabulary* a player may type and
maps it to the canonical :class:`~core.constants.Action` identifiers the engine
understands. It performs no gameplay logic and no I/O — the UI reads raw text and
hands it here; the engine receives only clean, structured commands.
"""
