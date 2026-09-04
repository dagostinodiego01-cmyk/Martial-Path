"""UI-safe state snapshots and view models."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from game.core.constants import EventType, MODE_COMBAT

from game.systems.combat_system import COMBO_ROLES


# Human-readable labels for each skill effect, used by the Techniques tab so the
# frontend can render what a technique actually does without its own mapping.
EFFECT_LABELS: Dict[str, str] = {
    "damage": "Damage",
    "true_damage": "True Damage",
    "aoe_damage": "Area Damage",
    "dot_damage": "Damage over Time",
    "execute": "Execute",
    "heal_self": "Self Heal",
    "stun": "Stun",
    "debuff_attack": "Weaken Attack",
    "debuff_defense": "Weaken Defense",
    "life_steal": "Life Steal",
    "shield": "Shield",
    "counter": "Counter",
    "buff_attack": "Attack",
    "buff_defense": "Defense",
    "buff_max_hp": "Max HP",
    "buff_max_qi": "Max Qi",
    "buff_speed": "Speed",
    "buff_evasion": "Evasion",
    "crit_chance": "Crit Chance",
    "crit_damage": "Crit Damage",
    "hp_regen": "HP Regen",
    "qi_regen": "Qi Regen",
    "qi_cost_reduction": "Qi Cost Reduction",
    "comprehension_gain": "Comprehension",
    "lifespan": "Lifespan",
    "cultivation_speed": "Cultivation Speed",
}

# Passive effects that always-on modify combat stats (see ``StatsSystem``).
_STAT_PASSIVE_EFFECTS = frozenset({
    "buff_attack", "buff_defense", "buff_max_hp", "buff_max_qi",
    "buff_speed", "buff_evasion", "crit_chance", "crit_damage",
    "hp_regen", "qi_regen", "qi_cost_reduction",
})

# Passive effects resolved once at learn time (``SkillSystem`` / cultivation).
_GROWTH_PASSIVE_EFFECTS = frozenset({
    "comprehension_gain", "lifespan", "cultivation_speed",
})


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
            "world": self._world_view(),
            "debate": self._active_debate_view(),
            "campaign": self._campaign_view(),
            "running": self._running,
        }

    def _codex(self) -> Dict[str, Any]:
        """The wanderer's codex: secret realms, sects, and faction arcs.

        Pure read-only composition for the CODEX action. Realms and sects the
        player has not reached yet still appear (the codex is a lore surface,
        not a spoiler-free guide) but carry their story tier so the UI can
        mark undiscovered entries.
        """
        sects_payload = self.sects.codex_summary(self.player)
        max_story_tier = int(sects_payload.get("max_story_tier", 0))

        # -- faction arcs: quest chains grouped by their ``chain`` tag ----
        arcs: Dict[str, Dict[str, Any]] = {}
        for quest in self.quests.snapshot():
            chain = str(quest.get("chain", "") or "")
            if not chain:
                continue
            entry = arcs.setdefault(
                chain, {"chain": chain, "title": chain.replace("_", " ").title(), "quests": []}
            )
            entry["quests"].append(
                {
                    "id": quest.get("id", ""),
                    "title": quest.get("title", ""),
                    "status": quest.get("status", ""),
                }
            )
        arc_list = [arcs[key] for key in sorted(arcs)]

        # -- secret realms with reach/discovery flags ---------------------
        realms: List[Dict[str, Any]] = []
        for definition in self.secret_realm.definitions():
            location_id = str(definition.get("location_id", ""))
            story_tier = self.locations.story_tier(location_id)
            realms.append(
                {
                    "id": str(definition.get("id", "")),
                    "display_name": str(definition.get("display_name", definition.get("id", ""))),
                    "location_id": location_id,
                    "location_name": self.locations.display_name(location_id),
                    "description": str(definition.get("description", "")),
                    "story_tier": story_tier,
                    "discovered": story_tier <= max_story_tier,
                }
            )
        realms.sort(key=lambda realm: (realm["story_tier"], realm["id"]))

        return {
            "event": EventType.CODEX,
            "max_story_tier": max_story_tier,
            "realms": realms,
            "sects": sects_payload.get("sects", []),
            "arcs": arc_list,
        }

    def _world_view(self) -> Dict[str, Any]:
        """Compact living-world summary for the main state payload (E.1-E.5)."""
        state = getattr(self, "_world_state", None) or {}
        npcs = state.get("npcs", {})
        living = sum(1 for npc in npcs.values() if npc.get("alive", True))
        power = state.get("sect_power", {})
        top = max(power, key=lambda sect_id: float(power[sect_id])) if power else ""
        market = state.get("market", {})
        try:
            price_multiplier = float(market.get("price_multiplier", 1.0))
        except (TypeError, ValueError):
            price_multiplier = 1.0
        return {
            "year": state.get("year", 0.0),
            "season": self.lifespan.season(self.player),
            "season_modifiers": self._season_modifiers(),
            "cultivators_alive": living,
            "cultivators_total": len(npcs),
            "dominant_sect_id": top,
            "dominant_sect_name": self.world.sect_name(top) if top else "",
            "price_multiplier": price_multiplier,
            "rumor_count": len(self.world.rumors(state)),
        }

    def is_running(self) -> bool:
        """Return ``True`` until the player quits."""
        return self._running

    def get_meta_state(self) -> Dict[str, Any]:
        """Return the cross-run meta view: Ancestral Memory, chronicle, and origins.

        The main menu reads this to render the graveyard, the origin picker, and
        the legacy unlock tree. Each origin is annotated with ``affordable``
        (memory balance vs cost) and each unlock node with ``purchased``/
        ``available`` so the UI can disable locked entries without its own game
        rules.
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
            "unlocks": self.meta.unlocks(),
            "unlock_tree": self.legacy.tier_state(self.meta.unlocks()),
            "retired": self.meta.state().get("retired", False),
        }

    def _meta_unlock_tree(self) -> Dict[str, Any]:
        """Return the legacy unlock tree with live purchase state (C.5).

        Reachable mid-run through the ``UNLOCK_TREE`` action; the main menu's
        ``get_meta_state`` carries the same tree for out-of-run purchases.
        """
        balance = self.meta.memory()
        return {
            "event": EventType.UNLOCK_TREE,
            "ancestral_memory": balance,
            "tiers": self.legacy.tier_state(self.meta.unlocks()),
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
            expected_role = self.combat.next_combo_role(self.player)
            brief["expected_combo_role"] = expected_role
            brief["combo_ready"] = (
                expected_role is not None and str(brief.get("combo_role", "")) == expected_role
            )
            briefs.append(brief)
        return briefs

    def get_inventory_items(self) -> List[Dict[str, Any]]:
        """Return the player's inventory as UI-safe entries (read-only view)."""
        return self.inventory.list_inventory(self.player)["items"]

    # -- status -----------------------------------------------------------
    def _status(self) -> Dict[str, Any]:
        data = self._player_view()
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
        # B.7: the player's conviction for dao debates (insight is the pressure
        # behind each argument, mirroring how combat techniques draw on it).
        data["debate_conviction"] = max(1, int(getattr(self.player, "insight", 0)))
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
        data["combo_stage"] = self.player.combo_stage
        data["title"] = self._legacy_title_view()
        data["can_retire"] = self._can_retire()
        # Sect membership brief (tier + technique hall) for UIs that surface
        # learning from the player's own sect.
        data["joined_sect"] = self.sects.joined_sect_view(self.player)
        # Rich skill briefs (type/effect/cost/cooldown/affordability) so the
        # frontend can render the Techniques tab and the combat move menu from
        # the same authoritative view model.
        data["skills"] = self.get_known_skills()
        return data

    def _skill_category(self, skill: Any) -> str:
        """Classify a technique for the Techniques tab.

        Returns one of ``Active`` (invoked in combat), ``Stats`` (always-on
        combat stat passive), ``Growth`` (permanent learn-time passive), or
        ``Passive`` (uncategorised fallback).
        """
        if skill.is_active():
            return "Active"
        if skill.effect in _STAT_PASSIVE_EFFECTS:
            return "Stats"
        if skill.effect in _GROWTH_PASSIVE_EFFECTS:
            return "Growth"
        return "Passive"

    def _legacy_title_view(self) -> Optional[str]:
        """The cosmetic title granted by a purchased legacy unlock (C.5)."""
        for unlock_id in self.meta.unlocks():
            node = self.legacy.node(unlock_id)
            if node is not None and node.get("kind") == "title":
                return str(node.get("target_id", ""))
        return None

    def _skill_brief(self, skill_id: str) -> Dict[str, Any]:
        skill = self._skills.get(skill_id)
        if skill is None:
            return {"id": skill_id, "name": skill_id, "type": "unknown", "category": "unknown"}
        return {
            "id": skill_id,
            "name": skill.name,
            "type": skill.type,
            "category": self._skill_category(skill),
            "effect": skill.effect,
            "effect_label": EFFECT_LABELS.get(skill.effect, skill.effect.replace("_", " ").title()),
            "scaling": skill.scaling,
            "qi_cost": skill.qi_cost,
            "cooldown": skill.cooldown,
            "insight_required": skill.insight_required,
            "combo_role": skill.combo_role,
            "description": skill.description,
            "narrative": self.narrative.describe_technique(
                skill.name, self.dao.dao_name(self.player.dao_id)
            ),
        }
