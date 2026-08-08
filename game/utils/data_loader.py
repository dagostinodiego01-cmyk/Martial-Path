"""JSON content loading.

Loads data files from the sibling ``data/`` directory using a path resolved
relative to this module. This lets the game be launched from any working
directory (``python game/main.py`` or ``python main.py`` both work).

Two access patterns are supported:

* :func:`load_json` reads a single named file (objects or lists).
* :func:`load_collection` reads a *list* collection by logical name, transparently
  merging a folder of grouped files (e.g. ``data/characters/*.json``) so large
  content sets can be split for maintainability without changing consumers.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, List

# game/utils/data_loader.py -> game/data
DATA_DIR = Path(__file__).resolve().parent.parent / "data"


def load_json(filename: str) -> Any:
    """Load and parse a JSON file from the data directory."""
    path = DATA_DIR / filename
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_collection(name: str) -> List[Any]:
    """Load a list-collection by logical ``name``.

    If a directory ``data/<name>/`` exists, the JSON *lists* from every
    ``*.json`` file inside it are merged (in filename order) into one list. This
    lets a large collection be split into grouped files (by faction, region,
    tier, ...) without any consumer needing to know how many files back it.

    Otherwise ``data/<name>.json`` is loaded directly. The result is always a
    list; a non-list file or folder entry is a data error and raises.
    """
    directory = DATA_DIR / name
    if directory.is_dir():
        merged: List[Any] = []
        for path in sorted(directory.glob("*.json")):
            with path.open("r", encoding="utf-8") as handle:
                data = json.load(handle)
            if not isinstance(data, list):
                raise ValueError(f"{name}/{path.name}: expected a JSON list, got {type(data).__name__}")
            merged.extend(data)
        return merged

    data = load_json(f"{name}.json")
    if not isinstance(data, list):
        raise ValueError(f"{name}.json: expected a JSON list, got {type(data).__name__}")
    return data

