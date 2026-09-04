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

    def definitions(self) -> List[Dict[str, Any]]:
        """The raw realm definitions (for codex/lore composition views)."""
        return [dict(entry) for entry in self._definitions]

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

    def generate_endless(
        self,
        depth: int,
        enemy_pool: List[str],
        named_pool: Optional[List[str]] = None,
        treasure_pool: Optional[List[Dict[str, Any]]] = None,
        essence_order: int = 1,
        rng: Any = None,
        foe_orders: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Any]:
        """Generate a procedural endless realm at ``depth`` (ROADMAP D.5).

        Endless realms never exhaust: every depth builds a fresh room list from
        the live world's pools -- ordinary foes from ``enemy_pool``, with a
        chance of drawing a *named* foe from ``named_pool`` -- and a boss whose
        tier grows with depth. Stats scale as ``1 + 0.15 * (depth - 1)`` and
        rewards as ``1 + 0.25 * (depth - 1)``, so the road keeps demanding
        more. Deterministic per (rng, depth): the same seed replays the same
        realm at the same depth.
        """
        depth = max(1, int(depth))
        use_rng = rng if rng is not None else self._rng
        definitions = self._endless_definitions(named_pool, foe_orders)
        scale = 1.0 + 0.15 * (depth - 1)
        reward_scale = 1.0 + 0.25 * (depth - 1)
        names = [
            "the Nameless Hollow",
            "the Sunken Vault of Echoes",
            "the Ninth Mirror Garden",
            "the Sea of Severed Names",
            "the Bone Orchard of Fallen Stars",
            "the Palace of Rusting Laws",
            "the Ember Wastes Beyond Memory",
            "the Library of Buried Heavens",
        ]
        display_name = str(names[(depth - 1) % len(names)])
        room_count = min(9, 5 + (depth - 1) // 3)
        treasure_rooms = 1 + (depth - 1) // 4
        rest_rooms = 1
        normal = max(1, room_count - treasure_rooms - rest_rooms)
        kinds = [ROOM_ENCOUNTER] * normal + [ROOM_TREASURE] * treasure_rooms + [ROOM_REST] * rest_rooms
        shuffled = list(kinds)
        if use_rng is not None:
            for i in range(len(shuffled) - 1, 0, -1):
                j = use_rng.randint(0, i)
                shuffled[i], shuffled[j] = shuffled[j], shuffled[i]
        rooms: List[Dict[str, Any]] = []
        named = [str(entry) for entry in (named_pool or []) if entry]
        # Encounters draw from the *depth-appropriate* slice of the pools: the
        # shallow road is populated by shallow foes, and named heavyweights
        # only descend once the road reaches their realm.
        mook_pool = self._gate_mook_pool(enemy_pool, definitions, depth)
        named_pool = self._gate_named_pool(named, definitions, depth)
        for kind in shuffled:
            if kind == ROOM_ENCOUNTER:
                enemy_id = self._pick_endless_enemy(mook_pool, named_pool, use_rng)
                rooms.append(
                    {
                        "kind": kind,
                        "enemy_id": enemy_id,
                        "named": enemy_id in named_pool,
                        "scale": round(scale, 3),
                    }
                )
            elif kind == ROOM_TREASURE:
                rooms.append(
                    {
                        "kind": kind,
                        "item_id": self._pick_endless_treasure(treasure_pool or [], use_rng),
                        "count": 1,
                    }
                )
            else:
                rooms.append({"kind": kind})
        boss_id = self._pick_endless_boss(
            named_pool or [], essence_order, depth, use_rng, definitions
        )
        rooms.append({"kind": ROOM_BOSS, "enemy_id": boss_id, "named": True, "scale": round(scale, 3)})
        return {
            "id": f"endless_{depth}",
            "display_name": display_name,
            "description": (
                f"Depth {depth} of the endless road: a realm that was never mapped, "
                "folded out of the world's leftovers by laws that forgot their authors."
            ),
            "depth": depth,
            "scale": round(scale, 3),
            "final_reward": {
                "exp": int(round(200 * reward_scale)),
                "gold": int(round(150 * reward_scale)),
            },
            "rooms": rooms,
        }

    def _endless_definitions(
        self,
        named_pool: List[str],
        foe_orders: Optional[Dict[str, int]] = None,
    ) -> Dict[str, Dict[str, Any]]:
        """Realm metadata for the foe pools (id -> realm-tier info).

        ``foe_orders`` (foe id -> essence-realm order) comes from the engine's
        cultivation ladder; foes absent from it resolve to order 1, so unknown
        or wildlife foes are available at every depth.
        """
        info: Dict[str, Dict[str, Any]] = {}
        for entry in self._definitions:
            info[str(entry.get("id", ""))] = entry
        for foe_id in named_pool:
            if foe_id not in info:
                info[foe_id] = {}
        for foe_id, order in (foe_orders or {}).items():
            info.setdefault(str(foe_id), {})["_essence_order"] = int(order)
        return info

    def _gate_mook_pool(
        self, enemy_pool: List[str], definitions: Dict[str, Dict[str, Any]], depth: int
    ) -> List[str]:
        """The depth-appropriate slice of the mook pool for endless rooms.

        Without gating, a depth-1 road can roll the campaign's final-boss tier;
        with it, shallow depths draw shallow foes and every tier of the
        catalogue stays relevant at some depth. Mooks without realm info stay
        available at all depths (wildlife is everywhere).
        """
        gated: List[str] = []
        for foe_id in enemy_pool:
            entry = definitions.get(foe_id) or {}
            order = int(entry.get("_essence_order", 0) or 0)
            if order <= 1 or depth >= max(1, order - 2):
                gated.append(foe_id)
        return gated or list(enemy_pool)

    def _gate_named_pool(
        self, named_pool: List[str], definitions: Dict[str, Dict[str, Any]], depth: int
    ) -> List[str]:
        """The depth-appropriate slice of the named-foe pool (as for mooks)."""
        gated: List[str] = []
        for foe_id in named_pool:
            entry = definitions.get(foe_id) or {}
            order = int(entry.get("_essence_order", 0) or 0)
            if order <= 1 or depth >= max(1, order - 2):
                gated.append(foe_id)
        return gated or list(named_pool)

    def _pick_endless_enemy(
        self, enemy_pool: List[str], named_pool: List[str], rng: Any
    ) -> str:
        """Draw an endless encounter foe: mostly mooks, sometimes a named foe."""
        ids = [str(entry) for entry in enemy_pool if entry]
        pool: List[str] = ids + [entry for entry in named_pool if rng is not None]
        if not pool:
            return ""
        if rng is None or len(pool) == 1:
            return pool[0]
        # Weight named foes lightly (1 in ~4 encounters at most).
        weights = [1.0] * len(ids) + [0.35] * len(named_pool)
        return str(rng.weighted_choice(pool, weights))

    def _pick_endless_treasure(
        self, treasure_pool: List[Dict[str, Any]], rng: Any
    ) -> str:
        """Draw endless treasure from a weighted ``{item_id, weight}`` pool."""
        entries = [entry for entry in treasure_pool if isinstance(entry, dict) and entry.get("item_id")]
        if not entries:
            return ""
        ids = [str(entry["item_id"]) for entry in entries]
        weights = [float(entry.get("weight", 1)) for entry in entries]
        if rng is None or len(ids) == 1:
            return ids[0]
        return str(rng.weighted_choice(ids, weights))

    def _pick_endless_boss(
        self,
        named_pool: List[str],
        essence_order: int,
        depth: int,
        rng: Any,
        definitions: Optional[Dict[str, Dict[str, Any]]] = None,
    ) -> str:
        """Choose an endless boss whose tier grows with the road's depth.

        Bosses are drawn from the named-foe catalogue, gated by realm: a boss
        appears once the road's depth reaches roughly the realm the foe
        embodies (a Life Destruction devil does not haunt depth 1). Depth
        scaling then handles the rest, so every tier stays relevant forever.
        """
        ids = [str(entry) for entry in named_pool if entry]
        if not ids:
            return ""
        if rng is None:
            return ids[0]
        definitions = definitions or {}
        allowed: List[str] = []
        for foe_id in ids:
            order = int(definitions.get(foe_id, {}).get("_essence_order", 1) or 1)
            if order > 1:
                # Tier-gated: the road must reach the foe's world first.
                if depth >= max(1, order - 2):
                    allowed.append(foe_id)
            else:
                # Low-realm duelists can appear from the start.
                allowed.append(foe_id)
        if not allowed:
            allowed = ids
        return str(rng.choice(allowed))

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
