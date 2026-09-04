"""Sect and path rules.

Sects are static data keyed by location and ordered into story tiers (1-6).
Joining one assigns the player's martial ``path``, which later gates path-locked
techniques taught by trainers. This system lists a location's sects, validates
join requirements (reputation, body-realm progress, and the highest story tier
the player has reached), performs the join by writing ``player.path``, and sells
the techniques a sect hall teaches at its own tier.

Pure logic: it performs no I/O and returns structured results. It needs the
body-realm ladder only to compare realm progression by ``order``.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional

from game.core.constants import EventType
from game.models.player import Player
from game.systems import currency
from game.systems.skill_system import SkillSystem


class SectSystem:
    """Lists location sects, resolves joining them, and sells their techniques."""

    def __init__(
        self,
        sects: Iterable[Dict[str, Any]],
        body_realms: Dict[str, Any],
        dominant_sects: Optional[List[str]] = None,
        skills: Optional[Dict[str, Any]] = None,
        skill_system: Optional[SkillSystem] = None,
    ) -> None:
        self._sects = {str(sect.get("id")): dict(sect) for sect in sects if sect.get("id")}
        self._realm_order = {
            str(realm.get("id")): int(realm.get("order", 0))
            for realm in body_realms.get("realms", [])
            if realm.get("id")
        }
        # World seed (C.6): sects dominant in this run get first listing, a
        # ``dominant`` flag, and a -5 reputation subsidy on their join gate.
        self._dominant = [str(entry) for entry in (dominant_sects or [])]
        self._skills = skills or {}
        self._skill_system = skill_system

    # -- queries -----------------------------------------------------------
    def codex_summary(self, player: Player) -> Dict[str, Any]:
        """World codex of sects, tier technique halls, and faction arcs.

        Read-only view used by the CODEX action: every sect (even ones the
        player has not reached yet) with its tier, home locations, and a
        count of its hall techniques plus whether the player owns them;
        and the faction quest arcs (chains) with their quest titles and
        live status from the quest system.
        """
        entries: List[Dict[str, Any]] = []
        for sect in self._sects.values():
            techniques = sect.get("techniques", []) or []
            known = 0
            for entry in techniques:
                skill_id = str(entry.get("skill_id", ""))
                if skill_id and self._skill_system is not None and self._skill_system.knows(player, skill_id):
                    known += 1
            entries.append(
                {
                    "id": str(sect.get("id", "")),
                    "display_name": str(sect.get("display_name", sect.get("id", ""))),
                    "tier": self.sect_tier(sect),
                    "location_ids": [str(x) for x in sect.get("location_ids", [])],
                    "description": str(sect.get("description", "")),
                    "technique_count": len(techniques),
                    "techniques_known": known,
                    "joined": player.path == sect.get("path"),
                }
            )
        entries.sort(key=lambda entry: (entry["tier"], entry["id"]))
        return {
            "sects": entries,
            "max_story_tier": self.player_story_tier(player),
        }

    def sects_for_location(self, location_id: str) -> List[Dict[str, Any]]:
        """Return summaries for the sects available at a location.

        Dominant sects (world-seed variation) are listed first and carry
        ``dominant: true`` so the frontend can mark them.
        """
        entries = [self._sect_summary(sect) for sect in self._sects.values() if self._is_at_location(sect, location_id)]
        if self._dominant and len(entries) > 1:
            for entry in entries:
                entry["dominant"] = entry["id"] in self._dominant
            entries.sort(key=lambda entry: entry["id"] not in self._dominant)
        return entries

    def sect_view(self, player: Player, sect_id: str = "") -> Dict[str, Any]:
        """Return one sect's details, join status, and tier technique hall."""
        sect = self._resolve_sect(player.current_location, sect_id)
        if sect is None:
            reason = "UNKNOWN_SECT" if sect_id else "NO_SECT_AVAILABLE"
            return {"event": EventType.ERROR, "reason": reason, "sect_id": sect_id, "location_id": player.current_location}
        if not self._is_at_location(sect, player.current_location):
            return {"event": EventType.ERROR, "reason": "SECT_NOT_AVAILABLE", "sect_id": sect_id, "location_id": player.current_location}
        summary = self._sect_summary(sect)
        summary["join_status"] = self._join_status(player, sect)
        summary["techniques"] = [self._technique_view(player, sect, entry) for entry in sect.get("techniques", [])]
        summary["wallet"] = currency.wallet_view(player)
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
        min_story_tier = requirements.get("min_story_tier")
        if min_story_tier is not None and self.player_story_tier(player) < int(min_story_tier):
            return {
                "allowed": False,
                "reason": "STORY_TIER_TOO_LOW",
                "sect_id": sect_id,
                "required_story_tier": int(min_story_tier),
                "story_tier": self.player_story_tier(player),
            }
        min_realm = requirements.get("min_body_realm")
        if min_realm and self._realm_order.get(player.cultivation_state.body.realm_id, -1) < self._realm_order.get(min_realm, 0):
            return {"allowed": False, "reason": "REALM_TOO_LOW", "sect_id": sect_id, "required_realm": min_realm}
        min_rep = requirements.get("min_reputation")
        if min_rep is not None and sect_id in self._dominant:
            # Dominant sects recruit more eagerly in a run where they flourish.
            min_rep = max(0, int(min_rep) - 5)
        if min_rep is not None and player.reputation < int(min_rep):
            return {"allowed": False, "reason": "REPUTATION_TOO_LOW", "sect_id": sect_id, "required": int(min_rep)}
        max_rep = requirements.get("max_reputation")
        if max_rep is not None and player.reputation > int(max_rep):
            return {"allowed": False, "reason": "REPUTATION_TOO_HIGH", "sect_id": sect_id, "required": int(max_rep)}
        return {"allowed": True, "sect_id": sect_id}

    def player_story_tier(self, player: Player) -> int:
        """Return the highest story tier the player has visited (0 when unset)."""
        try:
            return max(0, int(getattr(player, "max_story_tier", 0)))
        except (TypeError, ValueError):
            return 0

    # -- mutations ---------------------------------------------------------
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
            "tier": self.sect_tier(sect),
            "previous_path": previous,
            "rank": rank,
            "player_message": f"You join {sect.get('display_name', sect_id)} as an {rank.replace('_', ' ')}.",
        }

    def learn(self, player: Player, skill_id: str, sect_id: str = "") -> Dict[str, Any]:
        """Buy a technique from a sect's hall, paying its currency cost.

        The sect must be present at the player's current location, the player
        must have joined its path, and the technique must be taught at a tier
        the sect's own ``tier`` reaches (see :meth:`_technique_gate`).
        """
        if not skill_id:
            return {"event": EventType.ERROR, "reason": "NO_SKILL_SPECIFIED", "sect_id": sect_id}
        sect = self._resolve_sect(player.current_location, sect_id)
        if sect is None:
            reason = "UNKNOWN_SECT" if sect_id else "NO_SECT_AVAILABLE"
            return {"event": EventType.ERROR, "reason": reason, "sect_id": sect_id, "location_id": player.current_location}
        if not self._is_at_location(sect, player.current_location):
            return {"event": EventType.ERROR, "reason": "SECT_NOT_AVAILABLE", "sect_id": sect_id, "location_id": player.current_location}
        if player.path != sect.get("path"):
            return {
                "event": EventType.ERROR,
                "reason": "SECT_NOT_JOINED",
                "sect_id": str(sect.get("id")),
                "required_path": sect.get("path"),
                "path": player.path,
            }

        entry = self._technique_entry(sect, skill_id)
        if entry is None:
            return {"event": EventType.ERROR, "reason": "TECHNIQUE_NOT_OFFERED", "sect_id": str(sect.get("id")), "skill_id": skill_id}
        if self._skills and skill_id not in self._skills:
            return {"event": EventType.ERROR, "reason": "UNKNOWN_SKILL", "skill_id": skill_id}
        if self._skill_system is not None and self._skill_system.knows(player, skill_id):
            return {"event": EventType.ERROR, "reason": "SKILL_ALREADY_KNOWN", "skill_id": skill_id}

        gate = self._technique_gate(player, sect, entry)
        if gate is not None:
            return {"event": EventType.ERROR, **gate}

        price = currency.normalise_price(entry.get("price"))
        missing = currency.shortage(player, price)
        if missing:
            return {
                "event": EventType.ERROR,
                "reason": "INSUFFICIENT_FUNDS",
                "skill_id": skill_id,
                "price": price,
                "missing": missing,
                "wallet": currency.wallet_view(player),
            }

        currency.spend(player, price)
        result = self._skill_system.learn_skill(
            player,
            skill_id,
            source="sect",
            price=price,
            wallet=currency.wallet_view(player),
        )
        if result.get("event") == EventType.SKILL_LEARNED:
            result["sect_id"] = str(sect.get("id"))
        return result

    def sect_tier(self, sect: Dict[str, Any]) -> int:
        """Return a sect's story tier (defaulting to 1 for untagged data)."""
        try:
            return max(1, int(sect.get("tier", 1)))
        except (TypeError, ValueError):
            return 1

    def joined_sect_view(self, player: Player) -> Dict[str, Any]:
        """Return a brief for the player's current sect, or ``{}`` when none.

        Includes the sect's technique hall so a UI can render learning from the
        player's own sect anywhere. Buying still requires standing at the sect
        (see :meth:`learn`); this view is informational.
        """
        for sect in self._sects.values():
            if player.path == sect.get("path"):
                return {
                    "sect_id": str(sect.get("id", "")),
                    "display_name": str(sect.get("display_name", sect.get("id", ""))),
                    "tier": self.sect_tier(sect),
                    "techniques": [self._technique_view(player, sect, entry) for entry in sect.get("techniques", [])],
                }
        return {}

    # -- internal helpers -------------------------------------------------
    def _technique_gate(self, player: Player, sect: Dict[str, Any], entry: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Return an error payload when a technique may not be bought now."""
        required_path = entry.get("required_path")
        if required_path and player.path != required_path:
            return {
                "reason": "PATH_LOCKED",
                "skill_id": entry.get("skill_id"),
                "required_path": required_path,
                "path": player.path,
            }
        min_tier = entry.get("min_tier")
        if min_tier is not None and self.sect_tier(sect) < int(min_tier):
            return {
                "reason": "SECT_TIER_TOO_LOW",
                "skill_id": entry.get("skill_id"),
                "sect_tier": self.sect_tier(sect),
                "required_tier": int(min_tier),
            }
        return None

    def _technique_view(self, player: Player, sect: Dict[str, Any], entry: Dict[str, Any]) -> Dict[str, Any]:
        skill_id = str(entry.get("skill_id", ""))
        skill = self._skills.get(skill_id)
        price = currency.normalise_price(entry.get("price"))
        gate = self._technique_gate(player, sect, entry)
        return {
            "skill_id": skill_id,
            "name": skill.name if skill else skill_id,
            "type": skill.type if skill else "unknown",
            "description": skill.description if skill else "",
            "price": price,
            "required_path": entry.get("required_path"),
            "path_locked": gate is not None and gate.get("reason") == "PATH_LOCKED",
            "already_known": bool(self._skill_system is not None and self._skill_system.knows(player, skill_id)),
            "affordable": not currency.shortage(player, price),
        }

    def _technique_entry(self, sect: Dict[str, Any], skill_id: str) -> Optional[Dict[str, Any]]:
        for entry in sect.get("techniques", []):
            if entry.get("skill_id") == skill_id:
                return entry
        return None

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
            "tier": self.sect_tier(sect),
            "description": str(sect.get("description", "")),
        }
