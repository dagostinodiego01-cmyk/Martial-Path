"""Save repository -- low-level persistence for save slots.

Owns *where* saves live (an OS-appropriate application-data directory), how slot
names map to files (sanitised so a slot can never escape the save directory), and
raw JSON read/write. It knows no save-schema versions and no game rules: it
round-trips whatever dict it is handed. Policy (versioning, validation) lives one
layer up in :class:`~game.services.save_service.SaveService`.

Saves default to ``%APPDATA%/MartialPath/saves`` on Windows (or ``~`` elsewhere).
The directory is created lazily on first write, so merely constructing the
repository has no filesystem side effects.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


class SaveRepository:
    """Reads and writes raw JSON save slots on disk."""

    def __init__(self, save_dir: Optional[Any] = None) -> None:
        self._dir = Path(save_dir) if save_dir else self._default_dir()

    @property
    def directory(self) -> Path:
        """The directory save slots are stored in."""
        return self._dir

    @staticmethod
    def _default_dir() -> Path:
        base = os.environ.get("APPDATA") or os.path.expanduser("~")
        return Path(base) / "MartialPath" / "saves"

    @staticmethod
    def _safe_slot(slot: str) -> str:
        """Sanitise a slot name so it can never escape the save directory."""
        cleaned = "".join(c for c in (slot or "") if c.isalnum() or c in ("_", "-"))
        return cleaned or "default"

    def path(self, slot: str) -> Path:
        """Return the on-disk path for ``slot`` (sanitised)."""
        return self._dir / f"{self._safe_slot(slot)}.json"

    def write_raw(self, slot: str, payload: Dict[str, Any]) -> Path:
        """Serialise ``payload`` to ``slot`` verbatim and return the file path."""
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self.path(slot)
        path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
        return path

    def read_raw(self, slot: str) -> Any:
        """Load and parse ``slot``; raise ``FileNotFoundError`` when absent."""
        path = self.path(slot)
        if not path.exists():
            raise FileNotFoundError(slot)
        return json.loads(path.read_text(encoding="utf-8"))

    def exists(self, slot: str) -> bool:
        """Return ``True`` when a save exists for ``slot``."""
        return self.path(slot).exists()

    def iter_slots(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Yield ``(slot_name, raw_data)`` for every readable slot file."""
        slots: List[Tuple[str, Dict[str, Any]]] = []
        if not self._dir.exists():
            return slots
        for path in sorted(self._dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict):
                slots.append((path.stem, data))
        return slots
