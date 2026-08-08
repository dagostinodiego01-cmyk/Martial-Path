"""Travel service.

Coordinates the world map (``LocationSystem``) with player-specific gating so the
engine and any UI have a single authority for "where can I go, and why not?".

Responsibilities:

* resolve the current location view,
* list neighbouring destinations tagged as reachable or locked (with a reason),
* validate a specific move against adjacency and entry requirements,
* apply a validated move to the player.

Requirement gating (cultivation realm minimums, required items/reputation) is
data-driven from each location's ``requirements`` block. The service reads and
moves the player it is handed, but it owns no session state itself -- the engine
still owns the player and any cross-system side effects (quests, encounters).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from game.core.results import ErrorResult, TravelResult
from game.systems.location_system import LocationSystem, danger_label

# Realm minimum values that mean "no cultivation gate".
_OPEN_REALMS = {"", "none", "any"}


class TravelService:
    """Validates and performs travel between connected locations."""

    def __init__(
        self,
        locations: LocationSystem,
        body_realms: Optional[Dict[str, Any]] = None,
        essence_realms: Optional[Dict[str, Any]] = None,
    ) -> None:
        self._locations = locations
        self._body_order = self._build_order(body_realms)
        self._essence_order = self._build_order(essence_realms)

    # -- queries ----------------------------------------------------------
    def get_current_location(self, player: Any) -> Dict[str, Any]:
        """Return the UI-safe view of the player's current location."""
        return self._locations.view(player.current_location)

    def get_available_destinations(self, player: Any) -> List[Dict[str, Any]]:
        """List neighbours of the current location, flagged reachable or locked."""
        destinations: List[Dict[str, Any]] = []
        for location_id in self._locations.neighbors(player.current_location):
            allowed, reason = self._evaluate(player, location_id)
            loc = self._locations.get(location_id) or {}
            destinations.append(
                {
                    "id": location_id,
                    "display_name": self._locations.display_name(location_id),
                    "danger": danger_label(loc.get("danger_level", loc.get("danger"))),
                    "reachable": allowed,
                    "reason": reason,
                }
            )
        return destinations

    def can_travel_to(self, player: Any, location_id: str) -> Dict[str, Any]:
        """Return ``{"allowed": bool, "reason": str|None}`` for a candidate move."""
        allowed, reason = self._evaluate(player, location_id)
        return {"allowed": allowed, "reason": reason}

    # -- mutation ---------------------------------------------------------
    def travel_to(self, player: Any, location_id: str) -> Dict[str, Any]:
        """Validate and, if allowed, move the player, returning a structured result."""
        allowed, reason = self._evaluate(player, location_id)
        if not allowed:
            return ErrorResult(reason=reason, location_id=location_id).to_dict()
        player.current_location = location_id
        return TravelResult(location=self._locations.view(location_id)).to_dict()

    # -- internal ---------------------------------------------------------
    def _evaluate(self, player: Any, location_id: str) -> Tuple[bool, Optional[str]]:
        if not location_id:
            return False, "NO_DESTINATION"
        if not self._locations.exists(location_id):
            return False, "UNKNOWN_LOCATION"
        if location_id == player.current_location:
            return False, "ALREADY_THERE"
        if not self._locations.can_travel(player.current_location, location_id):
            return False, "NO_ROUTE"
        return self._requirements_met(player, location_id)

    def _requirements_met(self, player: Any, location_id: str) -> Tuple[bool, Optional[str]]:
        req = self._locations.requirements(location_id)
        if not req:
            return True, None

        body = req.get("body_transformation", {})
        if not self._realm_ok(self._body_order, self._body_realm_id(player), body.get("minimum_realm")):
            return False, "BODY_REALM_TOO_LOW"

        essence = req.get("essence_gathering", {})
        if not self._realm_ok(self._essence_order, self._essence_realm_id(player), essence.get("minimum_realm")):
            return False, "ESSENCE_REALM_TOO_LOW"

        for item_id in req.get("required_items", []):
            if int(player.inventory.get(item_id, 0)) <= 0:
                return False, "MISSING_REQUIRED_ITEM"

        for entry in req.get("required_reputation", []):
            needed = entry.get("min") if isinstance(entry, dict) else entry
            if isinstance(needed, (int, float)) and player.reputation < needed:
                return False, "REPUTATION_TOO_LOW"

        return True, None

    @staticmethod
    def _realm_ok(order_map: Dict[str, int], player_realm_id: Optional[str], minimum: Any) -> bool:
        """Return ``True`` when the player's realm meets ``minimum`` (fail-open on unknowns)."""
        if minimum is None or str(minimum).strip().lower() in _OPEN_REALMS:
            return True
        min_order = order_map.get(str(minimum).strip().lower())
        if min_order is None:
            return True  # unknown minimum: do not block travel on bad/legacy data
        player_order = order_map.get(str(player_realm_id).strip().lower(), 0)
        return player_order >= min_order

    @staticmethod
    def _body_realm_id(player: Any) -> Optional[str]:
        state = getattr(player, "cultivation_state", None)
        return getattr(getattr(state, "body", None), "realm_id", None)

    @staticmethod
    def _essence_realm_id(player: Any) -> Optional[str]:
        state = getattr(player, "cultivation_state", None)
        return getattr(getattr(state, "essence", None), "realm_id", None)

    @staticmethod
    def _build_order(realms_data: Optional[Dict[str, Any]]) -> Dict[str, int]:
        """Map realm ids and display names (lowercased) to their order value."""
        mapping: Dict[str, int] = {}
        for realm in (realms_data or {}).get("realms", []):
            order = int(realm.get("order", 0))
            for key in (realm.get("id"), realm.get("display_name")):
                if key:
                    mapping[str(key).strip().lower()] = order
        return mapping
