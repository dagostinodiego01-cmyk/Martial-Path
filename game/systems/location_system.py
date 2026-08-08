"""Location system.

Owns the world map: which places exist and how they connect. The map is injected
from ``data/locations.json`` so content stays data-driven with stable IDs. This
system is read-only with respect to gameplay rules -- it validates adjacency and
produces UI-safe views, but it never prints text or mutates the player. The
engine owns ``player.current_location``; this system only answers questions
about the map.

Locations use a node-based schema (``display_name``, ``zone``, ``danger_level``,
``qi_density``, ``connected_locations``, ``npc_ids``, ``requirements``, ...).
Numeric ``danger_level``/``qi_density`` (0-10) are mapped to display labels here
so frontends can render either the number or a word without recomputing rules.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

# Legacy single-file maps used ``connections``/``name``; the node schema uses
# ``connected_locations``/``display_name``. Both are read so older data still loads.
_CONNECTION_KEYS = ("connected_locations", "connections")


def danger_label(level: Any) -> str:
    """Map a numeric ``danger_level`` (0-10) to a display word."""
    try:
        value = int(level)
    except (TypeError, ValueError):
        return str(level) if level else "Unknown"
    if value <= 0:
        return "Safe"
    if value <= 2:
        return "Low"
    if value <= 4:
        return "Moderate"
    if value <= 6:
        return "High"
    if value <= 8:
        return "Deadly"
    return "Lethal"


def qi_density_label(level: Any) -> str:
    """Map a numeric ``qi_density`` (0-10) to a display word."""
    try:
        value = int(level)
    except (TypeError, ValueError):
        return str(level) if level else "Unknown"
    if value <= 0:
        return "None"
    if value <= 1:
        return "Faint"
    if value <= 2:
        return "Poor"
    if value <= 4:
        return "Moderate"
    if value <= 6:
        return "Dense"
    if value <= 8:
        return "Rich"
    return "Saturated"


class LocationSystem:
    """Data-driven world map: lookup, adjacency, and UI views."""

    def __init__(self, locations: List[Dict[str, Any]]) -> None:
        self._locations: Dict[str, Dict[str, Any]] = {
            entry["id"]: entry for entry in (locations or [])
        }

    def exists(self, location_id: str) -> bool:
        """Return ``True`` when ``location_id`` is a known place."""
        return location_id in self._locations

    def get(self, location_id: str) -> Optional[Dict[str, Any]]:
        """Return the raw definition for ``location_id`` (or ``None``)."""
        return self._locations.get(location_id)

    def display_name(self, location_id: str) -> str:
        """Return the human-readable name for ``location_id``."""
        loc = self._locations.get(location_id, {})
        return loc.get("display_name", loc.get("name", location_id))

    def neighbors(self, location_id: str) -> List[str]:
        """Return the ids directly connected to ``location_id``."""
        loc = self._locations.get(location_id)
        if loc is None:
            return []
        return list(self._connections(loc))

    def npc_ids(self, location_id: str) -> List[str]:
        """Return the NPC ids anchored to ``location_id``."""
        loc = self._locations.get(location_id, {})
        return list(loc.get("npc_ids", []))

    def requirements(self, location_id: str) -> Dict[str, Any]:
        """Return the entry requirements for ``location_id`` (or ``{}``)."""
        loc = self._locations.get(location_id, {})
        return dict(loc.get("requirements", {}))

    def can_travel(self, from_id: str, to_id: str) -> bool:
        """Return ``True`` when ``to_id`` is a direct neighbour of ``from_id``."""
        origin = self._locations.get(from_id)
        if origin is None or to_id not in self._locations:
            return False
        return to_id in self._connections(origin)

    def view(self, location_id: str) -> Dict[str, Any]:
        """Return a UI-safe snapshot of a location and its exits."""
        loc = self._locations.get(location_id)
        if loc is None:
            return {"id": location_id, "name": "Unknown", "known": False}
        name = loc.get("display_name", loc.get("name", loc["id"]))
        danger_level = loc.get("danger_level", loc.get("danger"))
        qi_level = loc.get("qi_density")
        exits = [self._exit_brief(cid) for cid in self._connections(loc)]
        map_position = loc.get("map_position", {})
        return {
            "id": loc["id"],
            "name": name,
            "display_name": name,
            "zone": loc.get("zone", ""),
            "location_type": loc.get("location_type", ""),
            "tier": loc.get("tier", ""),
            "description": loc.get("description", ""),
            "danger_level": danger_level,
            "danger": danger_label(danger_level),
            "qi_density": qi_level,
            "qi_density_label": qi_density_label(qi_level),
            "resources": list(loc.get("resources", [])),
            "npc_ids": list(loc.get("npc_ids", [])),
            "available_systems": list(loc.get("available_systems", [])),
            "map_position": dict(map_position) if isinstance(map_position, dict) else {},
            "connections": exits,
            "known": True,
        }

    # -- internal helpers -------------------------------------------------
    @staticmethod
    def _connections(loc: Dict[str, Any]) -> List[str]:
        for key in _CONNECTION_KEYS:
            if key in loc:
                return loc.get(key) or []
        return []

    def _exit_brief(self, location_id: str) -> Dict[str, Any]:
        loc = self._locations.get(location_id, {})
        return {
            "id": location_id,
            "name": loc.get("display_name", loc.get("name", location_id)),
            "danger": danger_label(loc.get("danger_level", loc.get("danger"))),
        }

