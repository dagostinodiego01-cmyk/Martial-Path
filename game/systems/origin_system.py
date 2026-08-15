"""Origin system.

Starting backgrounds (``data/origins.json``) shape a fresh cultivator: their
Dao, their opening techniques, and small stat adjustments. Each origin carries a
``cost`` in Ancestral Memory -- the meta currency earned across runs -- so
stronger or more exotic origins are unlocked over successive deaths.

This system is pure: it resolves origins and applies their modifiers to a
:class:`~game.models.player.Player`. Spending the meta currency is the engine's
job (this system never touches the meta-save).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# Player fields an origin's ``stat_modifiers`` may adjust (additively).
STAT_FIELDS = (
    "attack",
    "defense",
    "speed",
    "evasion",
    "comprehension",
    "body_strength",
    "soul_strength",
    "foundation_quality",
    "reputation",
    "morality",
    "gold",
    "max_hp",
    "max_qi",
)


class OriginSystem:
    """Resolves and applies starting origins."""

    def __init__(self, origins: Optional[List[Dict[str, Any]]] = None) -> None:
        self._by_id: Dict[str, Dict[str, Any]] = {
            str(entry["id"]): dict(entry) for entry in (origins or []) if entry.get("id")
        }

    def all(self) -> List[Dict[str, Any]]:
        """Return every origin definition (in data order)."""
        return [dict(entry) for entry in self._by_id.values()]

    def get(self, origin_id: Optional[str]) -> Optional[Dict[str, Any]]:
        """Return an origin definition, or ``None`` if unknown."""
        if not origin_id:
            return None
        entry = self._by_id.get(str(origin_id))
        return dict(entry) if entry is not None else None

    def cost(self, origin_id: Optional[str]) -> int:
        """Return an origin's Ancestral Memory cost (0 if unknown)."""
        entry = self.get(origin_id)
        return int(entry.get("cost", 0)) if entry else 0

    def default_id(self) -> str:
        """Return the free starting origin (first cost-0 origin, else the first)."""
        free = next((entry["id"] for entry in self._by_id.values() if int(entry.get("cost", 0)) == 0), None)
        if free is not None:
            return free
        return next(iter(self._by_id), "")

    def apply(self, player: Any, origin: Dict[str, Any]) -> Dict[str, Any]:
        """Apply an origin's starting modifiers to a freshly-built player.

        Returns a UI-safe summary (id, name, story hook). The player is mutated
        in place: Dao, starting techniques, and additive stat modifiers.
        """
        player.origin_id = str(origin.get("id"))
        if origin.get("dao_id"):
            player.dao_id = str(origin["dao_id"])
        if isinstance(origin.get("starting_skills"), list):
            player.skills = [str(skill_id) for skill_id in origin["starting_skills"]]
        modifiers = origin.get("stat_modifiers") or {}
        for field, delta in modifiers.items():
            if field in STAT_FIELDS:
                setattr(player, field, int(getattr(player, field)) + int(delta))
        # Starting a new run at full vigour: any max-pool increase also tops up.
        if "max_hp" in modifiers:
            player.hp = int(player.max_hp)
        if "max_qi" in modifiers:
            player.qi = int(player.max_qi)
        return {
            "origin_id": origin.get("id"),
            "display_name": origin.get("display_name", origin.get("id")),
            "story_hook": origin.get("story_hook", ""),
        }
