"""Meta-save service.

Persists *cross-run* state that outlives any single character: the Ancestral
Memory currency (earned on death/retirement, spent to unlock origins) and the
run chronicle (a graveyard of past runs). This is deliberately separate from the
run save in :class:`~game.services.save_service.SaveService` -- a permadeath run
is scoped to one save, while the meta-save survives every death.

Policy (what the data means) lives here; raw file I/O is a few small helpers.
The default path is ``%APPDATA%/MartialPath/meta.json`` on Windows, or
``~/.martialpath/meta.json`` elsewhere. Pass ``path`` explicitly in tests to keep
them isolated from the real meta-save.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

#: Bump when the meta-save schema changes in a backward-incompatible way.
META_VERSION = 1

#: Ancestral Memory banked on a death (retirement/ascension banks more later).
DEATH_REWARD = 10
#: Bonus Ancestral Memory per composite realm rank reached before death.
DEATH_REALM_BONUS = 1

#: Keep the chronicle bounded so a long-lived meta-save never grows unbounded.
MAX_CHRONICLE_ENTRIES = 100


class MetaService:
    """Reads and writes the cross-run meta-save."""

    def __init__(self, path: Optional[Any] = None) -> None:
        self._path = Path(path) if path else self._default_path()

    @property
    def path(self) -> Path:
        """The on-disk meta-save location."""
        return self._path

    @staticmethod
    def _default_path() -> Path:
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return Path(base) / "MartialPath" / "meta.json"

    @staticmethod
    def _empty() -> Dict[str, Any]:
        return {"version": META_VERSION, "ancestral_memory": 0, "chronicle": []}

    def load(self) -> Dict[str, Any]:
        """Load the meta-save, returning sane defaults when absent/corrupt."""
        if not self._path.exists():
            return self._empty()
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return self._empty()
        if not isinstance(data, dict):
            return self._empty()
        data.setdefault("ancestral_memory", 0)
        if not isinstance(data.get("chronicle"), list):
            data["chronicle"] = []
        return data

    def save(self, data: Dict[str, Any]) -> None:
        """Persist the meta-save (creating the directory as needed)."""
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = dict(data)
        payload["version"] = META_VERSION
        self._path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    # -- Ancestral Memory -------------------------------------------------
    def memory(self) -> int:
        """Return the current Ancestral Memory balance."""
        return int(self.load().get("ancestral_memory", 0))

    def add_memory(self, amount: int) -> int:
        """Credit ``amount`` Ancestral Memory and return the new balance."""
        data = self.load()
        data["ancestral_memory"] = max(0, int(data.get("ancestral_memory", 0)) + int(amount))
        self.save(data)
        return int(data["ancestral_memory"])

    def spend_memory(self, amount: int) -> bool:
        """Deduct ``amount`` Ancestral Memory; return ``False`` if unaffordable."""
        data = self.load()
        balance = int(data.get("ancestral_memory", 0))
        if balance < int(amount):
            return False
        data["ancestral_memory"] = balance - int(amount)
        self.save(data)
        return True

    # -- chronicle --------------------------------------------------------
    def record_run(self, entry: Dict[str, Any]) -> None:
        """Append a run record to the chronicle, keeping the most recent only."""
        data = self.load()
        data["chronicle"].append(dict(entry))
        data["chronicle"] = data["chronicle"][-MAX_CHRONICLE_ENTRIES:]
        self.save(data)

    def chronicle(self) -> List[Dict[str, Any]]:
        """Return the run chronicle (most recent last)."""
        return [dict(entry) for entry in self.load().get("chronicle", [])]

    def state(self) -> Dict[str, Any]:
        """Return the full meta-save snapshot (memory + chronicle)."""
        data = self.load()
        return {
            "ancestral_memory": int(data.get("ancestral_memory", 0)),
            "chronicle": [dict(entry) for entry in data.get("chronicle", [])],
        }
