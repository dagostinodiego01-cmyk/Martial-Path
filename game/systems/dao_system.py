"""Dao system.

Pure rules for the Dao / philosophy layer of combat:

* **Realm pressure** -- a higher cultivation realm suppresses a lower one. The
  composite rank is ``body_realm.order + (essence_realm.order - 1)`` so a fresh
  cultivator (``mortal`` body + ``houtian`` essence) ranks 0. A gap of
  ``SUPPRESS_GAP`` tiers or more scales the weaker side's stats down; a gap of
  ``YIELD_GAP`` or more makes the weaker side yield before the fight.
* **Dao counter-graph** -- some Daos overcome others. Attacking a Dao you counter
  deals bonus damage; attacking a Dao that counters you deals reduced damage.

No UI, no I/O: deterministic lookups over the ``daos`` catalogue and the realm
order maps, exactly like the other pure systems.
"""
from __future__ import annotations

from typing import Any, Dict, List

from game.core.constants import DEFAULT_DAO_ID

# A composite realm gap of this many tiers or more lets the stronger side
# suppress the weaker side's stats.
SUPPRESS_GAP = 2
# A composite realm gap of this many tiers or more makes the weaker side yield
# outright (resolved by the engine before any round is fought).
YIELD_GAP = 4
# Per-tier effectiveness lost by the suppressed side, starting one tier past
# ``SUPPRESS_GAP`` (so gap 2 -> 0.75, gap 3 -> 0.5).
SUPPRESS_STEP = 0.25
# The suppressed side never drops below this effectiveness.
SUPPRESS_FLOOR = 0.3
# Dao matchup multipliers applied to outgoing damage.
COUNTER_MULTIPLIER = 1.5
COUNTERED_MULTIPLIER = 0.75


class DaoSystem:
    """Realm-pressure and Dao-counter rules over the dao + realm catalogues."""

    def __init__(
        self,
        daos: List[Dict[str, Any]],
        body_realms: Dict[str, Any],
        essence_realms: Dict[str, Any],
    ) -> None:
        self._daos: Dict[str, Dict[str, Any]] = {
            entry["id"]: entry for entry in daos if entry.get("id")
        }
        self._body_order = {
            realm["id"]: int(realm.get("order", 0))
            for realm in body_realms.get("realms", [])
            if realm.get("id")
        }
        # Essence realms are 1-indexed (``houtian`` = 1); shift by one so a fresh
        # cultivator (``mortal`` body + ``houtian`` essence) ranks 0, not 1.
        self._essence_order = {
            realm["id"]: int(realm.get("order", 1)) - 1
            for realm in essence_realms.get("realms", [])
            if realm.get("id")
        }

    # -- lookups ---------------------------------------------------------
    def dao_ids(self) -> List[str]:
        return list(self._daos)

    def dao_name(self, dao_id: Any) -> str:
        entry = self._daos.get(dao_id)
        return str(entry["display_name"]) if entry else str(dao_id or "")

    def dao_view(self) -> List[Dict[str, Any]]:
        return [dict(entry) for entry in self._daos.values()]

    def has_dao(self, dao_id: Any) -> bool:
        return dao_id in self._daos

    # -- realm rank ------------------------------------------------------
    def body_rank(self, body_realm_id: Any) -> int:
        return self._body_order.get(body_realm_id, 0)

    def essence_rank(self, essence_realm_id: Any) -> int:
        if not essence_realm_id:
            return 0
        return max(0, self._essence_order.get(essence_realm_id, 0))

    def realm_rank(self, body_realm_id: Any, essence_realm_id: Any) -> int:
        return self.body_rank(body_realm_id) + self.essence_rank(essence_realm_id)

    def player_rank(self, player: Any) -> int:
        return self.realm_rank(
            player.cultivation_state.body.realm_id,
            player.cultivation_state.essence.realm_id,
        )

    def enemy_rank(self, enemy: Any) -> int:
        return self.realm_rank(enemy.body_realm_id, enemy.essence_realm_id)

    # -- pressure --------------------------------------------------------
    def pressure(self, player: Any, enemy: Any) -> Dict[str, Any]:
        """Return the signed realm gap and each side's stat multiplier (1.0 = none)."""
        gap = self.player_rank(player) - self.enemy_rank(enemy)
        player_multiplier = 1.0
        enemy_multiplier = 1.0
        magnitude = abs(gap)
        if magnitude >= SUPPRESS_GAP:
            suppressed = max(
                SUPPRESS_FLOOR, 1.0 - SUPPRESS_STEP * (magnitude - SUPPRESS_GAP + 1)
            )
            if gap > 0:
                enemy_multiplier = suppressed
            else:
                player_multiplier = suppressed
        return {
            "gap": gap,
            "player_multiplier": round(player_multiplier, 2),
            "enemy_multiplier": round(enemy_multiplier, 2),
        }

    def enemy_yields(self, player: Any, enemy: Any) -> bool:
        """``True`` when the player outranks the enemy enough that it yields."""
        return self.player_rank(player) - self.enemy_rank(enemy) >= YIELD_GAP

    # -- dao matchup -----------------------------------------------------
    def matchup(self, attacker_dao_id: Any, defender_dao_id: Any) -> float:
        """Return the damage multiplier for ``attacker_dao_id`` vs ``defender_dao_id``."""
        attacker = self._daos.get(attacker_dao_id)
        defender = self._daos.get(defender_dao_id)
        if not attacker or not defender:
            return 1.0
        if defender_dao_id in attacker.get("counters", []):
            return COUNTER_MULTIPLIER
        if attacker_dao_id in defender.get("counters", []):
            return COUNTERED_MULTIPLIER
        return 1.0


def default_dao_id() -> str:
    """The Dao a brand-new cultivator begins with (see ``DEFAULT_DAO_ID``)."""
    return DEFAULT_DAO_ID
