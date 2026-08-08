"""HTTP API frontend for the Martial Path engine.

A thin FastAPI adapter that exposes the existing ``GameEngine`` over HTTP so a
Godot (or any) client can drive the game. Like every other frontend, this layer
contains NO game rules: it forwards structured commands to ``process_action`` and
returns the engine's structured result dictionaries unchanged.

Run (from the repository root):

    uvicorn game.api.server:app --reload

The engine is a single in-process instance (local, single-player). Bind only to
localhost and run a single worker; do not expose this to a network without adding
authentication. Native Godot builds need no CORS; for a Godot **Web** export, add
Starlette's ``CORSMiddleware``.
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI
from pydantic import BaseModel

from game.core.game_engine import GameEngine

app = FastAPI(title="Martial Path API")

# Single in-process game session (local, single-player).
engine = GameEngine.new_game()


class ActionRequest(BaseModel):
    """A command for the engine.

    ``action`` is required (an ``Action`` name such as ``"TRAIN"``); the rest are
    optional and only sent when relevant (e.g. ``item_id`` for ``USE_ITEM``,
    ``skill_id`` for ``USE_SKILL``). ``character_id`` / ``dialogue_choice`` are
    reserved for future systems and are ignored by the engine today.
    """

    action: str
    item_id: Optional[str] = None
    shop_id: Optional[str] = None
    quantity: Optional[int] = None
    skill_id: Optional[str] = None
    method_id: Optional[str] = None
    location_id: Optional[str] = None
    slot: Optional[str] = None
    character_id: Optional[str] = None
    dialogue_choice: Optional[str] = None
    raw: Optional[str] = None


class NewGameRequest(BaseModel):
    """Parameters for starting a fresh session."""

    player_name: str = "Daoist"
    seed: Optional[int] = None


class SaveRequest(BaseModel):
    """Target a named save slot."""

    slot: str = "default"


@app.get("/health")
def health() -> Dict[str, str]:
    """Liveness probe."""
    return {"status": "ok"}


@app.get("/state")
def get_state() -> Dict[str, Any]:
    """Return the full, UI-agnostic game-state snapshot."""
    return engine.get_game_state()


@app.post("/action")
def process_action(request: ActionRequest) -> Dict[str, Any]:
    """Forward a structured command to the engine and return its result dict."""
    command = request.model_dump(exclude_none=True)
    return engine.process_action(command)


@app.post("/new-game")
def new_game(request: NewGameRequest) -> Dict[str, Any]:
    """Reset the in-process engine and return the initial state."""
    global engine
    engine = GameEngine.new_game(player_name=request.player_name, seed=request.seed)
    return engine.get_game_state()


@app.post("/save")
def save_game(request: SaveRequest) -> Dict[str, Any]:
    """Persist the current session to a named slot."""
    return engine.save_game(request.slot)


@app.post("/load")
def load_game(request: SaveRequest) -> Dict[str, Any]:
    """Restore a session from a named slot and return the result."""
    return engine.load_game(request.slot)


@app.get("/saves")
def list_saves() -> Dict[str, Any]:
    """List available save slots with summary metadata."""
    return {"saves": engine.saves.list_slots()}


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)
