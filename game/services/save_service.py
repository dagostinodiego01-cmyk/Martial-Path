"""Save service -- save policy over a persistence backend.

Owns the save *schema version*, stamps it on write, validates it on read, and
translates raw persistence outcomes into stable, UI-translatable error codes via
:class:`SaveError`. All disk I/O is delegated to a
:class:`~game.persistence.save_repository.SaveRepository`, so a future cloud or
alternate backend only needs a new repository -- not new policy.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from game.persistence.save_repository import SaveRepository

#: Bump when the save schema changes in a backward-incompatible way.
SAVE_VERSION = 2


class SaveError(Exception):
    """Raised when a save cannot be read or is incompatible.

    ``code`` is a stable, UI-translatable identifier (e.g. ``"SAVE_NOT_FOUND"``).
    """

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


class SaveService:
    """Versioned save/load policy over a :class:`SaveRepository`."""

    def __init__(
        self,
        save_dir: Optional[Any] = None,
        repository: Optional[SaveRepository] = None,
    ) -> None:
        self._repo = repository or SaveRepository(save_dir)

    def write(self, slot: str, snapshot: Dict[str, Any]) -> Path:
        """Stamp ``snapshot`` with the schema version and persist it to ``slot``."""
        payload = dict(snapshot)
        payload["version"] = SAVE_VERSION
        try:
            return self._repo.write_raw(slot or "default", payload)
        except OSError as exc:
            raise SaveError("WRITE_FAILED") from exc

    def read(self, slot: str) -> Dict[str, Any]:
        """Load and validate a save slot, or raise :class:`SaveError`."""
        try:
            data = self._repo.read_raw(slot or "default")
        except FileNotFoundError as exc:
            raise SaveError("SAVE_NOT_FOUND") from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise SaveError("SAVE_CORRUPT") from exc
        if not isinstance(data, dict):
            raise SaveError("SAVE_CORRUPT")
        if int(data.get("version", 0)) != SAVE_VERSION:
            raise SaveError("SAVE_VERSION_MISMATCH")
        return data

    def exists(self, slot: str) -> bool:
        """Return ``True`` when a save exists for ``slot``."""
        return self._repo.exists(slot or "default")

    def list_slots(self) -> List[Dict[str, Any]]:
        """Return UI-safe summaries for every readable save slot."""
        summaries: List[Dict[str, Any]] = []
        for stem, data in self._repo.iter_slots():
            player = data.get("player", {})
            summaries.append(
                {
                    "slot": stem,
                    "name": player.get("name", "Unknown"),
                    "realm": player.get("realm", ""),
                    "version": data.get("version", 0),
                }
            )
        return summaries
