"""World exploration, movement, enemy spawning, and their prose helpers."""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from game.core.constants import Action, EventType, MODE_COMBAT
from game.core.results import (
    CharacterEncounterResult,
    MapResult,
    MeditateResult,
    RestResult,
)
from game.models.enemy import Enemy


class ExplorationMixin:
    """Exploration and movement verbs plus the enemy/encounter view models."""

    # -- exploration helpers ---------------------------------------------
    def _explore(self) -> Dict[str, Any]:
        characters = self._location_character_options()
        if characters and self._rng.chance(self._character_encounter_chance):
            return CharacterEncounterResult(
                characters=characters,
                player_message="You encounter familiar cultivators nearby.",
            ).to_dict()

        event = self.event_system.generate(self.player, self._find_rarity_index())
        kind = event.get("event")

        if kind == EventType.COMBAT:
            enemy = self._spawn_enemy(event.get("enemy_id", ""))
            if self.dao.enemy_yields(self.player, enemy):
                # The player's realm pressure is overwhelming: the foe yields
                # before a single blow, so skip the trivial fight.
                self._current_enemy = enemy
                return self._end_combat(
                    {
                        "event": EventType.COMBAT_END,
                        "outcome": "VICTORY",
                        "yielded": True,
                        "enemy_name": enemy.name,
                        "loot_table": enemy.loot_table,
                        "turn_events": [{"actor": "ENEMY", "action": "YIELD", "enemy_name": enemy.name}],
                    }
                )
            self._current_enemy = enemy
            self._mode = MODE_COMBAT
            self._cooldowns = {}
            self._combat_is_spar = False
            self.player.statuses.clear()
            self.player.shield = 0
            self.combat.begin_combat(self.player)
            return {
                "event": EventType.COMBAT,
                "enemy": self._enemy_view(enemy),
                "text": event.get("text", "A hostile presence blocks your path!"),
                "narrative": self.narrative.render(
                    "explore_combat", {**self._narrative_context(), "enemy": enemy.name}
                ),
            }
        if kind == EventType.LOOT:
            result = self.inventory.add_item(self.player, event.get("item_id", ""), event.get("count", 1))
            if result.get("event") == EventType.LOOT:
                result["narrative"] = self.narrative.render(
                    "explore_loot", {**self._narrative_context(), "item": result.get("name", "something")}
                )
            return result
        if kind == EventType.SPECIAL:
            return self._apply_special(event)
        event["narrative"] = self.narrative.render("explore_nothing", self._narrative_context())
        return event  # EXPLORE_RESULT / NOTHING

    def _apply_special(self, event: Dict[str, Any]) -> Dict[str, Any]:
        effect = event.get("effect", {})
        applied = self.effects.apply_to_player(
            self.player,
            effect.get("type", "none"),
            int(effect.get("magnitude", 0)),
        )

        return {
            "event": EventType.SPECIAL,
            "special_id": event.get("special_id"),
            "text": event.get("text", ""),
            "narrative": self.narrative.render("explore_special", self._narrative_context()),
            **applied,
        }

    def _spawn_enemy(self, enemy_id: str) -> Enemy:
        template = self._enemy_templates.get(enemy_id)
        if template is None:
            template = next(iter(self._enemy_templates.values()))
        return Enemy.from_dict(template)

    def _spawn_character_enemy(self, enemy_id: str) -> Optional[Enemy]:
        template = self._character_enemy_templates.get(enemy_id)
        if template is None:
            return None
        return Enemy.from_dict(template)

    def _location_character_options(self) -> List[Dict[str, Any]]:
        characters = []
        for brief in self.character_service.get_available_characters(self.player.current_location, self.player):
            options = []
            character_id = brief["id"]
            if brief.get("unlocked") and brief.get("can_talk"):
                options.append({"action": Action.TALK_TO_CHARACTER, "character_id": character_id, "label": "Talk"})
            spar = self.character_service.can_spar(character_id, self.player)
            if spar.get("allowed") and spar.get("enemy_id"):
                options.append({"action": Action.SPAR_CHARACTER, "character_id": character_id, "label": "Spar"})
            duel = self.character_service.can_duel(character_id, self.player)
            if duel.get("allowed") and duel.get("enemy_id"):
                options.append({"action": Action.DUEL_CHARACTER, "character_id": character_id, "label": "Duel"})
            if self.character_service.can_receive_reward(character_id, self.player):
                options.append({"action": Action.RECEIVE_BOON, "character_id": character_id, "label": "Receive Reward"})
            if options:
                entry = dict(brief)
                entry["options"] = options
                characters.append(entry)
        return characters

    def _enemy_view(self, enemy: Enemy) -> Dict[str, Any]:
        """Return the enemy's public stats plus a UI-only threat/reward preview."""
        view = enemy.public_view()
        view["shield"] = enemy.shield
        view["statuses"] = {k: dict(v) for k, v in enemy.statuses.items()}
        body_name = self._body_realm_names.get(enemy.body_realm_id, enemy.body_realm_id)
        essence_name = self._essence_realm_names.get(enemy.essence_realm_id or "", "")
        view["body_realm"] = body_name
        view["essence_realm"] = essence_name
        view["realm"] = f"{body_name} / {essence_name}" if essence_name else body_name
        view["dao_id"] = enemy.dao_id
        view["dao_name"] = self.dao.dao_name(enemy.dao_id)
        view["pressure"] = self.dao.pressure(self.player, enemy)
        view.update(self._encounter_preview(enemy))
        return view

    def _encounter_preview(self, enemy: Enemy) -> Dict[str, Any]:
        """Derive a UI-only threat tier and reward preview for an enemy.

        This is presentation metadata for the frontend; it never affects combat
        math (which is owned by the combat system).
        """
        enemy_power = enemy.max_hp + enemy.attack * 5 + enemy.defense * 3
        player_power = (
            self.player.max_hp
            + self.stats.effective_stats(self.player).get("attack", self.player.attack) * 5
            + self.stats.effective_defense(self.player) * 3
        )
        ratio = enemy_power / player_power if player_power > 0 else 1.0
        if ratio < 0.6:
            threat = "Low"
        elif ratio < 1.0:
            threat = "Moderate"
        elif ratio < 1.5:
            threat = "High"
        else:
            threat = "Deadly"
        reward_items = [
            self._items[drop["item_id"]].name
            for drop in enemy.loot_table
            if drop.get("item_id") in self._items
        ]
        return {
            "threat": threat,
            "reward_preview": {"exp": enemy.exp_reward, "items": reward_items},
        }

    def _find_rarity_index(self) -> int:
        """Return the max find rarity index allowed by the current area's danger."""
        danger = self._location_danger.get(self.player.current_location, 0)
        return self.find_system.max_rarity_index_for_danger(danger)

    # -- narrative helpers ------------------------------------------------
    def _narrative_context(self) -> Dict[str, Any]:
        """Build the standard prose context (realm rank, morality, season, ...)."""
        return {
            "realm_rank": self.dao.player_rank(self.player),
            "morality": self.morality.band_id(self.player.morality),
            "reputation": self.player.reputation,
            "comprehension": self.player.comprehension,
            "season": self.lifespan.season(self.player),
        }

    def describe_npc(self, character_id: str) -> str:
        """State-aware prose for an NPC (varying by relationship + morality)."""
        character = self.character_service.get_character(character_id) or {}
        name = str(character.get("name", character_id))
        score = int(self.player.relationships.get(character_id, {}).get("relationship_score", 0))
        tier = self.relationships.tier_for(score)
        morality = self.morality.band_id(self.player.morality)
        return self.narrative.describe_npc(name, tier, morality)

    def describe_item(self, item_id: str) -> str:
        """State-aware prose for an item (varying by rarity)."""
        item = self._items.get(item_id)
        if item is None:
            return ""
        return self.narrative.describe_item(item.name, item.rarity or "common")

    def describe_technique(self, skill_id: str) -> str:
        """State-aware prose for a technique (flavoured by Dao affinity)."""
        skill = self._skills.get(skill_id)
        if skill is None:
            return ""
        return self.narrative.describe_technique(skill.name, self.dao.dao_name(self.player.dao_id))

    # -- exploration actions ---------------------------------------------
    def _rest(self) -> Dict[str, Any]:
        """Recover a portion of HP and Qi while safely at rest."""
        healed = self.player.heal(int(self.player.max_hp * 0.4))
        qi_restored = self.player.restore_qi(int(self.player.max_qi * 0.4))
        return RestResult(
            healed=healed,
            qi_restored=qi_restored,
            hp=self.player.hp,
            qi=self.player.qi,
        ).to_dict()

    def _meditate(self) -> Dict[str, Any]:
        """Meditate to restore Qi and, sometimes, sharpen comprehension."""
        qi_restored = self.player.restore_qi(int(self.player.max_qi * 0.3))
        comprehension_gain = 0
        if self._rng.chance(0.5):
            martial_talent = self.starting_fate.martial_talent_data(self.player.martial_talent_id)
            comprehension_gain = max(0, int(round(float(martial_talent.get("comprehension_multiplier", 1.0)))))
        self.player.comprehension += comprehension_gain
        return MeditateResult(
            qi_restored=qi_restored,
            qi=self.player.qi,
            comprehension_gain=comprehension_gain,
            comprehension=self.player.comprehension,
        ).to_dict()

    def _travel(self, location_id: str) -> Dict[str, Any]:
        """Move to a connected location if the route and requirements allow it."""
        result = self.travel.travel_to(self.player, location_id)
        if result.get("event") != EventType.TRAVEL_RESULT:
            return result
        updates = self.quests.notify("visit_location", self.player, self.inventory, target=location_id)
        if updates:
            result["quest_updates"] = updates
        result["narrative"] = self.narrative.render(
            "travel",
            {**self._narrative_context(), "destination": result.get("location", {}).get("name", location_id)},
        )
        return result

    def _map(self) -> Dict[str, Any]:
        """Return a text-map view: current location's map position and exits."""
        view = self.locations.view(self.player.current_location)
        return MapResult(
            location_name=view.get("name", self.player.current_location),
            map_position=view.get("map_position", {}),
            destinations=self.travel.get_available_destinations(self.player),
        ).to_dict()
