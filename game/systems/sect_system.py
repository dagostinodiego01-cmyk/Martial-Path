"""Sect and path rules.

Sects are static data keyed by location. Joining one assigns the player's
martial ``path``, which later gates path-locked techniques taught by trainers.
This system lists a location's sects, validates join requirements (reputation
and body-realm progress), and performs the join by writing ``player.path``.

Pure logic: it performs no I/O and returns structured results. It needs the
body-realm ladder only to compare realm progression by ``order``.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from game.core.constants import EventType
from game.models.player import Player


class SectSystem:
    """Lists location sects and resolves joining them."""

    def __init__(self, sects: Iterable[Dict[str, Any]], body_realms: Dict[str, Any]) -> None:
        self._sects = {str(sect.get("id")): dict(sect) for sect in sects if sect.get("id")}
        self._realm_order = {
            str(realm.get("id")): int(realm.get("order", 0))
            for realm in body_realms.get("realms", [])
            if realm.get("id")
        }

    def sects_for_location(self, location_id: str) -> List[Dict[str, Any]]:
        """Return summaries for the sects available at a location."""
        return [self._sect_summary(sect) for sect in self._sects.values() if self._is_at_location(sect, location_id)]

    def sect_view(self, player: Player, sect_id: str = "") -> Dict[str, Any]:
        """Return one sect's details plus the player's join status."""
        sect = self._resolve_sect(player.current_location, sect_id)
        if sect is None:
            reason = "UNKNOWN_SECT" if sect_id else "NO_SECT_AVAILABLE"
            return {"event": EventType.ERROR, "reason": reason, "sect_id": sect_id, "location_id": player.current_location}
        if not self._is_at_location(sect, player.current_location):
            return {"event": EventType.ERROR, "reason": "SECT_NOT_AVAILABLE", "sect_id": sect_id, "location_id": player.current_location}
        summary = self._sect_summary(sect)
        summary["join_status"] = self._join_status(player, sect)
        return {"event": EventType.SECTS, "sect": summary}

    def can_join(self, player: Player, sect_id: str) -> Dict[str, Any]:
        """Return ``{allowed, reason}`` for joining ``sect_id`` right now."""
        sect = self._sects.get(sect_id)
        if sect is None:
            return {"allowed": False, "reason": "UNKNOWN_SECT", "sect_id": sect_id}
        if not self._is_at_location(sect, player.current_location):
            return {"allowed": False, "reason": "SECT_NOT_AVAILABLE", "sect_id": sect_id}
        if player.path == sect.get("path"):
            return {"allowed": False, "reason": "ALREADY_JOINED", "sect_id": sect_id}
        requirements = sect.get("join_requirements", {}) or {}
        min_realm = requirements.get("min_body_realm")
        if min_realm and self._realm_order.get(player.cultivation_state.body.realm_id, -1) < self._realm_order.get(min_realm, 0):
            return {"allowed": False, "reason": "REALM_TOO_LOW", "sect_id": sect_id, "required_realm": min_realm}
        min_rep = requirements.get("min_reputation")
        if min_rep is not None and player.reputation < int(min_rep):
            return {"allowed": False, "reason": "REPUTATION_TOO_LOW", "sect_id": sect_id, "required": int(min_rep)}
        max_rep = requirements.get("max_reputation")
        if max_rep is not None and player.reputation > int(max_rep):
            return {"allowed": False, "reason": "REPUTATION_TOO_HIGH", "sect_id": sect_id, "required": int(max_rep)}
        return {"allowed": True, "sect_id": sect_id}

    def join(self, player: Player, sect_id: str) -> Dict[str, Any]:
        """Join a sect: assign ``player.path`` and report the starting rank."""
        gate = self.can_join(player, sect_id)
        if not gate.get("allowed"):
            return {"event": EventType.ERROR, **gate}
        sect = self._sects[sect_id]
        previous = player.path
        player.path = str(sect.get("path", sect_id))
        ranks = sect.get("contribution_ranks", [])
        rank = ranks[0] if ranks else "disciple"
        return {
            "event": EventType.SECT_JOINED,
            "sect_id": sect_id,
            "name": str(sect.get("display_name", sect_id)),
            "path": player.path,
            "previous_path": previous,
            "rank": rank,
            "player_message": f"You join {sect.get('display_name', sect_id)} as an {rank.replace('_', ' ')}.",
        }

    # -- internal helpers -------------------------------------------------
    def _resolve_sect(self, location_id: str, sect_id: str) -> Optional[Dict[str, Any]]:
        if sect_id:
            return self._sects.get(sect_id)
        for sect in self._sects.values():
            if self._is_at_location(sect, location_id):
                return sect
        return None

    def _is_at_location(self, sect: Dict[str, Any], location_id: str) -> bool:
        return location_id in [str(entry) for entry in sect.get("location_ids", [])]

    def _join_status(self, player: Player, sect: Dict[str, Any]) -> Dict[str, Any]:
        gate = self.can_join(player, str(sect.get("id")))
        return {
            "allowed": gate.get("allowed"),
            "reason": gate.get("reason"),
            "already_joined": player.path == sect.get("path"),
            "path": sect.get("path"),
            "join_requirements": dict(sect.get("join_requirements", {})),
            "contribution_ranks": list(sect.get("contribution_ranks", [])),
        }

    def _sect_summary(self, sect: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "id": str(sect.get("id", "")),
            "display_name": str(sect.get("display_name", sect.get("id", ""))),
            "path": str(sect.get("path", sect.get("id", ""))),
            "location_ids": [str(location_id) for location_id in sect.get("location_ids", [])],
            "description": str(sect.get("description", "")),
        }
