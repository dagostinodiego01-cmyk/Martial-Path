"""Combat-mode routing and end-of-combat resolution."""
from __future__ import annotations

from typing import Any, Dict

from game.core.constants import Action, EventType, MODE_COMBAT, MODE_EXPLORE


class CombatMixin:
    """The combat turn loop and its cleanup/penalty helpers."""

    # -- combat-mode dispatch --------------------------------------------
    def _process_combat_action(self, name: str, action: Dict[str, Any]) -> Dict[str, Any]:
        # Informational actions are resolved mode-agnostically in process_action
        # and never reach here; only turn-consuming actions remain.
        if self._current_enemy is None:
            self._mode = MODE_EXPLORE
            return {"event": EventType.ERROR, "reason": "NOT_IN_COMBAT"}
        if self.player.statuses.get("stun"):
            result = self.combat.player_stunned_turn(self.player, self._current_enemy, spar=self._combat_is_spar)
            self._tick_cooldowns()
            if result.get("event") == EventType.COMBAT_END:
                return self._end_combat(result)
            return result
        if name == Action.ATTACK:
            result = self.combat.attack(self.player, self._current_enemy, spar=self._combat_is_spar)
            self._tick_cooldowns()
            if result.get("event") == EventType.COMBAT_TURN and self._current_enemy is not None:
                result["narrative"] = self.narrative.render(
                    "attack", {**self._narrative_context(), "enemy": self._current_enemy.name}
                )
        elif name == Action.FLEE:
            result = self.combat.flee(self.player, self._current_enemy, spar=self._combat_is_spar)
            self._tick_cooldowns()
        elif name == Action.USE_SKILL:
            result = self._use_combat_skill(action.get("skill_id", ""))
            if result.get("event") == EventType.ERROR:
                return result
        elif name == Action.USE_ITEM:
            result = self._use_combat_item(action.get("item_id", ""))
            if result.get("event") == EventType.ERROR:
                return result
        else:
            return {"event": EventType.ERROR, "reason": "INVALID_IN_COMBAT", "input": name}

        if result.get("event") == EventType.COMBAT_END:
            return self._end_combat(result)
        return result

    # -- combat helpers ---------------------------------------------------
    def _use_combat_skill(self, skill_id: str) -> Dict[str, Any]:
        """Validate and resolve an active-skill activation in combat."""
        if not skill_id:
            return {"event": EventType.ERROR, "reason": "NO_SKILL_SPECIFIED"}
        if skill_id not in self.player.skills:
            return {"event": EventType.ERROR, "reason": "SKILL_NOT_KNOWN", "skill_id": skill_id}
        skill = self._skills.get(skill_id)
        if skill is None or not skill.is_active():
            return {"event": EventType.ERROR, "reason": "SKILL_NOT_USABLE", "skill_id": skill_id}
        if self._current_enemy is None:
            self._mode = MODE_EXPLORE
            return {"event": EventType.ERROR, "reason": "NOT_IN_COMBAT"}
        remaining = self._cooldowns.get(skill_id, 0)
        if remaining > 0:
            return {
                "event": EventType.ERROR,
                "reason": "SKILL_ON_COOLDOWN",
                "skill_id": skill_id,
                "remaining": remaining,
            }
        if skill.insight_required > 0 and self.player.insight < skill.insight_required:
            return {
                "event": EventType.ERROR,
                "reason": "NOT_ENOUGH_INSIGHT",
                "required": skill.insight_required,
                "insight": self.player.insight,
                "skill_id": skill_id,
            }
        qi_cost = self.stats.effective_qi_cost(skill, self.player)
        if self.player.qi < qi_cost:
            return {
                "event": EventType.ERROR,
                "reason": "NOT_ENOUGH_QI",
                "required": qi_cost,
                "qi": self.player.qi,
            }

        self.player.qi -= qi_cost
        result = self.combat.use_skill(self.player, self._current_enemy, skill, spar=self._combat_is_spar)
        # Tick existing cooldowns for the elapsed turn, then arm this skill so it
        # is unavailable for exactly ``skill.cooldown`` of the player's turns.
        self._tick_cooldowns()
        self._cooldowns[skill_id] = skill.cooldown
        return result

    def _use_combat_item(self, item_id: str) -> Dict[str, Any]:
        """Use an item during combat; this consumes the player's turn."""
        if self._current_enemy is None:
            self._mode = MODE_EXPLORE
            return {"event": EventType.ERROR, "reason": "NOT_IN_COMBAT"}
        item = self._items.get(item_id)
        if item is not None and item.effect == "learn_skill":
            return {"event": EventType.ERROR, "reason": "CANNOT_STUDY_IN_COMBAT", "item_id": item_id}
        item_result = self.inventory.use_item(self.player, item_id)
        if item_result.get("event") == EventType.ERROR:
            return item_result

        enemy_turn = self.combat.enemy_turn_only(self.player, self._current_enemy, spar=self._combat_is_spar)
        self._tick_cooldowns()

        item_event = {
            "actor": "PLAYER",
            "action": "USE_ITEM",
            "item": item_result.get("name"),
            "healed": item_result.get("healed"),
            "qi_restored": item_result.get("qi_restored"),
        }
        enemy_turn["turn_events"] = [item_event] + enemy_turn.get("turn_events", [])
        return enemy_turn

    def _end_combat(self, result: Dict[str, Any]) -> Dict[str, Any]:
        """Resolve the consequences of a finished fight and leave combat mode."""
        outcome = result.get("outcome")
        enemy_id = self._current_enemy.id if self._current_enemy else "any"
        self._mode = MODE_EXPLORE
        self._current_enemy = None
        self._cooldowns = {}
        self.player.statuses.clear()
        self.player.shield = 0
        self.player.insight = 0
        self._combat_is_spar = False

        if outcome == "VICTORY":
            result["loot"] = self.loot.roll_loot(self.player, result.get("loot_table", []))
            updates = self.quests.notify("defeat", self.player, self.inventory, target=enemy_id)
            if updates:
                result["quest_updates"] = updates
                for update in updates:
                    act = self.quests.act_end(update.get("id", ""))
                    if act:
                        result["act_complete"] = act
            if self._tournament_active:
                self._tournament_active = False
                result["tournament_won"] = True
                tournament_updates = self.quests.notify("tournament", self.player, self.inventory)
                if tournament_updates:
                    result["quest_updates"] = (result.get("quest_updates", []) + tournament_updates)
            if self._realm is not None:
                # A realm room is cleared: advance and surface the continue prompt.
                cleared = self._realm["realm"]["rooms"][self._realm["index"]]
                self._realm["index"] += 1
                result["realm"] = {
                    "display_name": self._realm["realm"]["display_name"],
                    "room_cleared": self._realm["index"],
                    "total": len(self._realm["realm"]["rooms"]),
                    "was_boss": cleared.get("kind") == "boss",
                }
        elif outcome == "DEFEAT":
            self._tournament_active = False
            if self._hardcore:
                return self._die("combat", result)
            self._realm = None
            self._apply_defeat_penalty(result)
        elif outcome in ("SPAR_WON", "SPAR_LOST"):
            self._apply_spar_end(result)
        elif outcome == "FLED":
            self._tournament_active = False
            self._realm = None
        return result

    def _apply_spar_end(self, result: Dict[str, Any]) -> None:
        """A friendly spar ends with no loot or progress loss; the loser is patched up."""
        if result.get("outcome") == "SPAR_LOST":
            self.player.hp = max(self.player.hp, self.player.max_hp // 2)
            self.player.qi = max(self.player.qi, self.player.max_qi // 2)
        result["spar"] = True

    def _apply_defeat_penalty(self, result: Dict[str, Any]) -> None:
        """Defeat is not game over: the player is rescued at a data-driven cost."""
        cfg = self._cultivation_config.get("defeat_penalty", {})
        loss_ratio = float(cfg.get("progress_loss_ratio", 1.0))
        hp_ratio = float(cfg.get("revive_hp_ratio", 0.5))
        qi_ratio = float(cfg.get("revive_qi_ratio", 0.5))

        body = self.player.cultivation_state.body
        lost = round(float(body.progress) * loss_ratio, 1)
        body.progress = max(0.0, float(body.progress) - lost)
        self.player.progress = body.progress
        self.player.hp = max(1, int(self.player.max_hp * hp_ratio))
        self.player.qi = int(self.player.max_qi * qi_ratio)
        degraded = self.equipment.degrade_equipped(self.player, 1)
        penalty = {"progress_lost": lost, "revived_hp": self.player.hp}
        if degraded:
            penalty["equipment_degraded"] = degraded
        result["penalty"] = penalty

    def _tick_cooldowns(self) -> None:
        for skill_id in list(self._cooldowns.keys()):
            self._cooldowns[skill_id] = max(0, self._cooldowns[skill_id] - 1)
