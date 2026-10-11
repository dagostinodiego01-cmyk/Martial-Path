"""Save repository -- low-level persistence for save slots.

Owns *where* saves live (an OS-appropriate application-data directory), how slot
names map to files (sanitised so a slot can never escape the save directory), and
raw JSON read/write. It knows no save-schema versions and no game rules: it
round-trips whatever dict it is handed. Policy (versioning, validation) lives one
layer up in :class:`~game.services.save_service.SaveService`.

Saves default to ``%APPDATA%/MartialPath/saves`` on Windows (or ``~``
elsewhere); the ``MARTIAL_PATH_SAVE_DIR`` environment variable overrides that
(used by portable installs and to keep the test suite hermetic). The directory
is created lazily on first write, so merely constructing the repository has no
filesystem side effects.

**Crash safety (SV.6):** writes are atomic and leave the previous save
recoverable. The payload is serialised *before* any file is touched, written to
a same-directory ``.json.tmp`` file and fsynced, the previous ``.json`` is moved
aside to ``.json.bak``, and only then does the temp file become the save. An
interrupted write therefore leaves either the new save, or the old save in
place, or the old save in ``.json.bak`` -- never a truncated file with no
recovery path. :meth:`read_raw` falls back to that backup when the primary file
is missing or unparseable.
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
        override = os.environ.get("MARTIAL_PATH_SAVE_DIR")
        if override:
            return Path(override)
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

    @staticmethod
    def _sibling(path: Path, suffix: str) -> Path:
        """A companion file for ``path`` that never matches the ``*.json`` glob."""
        return path.parent / (path.name + suffix)

    def backup_path(self, slot: str) -> Path:
        """Path of the previous-generation backup for ``slot``."""
        return self._sibling(self.path(slot), ".bak")

    def write_raw(self, slot: str, payload: Dict[str, Any]) -> Path:
        """Serialise ``payload`` to ``slot`` atomically and return the file path.

        Serialisation happens first, so an unserialisable snapshot fails without
        touching the existing save. See the module docstring for the ordering
        that makes every interruption recoverable.
        """
        data = json.dumps(payload, indent=2)  # fails before any file is touched
        self._dir.mkdir(parents=True, exist_ok=True)
        path = self.path(slot)
        tmp = self._sibling(path, ".tmp")
        backup = self._sibling(path, ".bak")
        try:
            with open(tmp, "w", encoding="utf-8") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            if path.exists():
                os.replace(path, backup)
            os.replace(tmp, path)
        except OSError:
            try:
                tmp.unlink(missing_ok=True)
            except OSError:
                pass
            raise
        return path

    def read_raw(self, slot: str) -> Any:
        """Load and parse ``slot``, falling back to the backup generation.

        Raises ``FileNotFoundError`` when neither the save nor its backup exists,
        and ``json.JSONDecodeError`` when both exist but neither parses -- the
        two errors :class:`SaveService` maps to ``SAVE_NOT_FOUND`` /
        ``SAVE_CORRUPT``.
        """
        path = self.path(slot)
        backup = self._sibling(path, ".bak")
        error: Exception
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                error = exc
        else:
            error = FileNotFoundError(slot)
        # An interrupted write can leave the previous generation as the only
        # valid file; recovering it beats reporting a corrupt save.
        if backup.exists():
            try:
                return json.loads(backup.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                pass
        raise error

    def exists(self, slot: str) -> bool:
        """Return ``True`` when a save exists for ``slot`` (or its backup)."""
        return self.path(slot).exists() or self.backup_path(slot).exists()

    def iter_slots(self) -> List[Tuple[str, Dict[str, Any]]]:
        """Yield ``(slot_name, raw_data)`` for every readable slot file.

        A slot whose primary file is missing (the crash window between the two
        replaces of an atomic write) still lists via its ``.json.bak`` backup.
        """
        slots: List[Tuple[str, Dict[str, Any]]] = []
        if not self._dir.exists():
            return slots
        seen: set = set()
        for path in sorted(self._dir.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict):
                slots.append((path.stem, data))
                seen.add(path.stem)
        for path in sorted(self._dir.glob("*.json.bak")):
            stem = path.name[: -len(".json.bak")]
            if stem in seen:
                continue
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if isinstance(data, dict):
                slots.append((stem, data))
        return slots
