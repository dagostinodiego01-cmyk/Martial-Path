"""Save service -- save policy over a persistence backend.

Owns the save *schema version*, stamps it on write, validates it on read, and
translates raw persistence outcomes into stable, UI-translatable error codes via
:class:`SaveError`. All disk I/O is delegated to a
:class:`~game.persistence.save_repository.SaveRepository`, so a future cloud or
alternate backend only needs a new repository -- not new policy.

Reads migrate older schemas forward (see :meth:`SaveService.migrate`):

* **v1 → v2** -- the starting talents were renamed from the old Spiritual Root
  / Physique fields (``spiritual_root_id`` / ``physique_id``) to the stable ids
  ``martial_talent_id`` / ``body_talent_id``.
* **v2 → v3** -- v3 persists the run seed, every gameplay RNG stream, and the
  session-side world/cooldown/fate state that a deterministic continuation
  needs (``SV.5``). v2 saves predate all of it, so the migration installs the
  documented defaults: the loading engine keeps its own seed and stream states,
  and the run resumes with stable player/world state but *without* guaranteed
  bit-identical continuation.

Any other version (missing, 0, or from a future release) is rejected with
``SAVE_VERSION_MISMATCH`` rather than guessed at.
"""
from __future__ import annotations

import copy
import json
from pathlib import Path
from typing import Any, Dict, List, Optional

from game.persistence.save_repository import SaveRepository

#: Bump when the save schema changes in a backward-incompatible way.
SAVE_VERSION = 3


def _migrate_v1_to_v2(data: Dict[str, Any]) -> Dict[str, Any]:
    """v1 → v2: rename the starting-talent fields to their stable ids."""
    player = data.get("player")
    if isinstance(player, dict):
        if "martial_talent_id" not in player and "spiritual_root_id" in player:
            player["martial_talent_id"] = player.pop("spiritual_root_id")
        if "body_talent_id" not in player and "physique_id" in player:
            player["body_talent_id"] = player.pop("physique_id")
    return data


def _migrate_v2_to_v3(data: Dict[str, Any]) -> Dict[str, Any]:
    """v2 → v3: install the documented defaults for the new session fields.

    The load path also defaults each field defensively (an exported payload can
    skip a step), but the migration makes the shape explicit so a test per
    version can pin it.
    """
    data.setdefault("seed", None)
    data.setdefault("rng", {})
    data.setdefault("world_seed", {})
    data.setdefault("last_world_report", {})
    data.setdefault("cooldowns", {})
    data.setdefault("encounter_seq", 0)
    data.setdefault("fate", {"accepted": True, "pending": None})
    data.setdefault("active_realm", None)
    data.setdefault("tournament_active", False)
    data.setdefault("oath_stakes", None)
    data.setdefault("running", True)
    return data


#: ``MIGRATIONS[n]`` upgrades a version-``n`` save to version ``n + 1``.
MIGRATIONS = {
    1: _migrate_v1_to_v2,
    2: _migrate_v2_to_v3,
}


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
        """Stamp ``snapshot`` with the schema version and persist it to ``slot``.

        A snapshot that carries an *older* version (an imported portable save)
        is migrated forward first, so ``version`` can never mislabel stale data
        as current.
        """
        payload = dict(snapshot)
        if payload.get("version") is not None:
            payload = self.migrate(payload)
        payload["version"] = SAVE_VERSION
        try:
            return self._repo.write_raw(slot or "default", payload)
        except (OSError, TypeError, ValueError) as exc:
            raise SaveError("WRITE_FAILED") from exc

    @staticmethod
    def migrate(data: Dict[str, Any]) -> Dict[str, Any]:
        """Upgrade ``data`` to :data:`SAVE_VERSION` (or raise :class:`SaveError`).

        The input is not mutated. Unknown or absent versions raise
        ``SAVE_VERSION_MISMATCH``; a non-integer version raises ``SAVE_CORRUPT``.
        """
        if not isinstance(data, dict):
            raise SaveError("SAVE_CORRUPT")
        try:
            version = int(data.get("version", 0))
        except (TypeError, ValueError) as exc:
            raise SaveError("SAVE_CORRUPT") from exc
        if version == SAVE_VERSION:
            return data
        data = copy.deepcopy(data)
        while version < SAVE_VERSION:
            step = MIGRATIONS.get(version)
            if step is None:
                raise SaveError("SAVE_VERSION_MISMATCH")
            data = step(data)
            version += 1
        if version != SAVE_VERSION:
            # version > SAVE_VERSION: a save from a future release.
            raise SaveError("SAVE_VERSION_MISMATCH")
        data["version"] = SAVE_VERSION
        return data

    def read(self, slot: str) -> Dict[str, Any]:
        """Load, migrate, and validate a save slot, or raise :class:`SaveError`."""
        try:
            data = self._repo.read_raw(slot or "default")
        except FileNotFoundError as exc:
            raise SaveError("SAVE_NOT_FOUND") from exc
        except (OSError, json.JSONDecodeError) as exc:
            raise SaveError("SAVE_CORRUPT") from exc
        if not isinstance(data, dict):
            raise SaveError("SAVE_CORRUPT")
        return self.migrate(data)

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
