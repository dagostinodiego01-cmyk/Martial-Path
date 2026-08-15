"""UI-safe state snapshots and view models."""
from __future__ import annotations

from typing import Any, Dict, List

from game.core.constants import EventType, MODE_COMBAT


class ViewsMixin:
    """Read-only views the frontends render (no gameplay rules here)."""

    def get_game_state(self) -> Dict[str, Any]:
        """Return a UI-safe snapshot of the entire game state."""
        player_data = self._player_view()
        location_view = self.locations.view(self.player.current_location)
        location_view["narrative"] = self.narrative.describe_location(
            location_view, self.lifespan.season(self.player)
        )
        inventory_items = self.inventory.list_inventory(self.player)["items"]
        for entry in inventory_items:
            entry["narrative"] = self.describe_item(entry.get("item_id", ""))
        return {
            "player": player_data,
            "mode": self._mode,
            "in_combat": self._mode == MODE_COMBAT,
            "enemy": self._enemy_view(self._current_enemy) if self._current_enemy else None,
            "cooldowns": dict(self._cooldowns),
            "inventory_items": inventory_items,
            "shops": self.shops.shops_for_location(self.player.current_location),
            "trainers": self.trainers.trainers_for_location(self.player.current_location),
            "sects": self.sects.sects_for_location(self.player.current_location),
            "gathering_available": self.gathering.has_gathering(self.player.current_location),
            "refining_recipes": self.refine.recipes(self.player),
            "realm_available": self.secret_realm.realm_available_at(self.player.current_location),
            "realm": self._realm_view(),
            "tournament_available": self._has_tournament(),
            "location": location_view,
            "destinations": self.travel.get_available_destinations(self.player),
            "location_characters": self.character_service.get_available_characters(
                self.player.current_location, self.player
            ),
            "quests": self.quests.snapshot(),
            "awaiting_fate_acceptance": not self._fate_accepted,
            "pending_fate": self._pending_fate_view(),
            "running": self._running,
        }

    def is_running(self) -> bool:
        """Return ``True`` until the player quits."""
        return self._running

    def get_meta_state(self) -> Dict[str, Any]:
        """Return the cross-run meta view: Ancestral Memory, chronicle, and origins.

        The main menu reads this to render the graveyard and the origin picker.
        Each origin is annotated with ``affordable`` (memory balance vs cost) so
        the UI can disable locked backgrounds without its own game rules.
        """
        balance = self.meta.memory()
        origins = []
        for origin in self.origins.all():
            entry = dict(origin)
            entry["affordable"] = int(entry.get("cost", 0)) <= balance
            origins.append(entry)
        return {
            "ancestral_memory": balance,
            "chronicle": self.meta.chronicle(),
            "origins": origins,
        }

    def set_player_name(self, name: str) -> None:
        """Set the player's display name (used by character creation in the UI)."""
        if name:
            self.player.name = name

    def get_known_skills(self) -> List[Dict[str, Any]]:
        """Return UI-safe briefs for the player's skills, incl. live combat state.

        Read-only view model used by graphical frontends (e.g. a Pokemon-style
        move menu) to render skill buttons with qi cost, base cooldown, current
        cooldown remaining, and affordability. Adds no gameplay logic.
        """
        briefs: List[Dict[str, Any]] = []
        for skill_id in self.player.skills:
            brief = self._skill_brief(skill_id)
            brief["cooldown_remaining"] = self._cooldowns.get(skill_id, 0)
            brief["affordable"] = self.player.qi >= int(brief.get("qi_cost", 0))
            brief["insight_met"] = self.player.insight >= int(brief.get("insight_required", 0))
            briefs.append(brief)
        return briefs

    def get_inventory_items(self) -> List[Dict[str, Any]]:
        """Return the player's inventory as UI-safe entries (read-only view)."""
        return self.inventory.list_inventory(self.player)["items"]

    # -- status -----------------------------------------------------------
    def _status(self) -> Dict[str, Any]:
        data = self._player_view()
        data["skills"] = [self._skill_brief(skill_id) for skill_id in self.player.skills]
        data["cooldowns"] = dict(self._cooldowns)
        return {"event": EventType.STATUS, "player": data}

    def _player_view(self) -> Dict[str, Any]:
        data = self.player.to_dict()
        # Show effective defense (base + always-on passives) rather than the
        # pristine base value stored on the player.
        data["defense"] = self.stats.effective_defense(self.player)
        cultivation_state = self.cultivation_service.get_cultivation_state("player")
        data["cultivation_state"] = cultivation_state
        data["cultivation"] = cultivation_state["summary"]
        data["progress"] = cultivation_state["body_transformation"]["progress"]
        data["realm"] = cultivation_state["body_transformation"]["display_name"]
        data["essence_progress"] = cultivation_state["essence_gathering"]["progress"]
        data["essence_cultivation"] = cultivation_state["essence_gathering"]["display_name"]
        data["essence_unlocked"] = cultivation_state.get("essence_unlocked", True)
        data["martial_talent"] = self.starting_fate.martial_talent_view(self.player.martial_talent_id)
        data["body_talent"] = self.starting_fate.body_talent_view(self.player.body_talent_id)
        data["lifespan"] = self.lifespan.lifespan_view(self.player, cultivation_state.get("essence_unlocked", True))
        data["equipment_details"] = self.equipment.equipment_details(self.player)
        data["equipment_modifiers"] = self.equipment.aggregate_modifiers(self.player)
        data["effective_stats"] = self.stats.effective_stats(self.player)
        data["shield"] = self.player.shield
        data["statuses"] = {k: dict(v) for k, v in self.player.statuses.items()}
        data["insight"] = self.player.insight
        return data

    def _skill_brief(self, skill_id: str) -> Dict[str, Any]:
        skill = self._skills.get(skill_id)
        if skill is None:
            return {"id": skill_id, "name": skill_id, "type": "unknown"}
        return {
            "id": skill_id,
            "name": skill.name,
            "type": skill.type,
            "qi_cost": skill.qi_cost,
            "cooldown": skill.cooldown,
            "insight_required": skill.insight_required,
            "description": skill.description,
            "narrative": self.narrative.describe_technique(
                skill.name, self.dao.dao_name(self.player.dao_id)
            ),
        }
