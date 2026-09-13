"""Choice-driven encounter flow: pending state, dispatch, and application.

``_explore`` no longer resolves a roll outright. It hands the roll to
:class:`~game.systems.encounter_system.EncounterSystem`, which describes a
*scene* and the choices it permits; the engine parks that scene in
``_pending_encounter`` and switches to :data:`MODE_ENCOUNTER`. Only
``ENCOUNTER_CHOICE`` advances it.

This module owns the half of the design that mutates state: spending a toll,
taking damage from a hazard or trap, granting a find, opening a formation
fight, and banking the insight a turn spent observing earns.

Two deliberate safety rules keep encounters from becoming a second death
system:

* road hazards and traps cannot kill -- they leave the player at 1 HP and feed
  the consequences into the *next* fight, which is where lethality belongs;
* hazard damage turned against a foe (the payoff for observing first) leaves
  that foe reeling at 1 HP rather than killing it outright, so the combat
  transition always has a living leader to field.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from game.core.constants import Action, EventType, MODE_COMBAT, MODE_ENCOUNTER, MODE_EXPLORE
from game.models.enemy import Enemy
from game.systems import currency as currency_helpers
from game.systems.encounter_system import foe_power

#: A road hazard never finishes what it starts.
HAZARD_HP_FLOOR = 1


class EncountersMixin:
    """Exploration encounters: prompt the player, apply their choice."""

    # -- scene construction ----------------------------------------------
    def _begin_encounter(self, descriptor: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Turn an exploration descriptor into a pending, choosable encounter.

        Returns ``None`` when the descriptor carries no real decision (a quiet
        wander, an unknown foe), leaving the caller to resolve it as before.
        """
        encounter = self.encounters.build(
            descriptor,
            self.player,
            danger=self._encounter_danger(),
            player_power=self._player_power(),
            pool=self._encounter_pool(),
        )
        if encounter is None:
            return None
        self._encounter_seq += 1
        encounter["id"] = f"enc-{self._encounter_seq}"
        self._pending_encounter = encounter
        self._mode = MODE_ENCOUNTER
        return self._encounter_prompt(encounter)

    def _encounter_prompt(
        self,
        encounter: Dict[str, Any],
        *,
        verb: Optional[str] = None,
        outcome: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Build the ENCOUNTER result the frontend renders as choice cards.

        ``outcome`` carries what an informational choice (observe/examine/study)
        already produced, so the refreshed prompt can still report the insight it
        banked or the trap it exposed.
        """
        context = {**self._narrative_context(), **(encounter.get("context") or {})}
        result: Dict[str, Any] = {
            "event": EventType.ENCOUNTER,
            "narrative": self.narrative.render(verb or encounter.get("scene_verb", "encounter"), context),
            **self._encounter_view(encounter),
        }
        if outcome:
            result["outcome"] = {
                "choice_id": outcome.get("choice_id"),
                "outcome": outcome.get("outcome"),
                "player_message": outcome.get("player_message", ""),
                **{key: outcome[key] for key in ("insight_gained", "exp_gained", "reveals", "damage", "hp") if key in outcome},
            }
        return result

    def _encounter_view(self, encounter: Dict[str, Any]) -> Dict[str, Any]:
        """Return the UI-safe projection of a pending encounter."""
        foes = [self._enemy_templates.get(foe_id, {}) for foe_id in (encounter.get("foes") or [])]
        view: Dict[str, Any] = {
            "encounter_id": encounter.get("id"),
            "kind": encounter.get("kind"),
            "title": encounter.get("title"),
            "text": encounter.get("text", ""),
            "danger": int(encounter.get("danger", 0) or 0),
            "ambush": bool(encounter.get("ambush")),
            "observed": bool(encounter.get("observed")),
            "options": self.encounters.options(encounter, self.player, self._player_power()),
        }
        if encounter.get("kind") == "combat":
            view["foes"] = [
                {
                    "id": str(foe.get("id", "")),
                    "name": str(foe.get("name", "a foe")),
                    "realm": self._body_realm_names.get(str(foe.get("body_realm_id", "")), str(foe.get("body_realm_id", ""))),
                    "power": int(foe_power(foe)) if foe else 0,
                }
                for foe in foes
            ]
            view["foe_count"] = len(foes)
            leader = foes[0] if foes else {}
            if leader:
                view["threat"] = self._threat_tier(foe_power(leader), self._player_power())
        reveal = self.encounters.reveal_view(encounter, self.player)
        if reveal:
            view["reveal"] = reveal
        return view

    def _clear_encounter_state(self) -> None:
        """Drop transient combat/encounter state (a run ending, or a load)."""
        self._pending_encounter = None
        self._current_foes = []
        self._defeated_foes = []
        self._leader_foe = None
        self._current_enemy = None
        self._combat_ambush = False

    def _encounter_danger(self) -> int:
        """Return the danger level of the area the player is exploring."""
        return int(self._location_danger.get(self.player.current_location, 0) or 0)

    def _encounter_pool(self) -> Dict[str, Any]:
        """Return the current location's encounter pool (empty when unmapped)."""
        return dict(self._encounter_pools.get(self.player.current_location) or {})

    def _player_power(self) -> float:
        """The player's single-number fighting weight, in the same units as a foe's.

        Shared by the threat preview, the parley/stealth odds, and the toll
        price so every number the player sees agrees with every other.
        """
        attack = self.stats.effective_stats(self.player).get("attack", self.player.attack)
        return float(
            self.player.max_hp
            + attack * 5
            + self.stats.effective_defense(self.player) * 3
        )

    def _threat_tier(self, foe_power: float, player_power: float) -> str:
        """Classify a foe relative to the player: Low, Moderate, High, or Deadly."""
        ratio = foe_power / player_power if player_power > 0 else 1.0
        if ratio < 0.6:
            return "Low"
        if ratio < 1.0:
            return "Moderate"
        if ratio < 1.5:
            return "High"
        return "Deadly"

    # -- dispatch ---------------------------------------------------------
    def _process_encounter_action(self, name: str, action: Dict[str, Any]) -> Dict[str, Any]:
        """Handle actions while an exploration encounter waits on a choice."""
        if name == Action.ENCOUNTER_CHOICE:
            return self._resolve_encounter(str(action.get("choice_id", "")))
        return {"event": EventType.ERROR, "reason": "INVALID_IN_ENCOUNTER", "input": name}

    def _resolve_encounter(self, choice_id: str) -> Dict[str, Any]:
        """Apply one encounter choice and return the outcome."""
        encounter = self._pending_encounter
        if encounter is None:
            self._mode = MODE_EXPLORE
            return {"event": EventType.ERROR, "reason": "NOT_IN_ENCOUNTER"}
        options = self.encounters.options(encounter, self.player, self._player_power())
        # Frontends that number the options (the CLI, and any text surface) may
        # send the 1-based index instead of the id; the engine owns the list, so
        # the mapping lives here rather than being duplicated per UI.
        if choice_id.isdigit():
            index = int(choice_id)
            if 1 <= index <= len(options):
                choice_id = options[index - 1]["choice_id"]
            else:
                return {
                    "event": EventType.ERROR,
                    "reason": "CHOICE_OUT_OF_RANGE",
                    "choice_id": choice_id,
                    "available": [option["choice_id"] for option in options],
                }
        chosen = next((option for option in options if option["choice_id"] == choice_id), None)
        if chosen is None:
            return {
                "event": EventType.ERROR,
                "reason": "UNKNOWN_CHOICE",
                "choice_id": choice_id,
                "available": [option["choice_id"] for option in options],
            }
        if not chosen.get("available", True):
            return {
                "event": EventType.ERROR,
                "reason": chosen.get("reason_code", "CHOICE_UNAVAILABLE"),
                "choice_id": choice_id,
                "player_message": chosen.get("reason", ""),
                "encounter": self._encounter_view(encounter),
            }

        payload = self.encounters.resolve(encounter, choice_id, self.player, self._player_power())
        return self._apply_encounter_payload(encounter, chosen, payload)

    def _apply_encounter_payload(
        self,
        encounter: Dict[str, Any],
        option: Dict[str, Any],
        payload: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Apply a resolved choice: pay, hurt, reward, fight, or keep waiting."""
        result: Dict[str, Any] = {
            "event": EventType.ENCOUNTER_RESULT,
            "encounter_id": encounter.get("id"),
            "kind": encounter.get("kind"),
            "choice_id": payload.get("choice") or option.get("choice_id"),
            "outcome": payload.get("outcome", "NONE"),
            "player_message": self._encounter_outcome_message(encounter, payload),
        }
        self._apply_encounter_costs(result, payload)
        self._apply_encounter_hurt(result, payload)
        self._apply_encounter_rewards(result, payload)
        if payload.get("reveals"):
            result["reveals"] = payload["reveals"]
        if payload.get("start_combat"):
            return self._start_encounter_combat(encounter, payload, result)
        if payload.get("resolve", True):
            self._pending_encounter = None
            self._mode = MODE_EXPLORE
        else:
            # Observing/studying costs the turn but keeps the scene open: hand
            # back a refreshed prompt so the player chooses with better eyes.
            self._mode = MODE_ENCOUNTER
            return self._encounter_prompt(encounter, verb=str(payload.get("verb", "encounter")), outcome=result)
        result["narrative"] = self.narrative.render(str(payload.get("verb", "encounter")), self._narrative_context())
        return result

    def _encounter_outcome_message(self, encounter: Dict[str, Any], payload: Dict[str, Any]) -> str:
        """A short, plain line describing what just happened (UI copy, not prose)."""
        outcome = str(payload.get("outcome", ""))
        messages = {
            "REVEALED": "You take the scene in before committing.",
            "PROVOKED": "They read your hesitation and close the distance.",
            "ENGAGED": "You commit to the fight.",
            "PARLEY": "Words carry the moment; they let you pass.",
            "NO_SPEECH": "There is nothing behind those eyes to reason with.",
            "OFFENDED": "Your offer lands badly, and steel answers.",
            "AVOIDED": "You slip past without a sound.",
            "SPOTTED": "A twig betrays you -- they are on you at once.",
            "NO_TIME": "There is no time to hide; they are already moving.",
            "TOLL_PAID": "The toll is paid and the road opens.",
            "TOLL_REFUSED": "They look at your coin and laugh.",
            "WITHDREW": "You back away and leave the road to them.",
            "CUT_OFF": "You turn to go and find the way already closed.",
            "EXAMINED": "You read the find before your hand moves.",
            "TAKEN": "You take it.",
            "LEFT": "You leave it where it lies.",
            "STUDIED": "You study what waits here.",
            "ACCEPTED": "You open yourself to the place.",
            "DECLINED": "You decline and walk on.",
            "ENGAGED_HAZARD": "The ground answers your step.",
            "CROSSED": "You cross it clean and breathe again.",
            "CAUGHT": "It takes its price from you.",
            "DEFUSED": "You find the way through and take its secret with you.",
            "FAILED": "Your reading is wrong, and you pay for it.",
        }
        return messages.get(outcome, "")

    def _apply_encounter_costs(self, result: Dict[str, Any], payload: Dict[str, Any]) -> None:
        """Spend whatever the choice cost (a toll, so far)."""
        cost = payload.get("cost")
        if not cost:
            return
        normalised = currency_helpers.normalise_price(cost)
        if currency_helpers.shortage(self.player, normalised):
            return
        currency_helpers.spend(self.player, normalised)
        result["cost"] = normalised
        result["wallet"] = currency_helpers.wallet_view(self.player)

    def _apply_encounter_hurt(self, result: Dict[str, Any], payload: Dict[str, Any]) -> None:
        """Apply hazard/trap damage, never fatally (see the module docstring)."""
        damage = int(payload.get("damage", 0) or 0)
        if damage <= 0:
            return
        allowed = max(0, self.player.hp - HAZARD_HP_FLOOR)
        dealt = self.player.take_damage(min(damage, allowed))
        result["damage"] = dealt
        result["hp"] = self.player.hp
        if dealt < damage:
            result["shrugged_off"] = True
        trap = payload.get("trap")
        if trap:
            result["trap"] = {"id": trap.get("id"), "name": trap.get("name"), "text": trap.get("text")}
        hazard = payload.get("hazard")
        if hazard:
            result["hazard"] = {"id": hazard.get("id"), "name": hazard.get("name")}

    def _apply_encounter_rewards(self, result: Dict[str, Any], payload: Dict[str, Any]) -> None:
        """Grant exp/reputation/insight/progress and any find the choice earned."""
        reward = payload.get("reward") or {}
        exp = int(reward.get("exp", 0) or 0)
        if exp:
            self.player.exp += exp
            result["exp_gained"] = exp
        reputation = int(reward.get("reputation", 0) or 0)
        if reputation:
            self.player.reputation += reputation
            result["reputation_gained"] = reputation
        insight = int(reward.get("insight", 0) or 0) + int(payload.get("insight", 0) or 0)
        if insight:
            self.player.insight += insight
            result["insight_gained"] = insight
        progress = int(reward.get("progress", 0) or 0)
        if progress:
            applied = self.effects.apply_to_player(self.player, "cultivation_boost", progress)
            result.update({key: value for key, value in applied.items() if key in ("progress_boost", "progress")})
        for effect_type in ("heal", "restore_qi", "restore"):
            magnitude = int(reward.get(effect_type, 0) or 0)
            if magnitude:
                result.update(self.effects.apply_to_player(self.player, effect_type, magnitude))
        loot = payload.get("loot")
        if loot and loot.get("item_id"):
            added = self.inventory.add_item(self.player, str(loot["item_id"]), int(loot.get("count", 1) or 1))
            if added.get("event") == EventType.LOOT:
                result["loot"] = added
        if payload.get("effect"):
            effect = payload["effect"]
            applied = self.effects.apply_to_player(self.player, str(effect.get("type", "none")), int(effect.get("magnitude", 0) or 0))
            result["effect"] = applied
            result.update({key: value for key, value in applied.items() if key not in ("note",)})

    # -- formation combat -------------------------------------------------
    def _start_encounter_combat(
        self,
        encounter: Dict[str, Any],
        payload: Dict[str, Any],
        result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Field the encounter's foes and open the fight the choice earned."""
        foes = self._spawn_formation(encounter)
        if not foes:
            self._pending_encounter = None
            self._mode = MODE_EXPLORE
            result["event"] = EventType.ENCOUNTER_RESULT
            result["outcome"] = "NO_FOES"
            return result

        self._pending_encounter = None
        self._current_foes = foes
        self._defeated_foes = []
        self._leader_foe = foes[0]
        self._current_enemy = foes[0]
        self._combat_ambush = bool(payload.get("ambush"))
        self._mode = MODE_COMBAT
        self._cooldowns = {}
        self._combat_is_spar = False
        self.player.statuses.clear()
        self.player.shield = 0
        self.combat.begin_combat(self.player)

        turn_events: List[Dict[str, Any]] = []
        hazard = payload.get("hazard")
        if hazard is not None and not hazard.get("neutralized"):
            if payload.get("hazard_to_player"):
                dealt = self.player.take_damage(max(0, min(int(hazard.get("effect", {}).get("magnitude", 0)), self.player.hp - HAZARD_HP_FLOOR)))
                turn_events.append({"actor": "HAZARD", "action": "STRIKE", "hazard": hazard.get("name"), "damage": dealt, "target_hp": self.player.hp})
            elif payload.get("hazard_revealed"):
                # The payoff for observing: you read the ground and lead them into it.
                for foe in foes:
                    if not foe.is_alive():
                        continue
                    dealt = foe.take_damage(max(0, int(hazard.get("effect", {}).get("magnitude", 0))))
                    turn_events.append({"actor": "HAZARD", "action": "STRIKE", "hazard": hazard.get("name"), "enemy_name": foe.name, "damage": dealt, "target_hp": foe.hp})
                    break
        if self._combat_ambush:
            turn_events.append(self.combat.ambush_strike(self.player, self._current_enemy))

        insight = int(payload.get("insight", 0) or 0)
        if insight:
            self.player.insight += insight

        if not self.player.is_alive():
            self._current_foes = []
            return self._end_combat({
                "event": EventType.COMBAT_END,
                "outcome": "DEFEAT",
                "enemy_name": self._current_enemy.name if self._current_enemy else "the wilds",
                "turn_events": turn_events,
            })

        return {
            # Carry the resolution (outcome, insight banked, reveals) into the
            # fight so the frontend can explain what led to it.
            **result,
            "event": EventType.COMBAT,
            "encounter_id": encounter.get("id"),
            "ambush": self._combat_ambush,
            "formation": len(foes) > 1,
            "enemy": self._enemy_view(self._current_enemy),
            "enemies": [self._enemy_view(foe) for foe in foes],
            "turn_events": turn_events,
            "text": self._encounter_combat_text(encounter, foes),
        }

    def _encounter_combat_text(self, encounter: Dict[str, Any], foes: List[Enemy]) -> str:
        """A short line naming who the player is now fighting."""
        leader = foes[0].name if foes else "a foe"
        if encounter.get("ambush"):
            return f"{leader} strikes before you can set your feet!"
        if len(foes) > 1:
            others = ", ".join(foe.name for foe in foes[1:])
            return f"{leader} is joined by {others}."
        return f"{leader} steps forward to meet you."

    def _spawn_formation(self, encounter: Dict[str, Any]) -> List[Enemy]:
        """Spawn the encounter's leader plus any extra foes, scaled as a pack."""
        foe_ids = list(encounter.get("foes") or [])
        if not foe_ids:
            return []
        scale = self.encounters.pack_scale()
        formation = self.encounters.formation_config()
        exp_ratio = float(formation.get("pack_exp_ratio", 0.5))
        spawned: List[Enemy] = []
        for index, foe_id in enumerate(foe_ids):
            enemy = self._spawn_enemy(str(foe_id))
            if index > 0:
                enemy.hp = enemy.max_hp = max(1, int(round(enemy.max_hp * scale)))
                enemy.attack = max(1, int(round(enemy.attack * scale)))
                enemy.defense = max(0, int(round(enemy.defense * scale)))
                enemy.exp_reward = max(1, int(round(enemy.exp_reward * exp_ratio)))
            spawned.append(enemy)
        return spawned

    # -- helpers used by the combat loop ----------------------------------
    def _living_foes(self) -> List[Enemy]:
        """Return the formation's surviving foes (empty outside a formation)."""
        return [foe for foe in (self._current_foes or []) if foe.is_alive()]

    def _retarget_foe(self, foe_id: str) -> Dict[str, Any]:
        """Focus the fight on a named foe of the current formation."""
        if self._current_enemy is None:
            return {"event": EventType.ERROR, "reason": "NOT_IN_COMBAT"}
        if not foe_id:
            return {"event": EventType.ERROR, "reason": "NO_FOE_SPECIFIED"}
        for foe in self._living_foes():
            if foe.id == foe_id:
                self._current_enemy = foe
                return {
                    "event": EventType.COMBAT_TURN,
                    "retargeted": foe.id,
                    "enemy": self._enemy_view(foe),
                    "enemies": [self._enemy_view(entry) for entry in self._living_foes()],
                    "turn_events": [{"actor": "PLAYER", "action": "RETARGET", "enemy_name": foe.name}],
                }
        return {"event": EventType.ERROR, "reason": "FOE_NOT_PRESENT", "foe_id": foe_id}
