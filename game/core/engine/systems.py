"""The newer MVP systems: alchemy, Dao awakening, tournament, secret realm."""
from __future__ import annotations

from typing import Any, Dict, Optional

from game.core.constants import EventType, MODE_COMBAT, MODE_EXPLORE


class SystemsMixin:
    """Actions that wrap the alchemy, Dao, tournament, and secret-realm systems."""

    # -- alchemy (gather / refine) ----------------------------------------
    def _gather(self) -> Dict[str, Any]:
        """Harvest a herb at the current location (gated by its herb table)."""
        location_id = self.player.current_location
        if not self.gathering.has_gathering(location_id):
            return {"event": EventType.ERROR, "reason": "NO_HERBS_HERE", "location_id": location_id}
        herb_id = self.gathering.roll(location_id, self._rng)
        if not herb_id:
            return {"event": EventType.ERROR, "reason": "NO_HERBS_HERE", "location_id": location_id}
        result = self.inventory.add_item(self.player, herb_id, 1)
        result["event"] = EventType.GATHER_RESULT
        result["location_id"] = location_id
        result["narrative"] = self.narrative.render(
            "explore_loot", {**self._narrative_context(), "item": result.get("name", "herbs")}
        )
        return result

    def _refine(self, recipe_id: str) -> Dict[str, Any]:
        """Refine herbs into a pill/elixir via the recipe graph."""
        return self.refine.refine(self.player, recipe_id, self.inventory)

    # -- dao view / awakening ---------------------------------------------
    def _dao_view(self) -> Dict[str, Any]:
        """Return the full Dao catalogue plus the player's current Dao."""
        return {
            "event": EventType.DAO_VIEW,
            "current_dao_id": self.player.dao_id,
            "current_dao_name": self.dao.dao_name(self.player.dao_id),
            "daos": self.dao.dao_view(),
        }

    def _dao_awaken(self, dao_id: str) -> Dict[str, Any]:
        """Awaken a new Dao, swapping the player's Dao and notifying quests.

        Gated behind the Act-1 ``dao_awakening`` beat: it opens once a quest with
        a ``dao_awakening`` objective is active and is a one-time choice per run.
        """
        if not dao_id:
            return {"event": EventType.ERROR, "reason": "NO_DAO_SPECIFIED"}
        if self.quests.objective_completed("dao_awakening"):
            return {"event": EventType.ERROR, "reason": "DAO_ALREADY_AWAKENED", "dao_id": dao_id}
        if not self.quests.objective_active("dao_awakening"):
            return {"event": EventType.ERROR, "reason": "DAO_AWAKENING_LOCKED"}
        if not self.dao.has_dao(dao_id):
            return {"event": EventType.ERROR, "reason": "UNKNOWN_DAO", "dao_id": dao_id}
        if dao_id == self.player.dao_id:
            return {"event": EventType.ERROR, "reason": "DAO_ALREADY_AWAKENED", "dao_id": dao_id}
        previous = self.player.dao_id
        self.player.dao_id = str(dao_id)
        result = {
            "event": EventType.DAO_AWAKENED,
            "dao_id": str(dao_id),
            "dao_name": self.dao.dao_name(dao_id),
            "previous_dao_id": previous,
            "previous_dao_name": self.dao.dao_name(previous),
            "player_message": f"You awaken to the {self.dao.dao_name(dao_id)} and your path bends to it.",
        }
        updates = self.quests.notify("dao_awakening", self.player, self.inventory, target=str(dao_id))
        if updates:
            result["quest_updates"] = updates
        result["player"] = self._player_view()
        return result

    # -- tournament -------------------------------------------------------
    def _tournament(self) -> Dict[str, Any]:
        """Enter the local tournament bracket: a duel against the seeded champion."""
        if self._current_enemy is not None or self._mode == MODE_COMBAT:
            return {"event": EventType.ERROR, "reason": "ALREADY_IN_COMBAT"}
        if not self._has_tournament():
            return {"event": EventType.ERROR, "reason": "NO_TOURNAMENT_HERE", "location_id": self.player.current_location}
        champion_id = self._tournament_champion_id()
        enemy = self._spawn_character_enemy(champion_id)
        if enemy is None:
            return {"event": EventType.ERROR, "reason": "NO_TOURNAMENT_HERE", "location_id": self.player.current_location}
        self._current_enemy = enemy
        self._mode = MODE_COMBAT
        self._cooldowns = {}
        self._combat_is_spar = False
        self.player.statuses.clear()
        self.player.shield = 0
        self.combat.begin_combat(self.player)
        self._tournament_active = True
        return {
            "event": EventType.COMBAT,
            "tournament": True,
            "enemy": self._enemy_view(enemy),
            "text": f"The tournament crier calls your name: you face {enemy.name} in the arena.",
        }

    def _tournament_champion_id(self) -> str:
        """The seeded named foe that champions the tournament at this location."""
        return "divine_phoenix_disciple_spar"

    def _has_tournament(self) -> bool:
        """Tournaments are held where sects gather (academies, sect halls, arenas)."""
        location = self.locations.get(self.player.current_location) or {}
        systems = set(location.get("available_systems", []))
        return bool(systems & {"sects", "sparring", "tournament"})

    # -- secret realm -----------------------------------------------------
    def _enter_realm(self) -> Dict[str, Any]:
        """Open the secret realm at the current location (if one opens here)."""
        location_id = self.player.current_location
        if not self.secret_realm.realm_available_at(location_id):
            return {"event": EventType.ERROR, "reason": "NO_REALM_HERE", "location_id": location_id}
        if self._realm is not None:
            return {"event": EventType.ERROR, "reason": "ALREADY_IN_REALM"}
        realm = self.secret_realm.generate(location_id)
        self._realm = {"realm": realm, "index": 0}
        return {
            "event": EventType.REALM_ENTERED,
            "realm": self.secret_realm.description(location_id),
            "rooms_total": len(realm["rooms"]),
            "player_message": f"You step into {realm['display_name']}.",
        }

    def _realm_advance(self) -> Dict[str, Any]:
        """Step into the next room of the active realm, resolving its kind."""
        if self._realm is None:
            return {"event": EventType.ERROR, "reason": "NOT_IN_REALM"}
        realm = self._realm["realm"]
        rooms = realm["rooms"]
        index = self._realm["index"]
        if index >= len(rooms):
            return self._complete_realm()
        room = rooms[index]
        kind = room.get("kind")
        if kind in ("encounter", "boss"):
            enemy_id = room.get("enemy_id", "")
            enemy = self._spawn_character_enemy(enemy_id) if room.get("named") else self._spawn_enemy(enemy_id)
            self._current_enemy = enemy
            self._mode = MODE_COMBAT
            self._cooldowns = {}
            self._combat_is_spar = False
            self.player.statuses.clear()
            self.player.shield = 0
            self.combat.begin_combat(self.player)
            return {
                "event": EventType.COMBAT,
                "realm": {"display_name": realm["display_name"], "room": index + 1, "total": len(rooms)},
                "is_boss": kind == "boss",
                "enemy": self._enemy_view(enemy),
                "text": f"A {enemy.name} bars your way deeper into {realm['display_name']}.",
            }
        if kind == "treasure":
            self._realm["index"] = index + 1
            result = self.inventory.add_item(self.player, room.get("item_id", ""), int(room.get("count", 1)))
            return {
                "event": EventType.REALM_ROOM,
                "kind": "treasure",
                "item_id": result.get("item_id"),
                "name": result.get("name"),
                "room": index + 1,
                "total": len(rooms),
                "player_message": f"You find {result.get('name', 'a treasure')} in the realm.",
            }
        if kind == "rest":
            self._realm["index"] = index + 1
            healed = self.player.heal(int(self.player.max_hp * 0.5))
            qi_restored = self.player.restore_qi(int(self.player.max_qi * 0.5))
            return {
                "event": EventType.REALM_ROOM,
                "kind": "rest",
                "healed": healed,
                "qi_restored": qi_restored,
                "room": index + 1,
                "total": len(rooms),
                "player_message": "You find a sheltered alcove and recover your strength.",
            }
        self._realm["index"] = index + 1
        return self._realm_advance()

    def _realm_leave(self) -> Dict[str, Any]:
        """Abandon the realm, returning to the overworld."""
        if self._realm is None:
            return {"event": EventType.ERROR, "reason": "NOT_IN_REALM"}
        self._realm = None
        self._current_enemy = None
        self._mode = MODE_EXPLORE
        self._cooldowns = {}
        return {"event": EventType.REALM_ROOM, "kind": "leave", "player_message": "You retreat from the secret realm."}

    def _complete_realm(self) -> Dict[str, Any]:
        """Grant the realm's final reward and return to the overworld."""
        realm = self._realm["realm"] if self._realm else {}
        reward = realm.get("final_reward", {})
        granted: Dict[str, Any] = {}
        if "exp" in reward:
            amount = int(reward["exp"])
            self.player.exp += amount
            granted["exp"] = amount
        if "gold" in reward:
            amount = int(reward["gold"])
            self.player.gold += amount
            granted["gold"] = amount
        for item_id, count in reward.get("items", {}).items():
            self.inventory.add_item(self.player, item_id, int(count))
            granted.setdefault("items", {})[item_id] = int(count)
        self._realm = None
        self._mode = MODE_EXPLORE
        return {
            "event": EventType.REALM_COMPLETED,
            "realm": realm.get("display_name", "secret realm"),
            "reward": granted,
            "player_message": f"You conquer {realm.get('display_name', 'the realm')} and claim its reward.",
        }

    def _realm_view(self) -> Optional[Dict[str, Any]]:
        """UI snapshot of the active realm (``None`` when not inside one)."""
        if self._realm is None:
            return None
        realm = self._realm["realm"]
        return {
            "id": realm.get("id"),
            "display_name": realm.get("display_name"),
            "room": self._realm["index"] + 1,
            "total": len(realm["rooms"]),
        }
