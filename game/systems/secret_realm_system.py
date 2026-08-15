"""Procedural secret realm (seeded dungeon) generator.

A secret realm is a deterministic sequence of rooms drawn from a data
definition (``data/secret_realm.json`` — a *list* of hand-placed realms): a run
of *encounter* rooms (fights against the realm's enemy pool), a few *treasure*
and *rest* rooms, and a final *boss* room. Generation uses the run's seeded
``RNG``, so the same seed always produces the same layout while different seeds
diverge (ROADMAP D.2).

The generator is pure layout: it returns room descriptors and never mutates the
player or performs I/O. The engine owns entering a realm, stepping through it,
and resolving fights/loot through the normal combat and inventory systems.

Each realm opens at exactly one location; ``realm_available_at`` answers whether
a realm opens here and ``generate``/``description`` are location-scoped.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

ROOM_ENCOUNTER = "encounter"
ROOM_TREASURE = "treasure"
ROOM_REST = "rest"
ROOM_BOSS = "boss"


class SecretRealmSystem:
    """Seeded room generation for a catalogue of hand-placed realms."""

    def __init__(self, definitions: Optional[Any] = None, rng: Any = None) -> None:
        raw = definitions or []
        # Accept either a single realm dict (legacy callers) or a list.
        if isinstance(raw, dict):
            raw = [raw]
        self._definitions: List[Dict[str, Any]] = [
            dict(entry) for entry in raw if isinstance(entry, dict)
        ]
        self._rng = rng
        self._by_location: Dict[str, Dict[str, Any]] = {
            str(entry.get("location_id")): entry
            for entry in self._definitions
            if entry.get("location_id")
        }

    @property
    def count(self) -> int:
        """How many realms are defined (regardless of location)."""
        return len(self._definitions)

    def realm_ids(self) -> List[str]:
        """Every realm id in the catalogue."""
        return [str(entry.get("id", "")) for entry in self._definitions]

    def realm_available_at(self, location_id: str) -> bool:
        """Return ``True`` when a realm opens at ``location_id``."""
        return str(location_id) in self._by_location

    def definition_for(self, location_id: str) -> Optional[Dict[str, Any]]:
        """Return the realm definition that opens at ``location_id``, if any."""
        return self._by_location.get(str(location_id))

    def description(self, location_id: str = "") -> Dict[str, Any]:
        """Return a UI-safe brief for the realm that opens at ``location_id``."""
        entry = self._by_location.get(str(location_id), {})
        return {
            "id": entry.get("id", ""),
            "display_name": entry.get("display_name", entry.get("id", "")),
            "location_id": entry.get("location_id", ""),
            "description": entry.get("description", ""),
        }

    def generate(self, location_id: str = "") -> Dict[str, Any]:
        """Generate a deterministic room list for the realm at ``location_id``."""
        return self._generate_from(self._by_location.get(str(location_id), {}))

    def _generate_from(self, definition: Dict[str, Any]) -> Dict[str, Any]:
        enemy_pool = list(definition.get("enemy_pool", []))
        treasure_pool = list(definition.get("treasure_pool", []))
        boss_id = definition.get("boss_id", "")
        room_count = int(definition.get("room_count", 5))
        treasure_rooms = int(definition.get("treasure_rooms", 1))
        rest_rooms = int(definition.get("rest_rooms", 1))

        normal = max(0, room_count - treasure_rooms - rest_rooms)
        kinds = [ROOM_ENCOUNTER] * normal + [ROOM_TREASURE] * treasure_rooms + [ROOM_REST] * rest_rooms
        kinds = self._shuffle(kinds)

        rooms: List[Dict[str, Any]] = []
        for kind in kinds:
            if kind == ROOM_ENCOUNTER:
                rooms.append({"kind": kind, "enemy_id": self._pick_enemy(enemy_pool), "named": False})
            elif kind == ROOM_TREASURE:
                rooms.append({"kind": kind, "item_id": self._pick_treasure(treasure_pool), "count": 1})
            elif kind == ROOM_REST:
                rooms.append({"kind": kind})
        rooms.append({"kind": ROOM_BOSS, "enemy_id": boss_id, "named": True})

        return {
            "id": definition.get("id", ""),
            "display_name": definition.get("display_name", definition.get("id", "")),
            "description": definition.get("description", ""),
            "final_reward": dict(definition.get("final_reward", {})),
            "rooms": rooms,
        }

    # -- internal helpers -------------------------------------------------
    def _pick_enemy(self, pool: List[str]) -> str:
        ids = [str(entry) for entry in pool if entry]
        if not ids:
            return ""
        if self._rng is None or len(ids) == 1:
            return ids[0]
        return str(self._rng.choice(ids))

    def _pick_treasure(self, pool: List[Dict[str, Any]]) -> str:
        entries = [entry for entry in pool if isinstance(entry, dict) and entry.get("item_id")]
        if not entries:
            return ""
        ids = [str(entry["item_id"]) for entry in entries]
        weights = [float(entry.get("weight", 1)) for entry in entries]
        if self._rng is None or len(ids) == 1:
            return ids[0]
        return str(self._rng.weighted_choice(ids, weights))

    def _shuffle(self, items: List[str]) -> List[str]:
        """Fisher-Yates shuffle through the run's RNG (deterministic per seed)."""
        shuffled = list(items)
        if self._rng is None:
            return shuffled
        for i in range(len(shuffled) - 1, 0, -1):
            j = self._rng.randint(0, i)
            shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
        return shuffled
