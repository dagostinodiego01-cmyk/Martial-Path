"""Dual-track cultivation system.

Owns the rules for Body Transformation and Essence Gathering. Realm names,
stage order, sequence IDs, training methods, and resource requirements are
loaded from JSON so progression remains data-driven. The system returns
structured dictionaries only; UI layers decide how to display them.
"""
from __future__ import annotations

from typing import Any, Dict, Iterable, List, Optional, Tuple, cast

from game.core.constants import EventType
from game.core.results import StabiliseResult
from game.models.cultivation import BreakthroughResult as CultivationBreakthroughResult
from game.models.player import Player
from game.utils.rng import RNG


class CultivationSystem:
    """Handles independent body and essence cultivation tracks."""

    BODY_TRACK_ID = "body_transformation"
    ESSENCE_TRACK_ID = "essence_gathering"
    BREAKTHROUGH_SUCCESS_CHANCE = 0.75

    def __init__(
        self,
        body_data: Dict[str, Any],
        essence_data: Dict[str, Any],
        config: Dict[str, Any],
        rng: RNG,
        spiritual_roots: Optional[List[Dict[str, Any]]] = None,
        physiques: Optional[List[Dict[str, Any]]] = None,
    ) -> None:
        self._body_data = body_data
        self._essence_data = essence_data
        self._config = config
        self._rng = rng
        self._body_realms = sorted(body_data.get("realms", []), key=lambda realm: int(realm.get("order", 0)))
        self._essence_realms = sorted(essence_data.get("realms", []), key=lambda realm: int(realm.get("order", 0)))
        self._body_by_id = {realm["id"]: realm for realm in self._body_realms}
        self._essence_by_id = {realm["id"]: realm for realm in self._essence_realms}
        self._spiritual_roots_by_id = {entry["id"]: entry for entry in spiritual_roots or [] if "id" in entry}
        self._physiques_by_id = {entry["id"]: entry for entry in physiques or [] if "id" in entry}

    def train(self, player: Player) -> Dict[str, Any]:
        """Backward-compatible default training action: train the body track."""
        return self.train_body(player, "train_body")

    def breakthrough(self, player: Player) -> Dict[str, Any]:
        """Backward-compatible default breakthrough action: advance the body track."""
        return self.attempt_body_breakthrough(player)

    def train_body(self, player: Player, method_id: str = "train_body") -> Dict[str, Any]:
        """Advance only Body Transformation progress."""
        state = player.cultivation_state.body
        realm = self._body_by_id.get(state.realm_id)
        if realm is None:
            return self._failure_result(self.BODY_TRACK_ID, "INVALID_REALM", state.realm_id)

        method = self._training_method("body_training_methods", method_id, "train_body")
        before = state.progress
        required_progress = self._required_body_progress(realm)
        self._record_body_training_day(player, state)
        daily_multiplier = self._daily_cultivation_multiplier(state.daily_cultivation_count)
        foundation_modifier = state.foundation / 100.0
        essence_support_modifier = self.calculate_essence_support_for_body(player)
        variance = self._rng.randint(0, 3)
        equipment_modifiers = self._equipment_modifiers(player).get("cultivation_modifiers", {})
        base_gain = float(method.get("base_gain", 8.0)) * self._physique_float(player, "body_cultivation_multiplier", 1.0)
        flat_bonus = float(equipment_modifiers.get("body_cultivation_flat_bonus", 0.0))
        gain = (base_gain * daily_multiplier) + foundation_modifier + essence_support_modifier + variance
        gain += flat_bonus
        state.progress = min(required_progress, state.progress + gain)
        state.foundation = min(100.0, state.foundation + float(method.get("foundation_gain", 0.5)))
        strain_gain = self._body_progression_float("training_strain_gain", float(method.get("fatigue_gain", 0.0))) * self._physique_float(player, "body_strain_gain_multiplier", 1.0)
        strain_gain *= float(equipment_modifiers.get("body_strain_gain_multiplier", 1.0))
        state.cultivation_strain = self._clamp(state.cultivation_strain + strain_gain)
        if state.realm_id == "tempering_marrow":
            state.marrow_percent = min(100.0, (state.progress / required_progress) * 100.0)
        player.progress = state.progress

        exp_gain = self._rng.randint(3, 8)
        player.exp += exp_gain
        return {
            "event": EventType.TRAIN_RESULT,
            "success": True,
            "track_id": self.BODY_TRACK_ID,
            "action_id": method.get("action_id", method_id),
            "gained": round(state.progress - before, 1),
            "progress_gained": round(state.progress - before, 1),
            "progress": round(state.progress, 1),
            "required_progress": round(required_progress, 1),
            "progress_percent": round((state.progress / required_progress) * 100.0, 1),
            "foundation_change": round(float(method.get("foundation_gain", 0.5)), 1),
            "fatigue_gained": round(strain_gain, 1),
            "strain_gained": round(strain_gain, 1),
            "current_strain": round(state.cultivation_strain, 1),
            "foundation_stability": round(state.foundation_stability, 1),
            "daily_cultivation_count": state.daily_cultivation_count,
            "daily_multiplier": round(daily_multiplier, 2),
            "exp_gained": exp_gain,
            "ready_to_breakthrough": self._body_missing_requirements(player) == [],
            "cultivation": self.get_body_display_name(player),
            "player_message": method.get("message", "Your body grows sturdier through training."),
        }

    def train_essence(self, player: Player, method_id: str = "gather_essence") -> Dict[str, Any]:
        """Advance only Essence Gathering progress."""
        state = player.cultivation_state.essence
        realm = self._essence_by_id.get(state.realm_id)
        if realm is None:
            return self._failure_result(self.ESSENCE_TRACK_ID, "INVALID_REALM", state.realm_id)
        if not self._essence_is_unlocked(player):
            return self._failure_result(self.ESSENCE_TRACK_ID, "ESSENCE_LOCKED_BY_BODY_PULSE", state.realm_id)

        method = self._training_method("essence_training_methods", method_id, "gather_essence")
        before = state.progress
        required_progress = self._required_essence_progress(realm)
        comprehension_modifier = state.foundation / 100.0
        body_stability_modifier = self.calculate_body_support_for_essence(player)
        density_bonus = state.true_essence_density / 100.0
        variance = self._rng.randint(0, 3)
        equipment_modifiers = self._equipment_modifiers(player).get("cultivation_modifiers", {})
        base_gain = float(method.get("base_gain", 8.0)) * self._spiritual_root_float(player, "essence_cultivation_multiplier", 1.0)
        gain = base_gain + comprehension_modifier + body_stability_modifier + density_bonus + variance
        gain += float(equipment_modifiers.get("essence_cultivation_flat_bonus", 0.0))
        state.progress = min(required_progress, state.progress + gain)
        state.foundation = min(100.0, state.foundation + float(method.get("foundation_gain", 0.5)))
        state.true_essence_density = max(1.0, state.true_essence_density + float(method.get("density_gain", 0.5)))
        state.dantian_capacity = max(1.0, state.dantian_capacity + float(method.get("capacity_gain", 1.0)))
        state.circulation_stability = max(1.0, min(100.0, state.circulation_stability + float(method.get("stability_gain", 0.5))))
        state.inner_world_development = min(
            100.0,
            state.inner_world_development + float(method.get("inner_world_gain", 0.0)),
        )
        strain_gain = self._essence_progression_float("training_strain_gain", float(method.get("fatigue_gain", 0.0)))
        strain_gain *= float(equipment_modifiers.get("essence_strain_gain_multiplier", 1.0))
        state.cultivation_strain = self._clamp(state.cultivation_strain + strain_gain)
        return {
            "event": EventType.TRAIN_RESULT,
            "success": True,
            "track_id": self.ESSENCE_TRACK_ID,
            "action_id": method.get("action_id", method_id),
            "gained": round(state.progress - before, 1),
            "progress_gained": round(state.progress - before, 1),
            "progress": round(state.progress, 1),
            "required_progress": round(required_progress, 1),
            "progress_percent": round((state.progress / required_progress) * 100.0, 1),
            "foundation_change": round(float(method.get("foundation_gain", 0.5)), 1),
            "fatigue_gained": round(strain_gain, 1),
            "strain_gained": round(strain_gain, 1),
            "current_strain": round(state.cultivation_strain, 1),
            "foundation_stability": round(state.foundation_stability, 1),
            "exp_gained": 0,
            "ready_to_breakthrough": self._essence_missing_requirements(player) == [],
            "cultivation": self.get_essence_display_name(player),
            "player_message": method.get("message", "Your true essence grows steadier."),
        }

    def attempt_body_breakthrough(self, player: Player) -> Dict[str, Any]:
        """Attempt a Body Transformation breakthrough without touching essence progress."""
        state = player.cultivation_state.body
        previous_realm_id = state.realm_id
        previous_display = self.get_body_display_name(player)
        missing = self._body_missing_requirements(player)
        if missing:
            reason = missing[0]
            result = self._breakthrough_failure(
                self.BODY_TRACK_ID,
                reason,
                state.progress,
                previous_realm_id,
                previous_display,
                missing_requirements=missing,
            )
            result.update(
                {
                    "current_strain": round(state.cultivation_strain, 1),
                    "foundation_stability": round(state.foundation_stability, 1),
                }
            )
            return result
        if not self._rng.chance(self._success_chance(player, self.BODY_TRACK_ID)):
            return self._failed_attempt(player, self.BODY_TRACK_ID)

        consumed = self._consume_body_resources(player)
        new_realm_id, unlocked = self._advance_body_state(player)
        stat_changes = self._body_stat_changes(player, new_realm_id, unlocked)
        self._apply_stat_changes(player, stat_changes)
        strain_reduction = self._body_progression_float("successful_breakthrough_strain_reduction", 0.0)
        state.cultivation_strain = self._clamp(state.cultivation_strain - strain_reduction)
        player.realm = self._body_by_id.get(state.realm_id, {}).get("display_name", player.realm)
        player.stage = 1
        result = CultivationBreakthroughResult(
            success=True,
            track_id=self.BODY_TRACK_ID,
            previous_realm_id=previous_realm_id,
            new_realm_id=state.realm_id,
            message_code="SUCCESS",
            player_message=f"Your body crosses its former limit and enters {self.get_body_display_name(player)}.",
            stat_changes=stat_changes,
            consumed_resources=consumed,
        ).to_dict()
        result.update(
            {
                "event": EventType.BREAKTHROUGH_RESULT,
                "previous": previous_display,
                "cultivation": self.get_body_display_name(player),
                "realm_changed": previous_realm_id != state.realm_id,
                "gains": stat_changes,
                "unlocked": unlocked,
                "progress": round(state.progress, 1),
                "cultivation_strain": round(state.cultivation_strain, 1),
                "foundation_stability": round(state.foundation_stability, 1),
            }
        )
        return result

    def attempt_essence_breakthrough(self, player: Player) -> Dict[str, Any]:
        """Attempt an Essence Gathering breakthrough without touching body progress."""
        state = player.cultivation_state.essence
        previous_realm_id = state.realm_id
        previous_substage = state.substage
        previous_display = self.get_essence_display_name(player)
        missing = self._essence_missing_requirements(player)
        if missing:
            reason = missing[0]
            result = self._breakthrough_failure(
                self.ESSENCE_TRACK_ID,
                reason,
                state.progress,
                previous_realm_id,
                previous_display,
                previous_substage=previous_substage,
                missing_requirements=missing,
            )
            result.update(
                {
                    "current_strain": round(state.cultivation_strain, 1),
                    "foundation_stability": round(state.foundation_stability, 1),
                }
            )
            return result
        if not self._rng.chance(self._success_chance(player, self.ESSENCE_TRACK_ID)):
            return self._failed_attempt(player, self.ESSENCE_TRACK_ID)

        advanced = self._advance_essence_state(player)
        if advanced == "REALM_LOCKED":
            return self._breakthrough_failure(
                self.ESSENCE_TRACK_ID,
                "REALM_LOCKED",
                state.progress,
                previous_realm_id,
                previous_display,
                previous_substage=previous_substage,
            )
        stat_changes = self._essence_stat_changes(state.realm_id)
        self._apply_stat_changes(player, stat_changes)
        strain_reduction = self._essence_progression_float("successful_breakthrough_strain_reduction", 0.0)
        state.cultivation_strain = self._clamp(state.cultivation_strain - strain_reduction)
        result = CultivationBreakthroughResult(
            success=True,
            track_id=self.ESSENCE_TRACK_ID,
            previous_realm_id=previous_realm_id,
            new_realm_id=state.realm_id,
            previous_substage=previous_substage,
            new_substage=state.substage,
            message_code="SUCCESS",
            player_message=f"Your true essence surges and stabilises at {self.get_essence_display_name(player)}.",
            stat_changes=stat_changes,
        ).to_dict()
        result.update(
            {
                "event": EventType.BREAKTHROUGH_RESULT,
                "previous": previous_display,
                "cultivation": self.get_essence_display_name(player),
                "realm_changed": previous_realm_id != state.realm_id,
                "gains": stat_changes,
                "progress": round(state.progress, 1),
                "cultivation_strain": round(state.cultivation_strain, 1),
                "foundation_stability": round(state.foundation_stability, 1),
            }
        )
        return result

    def stabilise_foundation(self, player: Player) -> Dict[str, Any]:
        """Reduce body cultivation strain and restore foundation stability."""
        state = player.cultivation_state.body
        realm = self._body_by_id.get(state.realm_id, {})
        config = self._config.get("body_progression", {}).get("stabilise", {})
        before_strain = state.cultivation_strain
        before_stability = state.foundation_stability
        before_progress = state.progress
        strain_reduction = float(config.get("strain_reduction", 18.0))
        foundation_gain = float(config.get("foundation_stability_gain", 4.0))
        comprehension_gain = int(config.get("comprehension_gain", 1))
        progress_gain = float(config.get("progress_gain", 0.0))
        required_progress = self._required_body_progress(realm)

        state.cultivation_strain = self._clamp(state.cultivation_strain - strain_reduction)
        state.foundation_stability = self._clamp(state.foundation_stability + foundation_gain)
        state.progress = min(required_progress, state.progress + progress_gain)
        player.progress = state.progress
        player.comprehension += comprehension_gain

        return StabiliseResult(
            strain_reduced=round(before_strain - state.cultivation_strain, 1),
            foundation_gained=round(state.foundation_stability - before_stability, 1),
            current_strain=round(state.cultivation_strain, 1),
            foundation_stability=round(state.foundation_stability, 1),
            comprehension_gain=comprehension_gain,
            comprehension=player.comprehension,
            progress_gained=round(state.progress - before_progress, 1),
            progress=round(state.progress, 1),
            required_progress=round(required_progress, 1),
            player_message=str(
                config.get(
                    "message",
                    "You slow your breathing and settle the restless force in your meridians.",
                )
            ),
        ).to_dict()

    def stabilise_essence(self, player: Player) -> Dict[str, Any]:
        """Reduce Essence Gathering strain and restore essence foundation stability."""
        state = player.cultivation_state.essence
        realm = self._essence_by_id.get(state.realm_id, {})
        config = self._config.get("essence_progression", {}).get("stabilise", {})
        before_strain = state.cultivation_strain
        before_stability = state.foundation_stability
        before_progress = state.progress
        strain_reduction = float(config.get("strain_reduction", 18.0))
        foundation_gain = float(config.get("foundation_stability_gain", 4.0))
        comprehension_gain = int(config.get("comprehension_gain", 1))
        progress_gain = float(config.get("progress_gain", 0.0))
        required_progress = self._required_essence_progress(realm)

        state.cultivation_strain = self._clamp(state.cultivation_strain - strain_reduction)
        state.foundation_stability = self._clamp(state.foundation_stability + foundation_gain)
        state.progress = min(required_progress, state.progress + progress_gain)
        player.comprehension += comprehension_gain

        return StabiliseResult(
            strain_reduced=round(before_strain - state.cultivation_strain, 1),
            foundation_gained=round(state.foundation_stability - before_stability, 1),
            current_strain=round(state.cultivation_strain, 1),
            foundation_stability=round(state.foundation_stability, 1),
            comprehension_gain=comprehension_gain,
            comprehension=player.comprehension,
            progress_gained=round(state.progress - before_progress, 1),
            progress=round(state.progress, 1),
            required_progress=round(required_progress, 1),
            player_message=str(
                config.get(
                    "message",
                    "You calm your churning true essence and let it settle evenly through your meridians.",
                )
            ),
        ).to_dict()

    def get_next_body_realm(self, realm_id: str) -> Optional[Dict[str, Any]]:
        """Return the next Body Transformation realm definition, if any."""
        return self._next_realm(self._body_realms, realm_id)

    def advance_essence_substage(self, player: Player) -> bool:
        """Advance Essence Gathering within the current realm when possible."""
        state = player.cultivation_state.essence
        realm = self._essence_by_id.get(state.realm_id, {})
        substages = self._substages_for(realm)
        if state.substage not in substages:
            state.substage = substages[0] if substages else ""
            return True
        index = substages.index(state.substage)
        if index + 1 >= len(substages):
            return False
        state.substage = substages[index + 1]
        state.progress = 0.0
        return True

    def advance_essence_realm(self, player: Player) -> bool:
        """Advance Essence Gathering to the next reachable realm when possible."""
        advanced = self._advance_essence_realm(player.cultivation_state.essence)
        return advanced == "ADVANCED"

    def get_body_display_name(self, player: Player) -> str:
        """Return the body track display name with sequence context."""
        state = player.cultivation_state.body
        realm = self._body_by_id.get(state.realm_id)
        if realm is None:
            return state.realm_id
        label = str(realm.get("display_name", state.realm_id))
        if realm.get("type") == "unlock_sequence":
            opened = self._opened_sequence(state, realm)
            if opened:
                return f"{label}: {self._sequence_name(opened[-1])}"
        return label

    def get_essence_display_name(self, player: Player) -> str:
        """Return the essence track display name with substage/fall context."""
        state = player.cultivation_state.essence
        realm = self._essence_by_id.get(state.realm_id)
        if realm is None:
            return state.realm_id
        label = str(realm.get("display_name", state.realm_id))
        if realm.get("type") == "numbered_falls":
            fall = state.life_destruction_fall or 1
            return f"{label} Fall {fall}"
        if state.substage:
            return f"{state.substage} {label}"
        return label

    def get_body_required_progress(self, player: Player) -> float:
        """Return the current Body Transformation progress requirement."""
        return self._required_body_progress(self._body_by_id.get(player.cultivation_state.body.realm_id, {}))

    def get_essence_required_progress(self, player: Player) -> float:
        """Return the current Essence Gathering progress requirement."""
        return self._required_essence_progress(self._essence_by_id.get(player.cultivation_state.essence.realm_id, {}))

    def calculate_body_stat_bonus(self, player: Player) -> Dict[str, int]:
        """Calculate current Body Transformation stat contribution."""
        realm = self._body_by_id.get(player.cultivation_state.body.realm_id, {})
        return {
            "max_hp": int(realm.get("base_hp_bonus", 0)),
            "physical_attack": int(realm.get("base_physical_attack_bonus", 0)),
            "physical_defence": int(realm.get("base_physical_defence_bonus", 0)),
            "body_strength": int(round(player.cultivation_state.body.body_strength)),
        }

    def calculate_essence_stat_bonus(self, player: Player) -> Dict[str, int]:
        """Calculate current Essence Gathering stat contribution."""
        realm = self._essence_by_id.get(player.cultivation_state.essence.realm_id, {})
        essence = player.cultivation_state.essence
        return {
            "max_qi": int(realm.get("base_qi_bonus", 0)),
            "technique_power": int(realm.get("base_technique_power_bonus", 0)),
            "dantian_capacity": int(round(essence.dantian_capacity + float(realm.get("base_dantian_capacity_bonus", 0)))),
            "spiritual_defence": int(round(essence.true_essence_density)),
        }

    def calculate_derived_cultivation_stats(self, player: Player) -> Dict[str, Any]:
        """Calculate derived stats from both tracks without persisting them."""
        body = self.calculate_body_stat_bonus(player)
        essence = self.calculate_essence_stat_bonus(player)
        safety = self.calculate_breakthrough_safety(player)
        return {
            "max_hp": player.max_hp + body["max_hp"],
            "max_qi": player.max_qi + essence["max_qi"] + int(player.cultivation_state.body.foundation / 10),
            "physical_attack": player.attack + body["physical_attack"],
            "technique_power": essence["technique_power"],
            "physical_defence": player.defense + body["physical_defence"],
            "spiritual_defence": essence["spiritual_defence"],
            "breakthrough_safety": safety["score"],
            "breakthrough_safety_level": safety["level"],
            "balance": self.calculate_body_essence_balance(player),
        }

    def calculate_body_essence_balance(self, player: Player) -> Dict[str, Any]:
        """Return balance status from relative realm order."""
        body_order = int(self._body_by_id.get(player.cultivation_state.body.realm_id, {}).get("order", 0))
        essence_order = int(self._essence_by_id.get(player.cultivation_state.essence.realm_id, {}).get("order", 0))
        difference = body_order - essence_order
        distance = abs(difference)
        thresholds = self._config.get("balance_thresholds", {})
        if distance <= int(thresholds.get("harmonised", 1)):
            status = "Harmonised"
        elif distance <= int(thresholds.get("leaning", 3)):
            status = "Body-Leaning" if difference > 0 else "Essence-Leaning"
        elif distance <= int(thresholds.get("unstable", 5)):
            status = "Unstable"
        else:
            status = "Severely Imbalanced"
        return {"status": status, "body_order": body_order, "essence_order": essence_order, "difference": difference}

    def calculate_breakthrough_safety(self, player: Player) -> Dict[str, Any]:
        """Estimate overall breakthrough safety from foundations and resources."""
        body = player.cultivation_state.body
        essence = player.cultivation_state.essence
        resource_support = min(20.0, sum(player.inventory.values()) * 2.0)
        score = min(100.0, (body.foundation * 0.4) + (essence.circulation_stability * 0.4) + resource_support)
        if score >= 75:
            level = "Strong"
        elif score >= 50:
            level = "Moderate"
        elif score >= 25:
            level = "Risky"
        else:
            level = "Dangerous"
        return {"score": round(score, 1), "level": level}

    def calculate_body_support_for_essence(self, player: Player) -> float:
        """Body foundation support used by essence training."""
        return player.cultivation_state.body.foundation / 100.0

    def calculate_essence_support_for_body(self, player: Player) -> float:
        """Essence density support used by body training."""
        return player.cultivation_state.essence.true_essence_density / 10.0

    def get_breakthrough_preview(self, player: Player, track_id: str) -> Dict[str, Any]:
        """Return a non-mutating breakthrough preview for a UI or API."""
        if track_id == self.BODY_TRACK_ID:
            missing = self._body_missing_requirements(player)
        elif track_id == self.ESSENCE_TRACK_ID:
            missing = self._essence_missing_requirements(player)
        else:
            missing = ["INVALID_REALM"]
        chance = 0.0 if missing else round(self._success_chance(player, track_id) * 100, 1)
        risk_level = self._risk_level(chance)
        warnings: List[str] = []
        balance = self.calculate_body_essence_balance(player)
        if balance["status"] in {"Unstable", "Severely Imbalanced"}:
            warnings.append("One cultivation path is much stronger than the other.")
        return {
            "track_id": track_id,
            "can_attempt": not missing,
            "success_chance": chance,
            "risk_level": risk_level,
            "missing_requirements": missing,
            "warnings": warnings,
        }

    def validate_cultivation_data(self, save_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Validate realm data and optional save-state references."""
        errors: List[str] = []
        all_ids = [realm.get("id") for realm in self._body_realms + self._essence_realms]
        if len(all_ids) != len(set(all_ids)):
            errors.append("Duplicate cultivation realm IDs found.")
        if "body_pulse_condensation" not in self._body_by_id:
            errors.append("Body Transformation must define body_pulse_condensation.")
        if "essence_pulse_condensation" in self._essence_by_id:
            errors.append("Pulse Condensation belongs only to Body Transformation.")
        errors.extend(self._validate_track(self.BODY_TRACK_ID, self._body_realms))
        errors.extend(self._validate_track(self.ESSENCE_TRACK_ID, self._essence_realms))
        errors.extend(self._validate_sequence_display_names())
        errors.extend(self._validate_required_resources())
        endpoint = self._essence_by_id.get("beyond_divinity", {})
        if endpoint.get("type") != "theoretical_endpoint" or endpoint.get("reachable") is not False:
            errors.append("beyond_divinity must remain an unreachable theoretical endpoint.")
        if save_data is not None:
            errors.extend(self._validate_save_data(save_data))
        return {"valid": not errors, "errors": errors}

    # -- internal breakthrough helpers ----------------------------------
    def _body_missing_requirements(self, player: Player) -> List[str]:
        state = player.cultivation_state.body
        realm = self._body_by_id.get(state.realm_id)
        if realm is None:
            return ["INVALID_REALM"]
        if realm.get("type") == "theoretical_endpoint":
            return ["REALM_LOCKED"]
        if self._is_body_at_peak(state, realm):
            return ["ALREADY_AT_PEAK"]
        requirements = realm.get("breakthrough_requirements", {})
        missing: List[str] = []
        progress_required = self._required_body_progress(realm)
        if state.progress < progress_required:
            missing.append("INSUFFICIENT_PROGRESS")
        max_strain = self._body_progression_float("max_strain_for_breakthrough", 45.0)
        if state.cultivation_strain > max_strain:
            missing.append("STRAIN_TOO_HIGH")
        stability_required = self._body_progression_float("required_foundation_stability", 70.0)
        effective_stability = state.foundation_stability + float(self._equipment_modifiers(player).get("cultivation_modifiers", {}).get("foundation_stability_bonus", 0.0))
        if effective_stability < stability_required:
            missing.append("FOUNDATION_UNSTABLE")
        foundation_min = float(requirements.get("foundation_min", 0.0))
        if state.foundation < foundation_min:
            missing.append("INSUFFICIENT_FOUNDATION")
        resources = requirements.get("resources", [])
        if any(player.inventory.get(resource_id, 0) <= 0 for resource_id in resources):
            missing.append("MISSING_RESOURCE")
        if player.hp <= 0:
            missing.append("INJURY_TOO_SEVERE")
        return missing

    def _essence_missing_requirements(self, player: Player) -> List[str]:
        state = player.cultivation_state.essence
        realm = self._essence_by_id.get(state.realm_id)
        if realm is None:
            return ["INVALID_REALM"]
        if realm.get("type") == "theoretical_endpoint" or realm.get("reachable") is False:
            return ["REALM_LOCKED"]
        if self._is_essence_at_peak(state, realm):
            return ["REALM_LOCKED"]
        required_progress = self._required_essence_progress(realm)
        missing: List[str] = []
        if not self._essence_is_unlocked(player):
            missing.append("ESSENCE_LOCKED_BY_BODY_PULSE")
        if state.progress < required_progress:
            missing.append("INSUFFICIENT_PROGRESS")
        max_strain = self._essence_progression_float("max_strain_for_breakthrough", 45.0)
        if state.cultivation_strain > max_strain:
            missing.append("STRAIN_TOO_HIGH")
        stability_required = self._essence_progression_float("required_foundation_stability", 70.0)
        effective_stability = state.foundation_stability + float(
            self._equipment_modifiers(player).get("cultivation_modifiers", {}).get("foundation_stability_bonus", 0.0)
        )
        if effective_stability < stability_required:
            missing.append("FOUNDATION_UNSTABLE")
        if state.foundation < 10.0:
            missing.append("INSUFFICIENT_FOUNDATION")
        if state.circulation_stability < 1.0:
            missing.append("ESSENCE_UNSTABLE")
        if player.cultivation_state.body.foundation < 5.0:
            missing.append("BODY_TOO_WEAK")
        return missing

    def is_essence_unlocked(self, player: Player) -> bool:
        """Public: has the body cleared Pulse Condensation, opening Essence Gathering?"""
        return self._essence_is_unlocked(player)

    def get_essence_unlock_requirement(self, player: Player) -> str:
        """Return a display string describing what unlocks Essence Gathering.

        Empty when Essence is already unlocked. Data-driven: the gating realm's
        display name is read from the cultivation data, not hard-coded here, so
        the UI can render it without knowing the unlock rule.
        """
        if self._essence_is_unlocked(player):
            return ""
        pulse = self._body_by_id.get("body_pulse_condensation", {})
        name = str(pulse.get("display_name", "Body Pulse Condensation"))
        return f"Complete {name}"

    def _essence_is_unlocked(self, player: Player) -> bool:
        body_state = player.cultivation_state.body
        pulse_realm = self._body_by_id.get("body_pulse_condensation")
        current_realm = self._body_by_id.get(body_state.realm_id)
        if pulse_realm is None or current_realm is None:
            return False
        current_order = int(current_realm.get("order", 0))
        pulse_order = int(pulse_realm.get("order", 0))
        if current_order > pulse_order:
            return True
        if body_state.realm_id != pulse_realm.get("id"):
            return False
        return self._body_missing_requirements(player) == []

    def _advance_body_state(self, player: Player) -> Tuple[str, str]:
        state = player.cultivation_state.body
        realm = self._body_by_id[state.realm_id]
        unlocked = ""
        if realm.get("type") == "unlock_sequence":
            sequence = list(realm.get("sequence", []))
            opened = self._opened_sequence(state, realm)
            if len(opened) < len(sequence):
                unlocked = sequence[len(opened)]
                opened.append(unlocked)
                state.progress = 0.0
                player.progress = 0.0
                if len(opened) < len(sequence):
                    return state.realm_id, unlocked
            next_realm = self.get_next_body_realm(state.realm_id)
            if next_realm is None:
                state.progress = 0.0
                player.progress = 0.0
                return state.realm_id, unlocked
            state.realm_id = str(next_realm["id"])
            state.progress = 0.0
            player.progress = 0.0
            return state.realm_id, unlocked

        next_realm = self.get_next_body_realm(state.realm_id)
        if next_realm is not None:
            state.realm_id = str(next_realm["id"])
        state.progress = 0.0
        if state.realm_id == "tempering_marrow":
            state.marrow_percent = 0.0
        player.progress = 0.0
        return state.realm_id, unlocked

    def _advance_essence_state(self, player: Player) -> str:
        state = player.cultivation_state.essence
        realm = self._essence_by_id[state.realm_id]
        if realm.get("type") == "numbered_falls":
            falls = int(realm.get("falls", 9))
            if state.life_destruction_fall < falls:
                state.life_destruction_fall += 1
                state.progress = 0.0
                return "ADVANCED"
            return self._advance_essence_realm(state)
        if self.advance_essence_substage(player):
            return "ADVANCED"
        return self._advance_essence_realm(state)

    def _advance_essence_realm(self, state: Any) -> str:
        next_realm = self._next_realm(self._essence_realms, state.realm_id)
        if next_realm is None:
            return "REALM_LOCKED"
        if next_realm.get("reachable") is False or next_realm.get("type") == "theoretical_endpoint":
            return "REALM_LOCKED"
        state.realm_id = str(next_realm["id"])
        state.progress = 0.0
        if next_realm.get("type") == "numbered_falls":
            state.substage = ""
            state.life_destruction_fall = 1
        else:
            substages = self._substages_for(next_realm)
            state.substage = substages[0] if substages else ""
            state.life_destruction_fall = 0
        return "ADVANCED"

    def _failed_attempt(self, player: Player, track_id: str) -> Dict[str, Any]:
        if track_id == self.BODY_TRACK_ID:
            state = player.cultivation_state.body
            previous = self.get_body_display_name(player)
            required_progress = self._required_body_progress(self._body_by_id.get(state.realm_id, {}))
            before = state.progress
            ratio = self._body_progression_float("failed_breakthrough_progress_ratio", 0.85)
            state.progress = min(state.progress, required_progress * ratio)
            lost = round(max(0.0, before - state.progress), 1)
            player.progress = state.progress
            strain_gain = self._body_progression_float("failed_breakthrough_strain_gain", 20.0)
            foundation_loss = self._body_progression_float("failed_breakthrough_foundation_loss", 10.0)
        else:
            state = player.cultivation_state.essence
            previous = self.get_essence_display_name(player)
            lost = self._rng.randint(20, 40)
            state.progress = max(0.0, state.progress - lost)
            strain_gain = self._essence_progression_float("failed_breakthrough_strain_gain", 18.0)
            foundation_loss = self._essence_progression_float("failed_breakthrough_foundation_loss", 10.0)
        state.cultivation_strain = self._clamp(state.cultivation_strain + strain_gain)
        state.foundation_stability = self._clamp(state.foundation_stability - foundation_loss)
        state.breakthrough_failures += 1
        previous_realm_id = state.realm_id
        return {
            "event": EventType.BREAKTHROUGH_RESULT,
            "success": False,
            "reason": "FAILED_ATTEMPT",
            "track_id": track_id,
            "previous_realm_id": previous_realm_id,
            "new_realm_id": previous_realm_id,
            "previous": previous,
            "progress_lost": lost,
            "progress": round(state.progress, 1),
            "message_code": "FAILED_ATTEMPT",
            "player_message": "The breakthrough fails and your gathered momentum scatters.",
            "strain_gained": round(strain_gain, 1),
            "current_strain": round(state.cultivation_strain, 1),
            "foundation_stability": round(state.foundation_stability, 1),
            "backlash": {
                "progress_lost": lost,
                "strain_gained": round(strain_gain, 1),
                "foundation_stability_lost": round(foundation_loss, 1),
            },
        }

    def _breakthrough_failure(
        self,
        track_id: str,
        reason: str,
        progress: float,
        realm_id: str,
        previous: str,
        previous_substage: str = "",
        missing_requirements: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        messages = self._config.get("failure_messages", {})
        result = {
            "event": EventType.BREAKTHROUGH_RESULT,
            "success": False,
            "reason": reason,
            "track_id": track_id,
            "previous_realm_id": realm_id,
            "new_realm_id": realm_id,
            "previous_substage": previous_substage,
            "new_substage": previous_substage,
            "previous": previous,
            "progress": round(progress, 1),
            "message_code": reason,
            "player_message": messages.get(reason, "The breakthrough cannot be attempted."),
            "missing_requirements": list(missing_requirements or [reason]),
        }
        if track_id == self.BODY_TRACK_ID:
            realm = self._body_by_id.get(realm_id, {})
            result.update(
                {
                    "required_progress": round(self._required_body_progress(realm), 1),
                    "max_allowed_strain": round(self._body_progression_float("max_strain_for_breakthrough", 45.0), 1),
                    "required_foundation_stability": round(
                        self._body_progression_float("required_foundation_stability", 70.0),
                        1,
                    ),
                }
            )
        elif track_id == self.ESSENCE_TRACK_ID:
            realm = self._essence_by_id.get(realm_id, {})
            result.update(
                {
                    "required_progress": round(self._required_essence_progress(realm), 1),
                    "max_allowed_strain": round(self._essence_progression_float("max_strain_for_breakthrough", 45.0), 1),
                    "required_foundation_stability": round(
                        self._essence_progression_float("required_foundation_stability", 70.0),
                        1,
                    ),
                }
            )
        return result

    def _failure_result(self, track_id: str, reason: str, realm_id: str) -> Dict[str, Any]:
        return {
            "event": EventType.ERROR,
            "success": False,
            "track_id": track_id,
            "reason": reason,
            "realm_id": realm_id,
            "player_message": self._config.get("failure_messages", {}).get(reason, reason),
        }

    def _consume_body_resources(self, player: Player) -> List[str]:
        realm = self._body_by_id[player.cultivation_state.body.realm_id]
        resources = list(realm.get("breakthrough_requirements", {}).get("resources", []))
        for resource_id in resources:
            player.inventory[resource_id] = player.inventory.get(resource_id, 0) - 1
            if player.inventory[resource_id] <= 0:
                player.inventory.pop(resource_id, None)
        return resources

    def _body_stat_changes(self, player: Player, realm_id: str, unlocked: str = "") -> Dict[str, int]:
        realm = self._body_by_id.get(realm_id, {})
        divisor = max(1, len(realm.get("sequence", []))) if unlocked else 1
        gains = realm.get("success_stat_gains", {})
        multiplier = self._physique_float(player, "body_stat_gain_multiplier", 1.0)
        return {
            "max_hp": self._scaled_body_gain(gains.get("max_hp", realm.get("base_hp_bonus", 0)), multiplier, divisor),
            "attack": self._scaled_body_gain(gains.get("attack", realm.get("base_physical_attack_bonus", 0)), multiplier, divisor),
            "defense": self._scaled_body_gain(gains.get("defense", realm.get("base_physical_defence_bonus", 0)), multiplier, divisor),
            "body_strength": self._scaled_body_gain(gains.get("body_strength", 0), multiplier, divisor),
            "max_qi": self._scaled_body_gain(gains.get("max_qi", 0), multiplier, divisor),
        }

    def _essence_stat_changes(self, realm_id: str) -> Dict[str, int]:
        realm = self._essence_by_id.get(realm_id, {})
        return {
            "max_hp": 0,
            "max_qi": max(0, int(realm.get("base_qi_bonus", 0)) // 4),
            "attack": 0,
            "defense": max(0, int(realm.get("base_technique_power_bonus", 0)) // 8),
        }

    def _apply_stat_changes(self, player: Player, changes: Dict[str, int]) -> None:
        player.max_hp += int(changes.get("max_hp", 0))
        player.max_qi += int(changes.get("max_qi", 0))
        player.attack += int(changes.get("attack", 0))
        player.defense += int(changes.get("defense", 0))
        body_strength_gain = int(changes.get("body_strength", 0))
        if body_strength_gain:
            player.body_strength += body_strength_gain
            player.cultivation_state.body.body_strength += body_strength_gain
        player.hp = player.max_hp
        player.qi = player.max_qi

    def _success_chance(self, player: Player, track_id: str) -> float:
        if track_id == self.BODY_TRACK_ID:
            foundation = player.cultivation_state.body.foundation
            support = self.calculate_essence_support_for_body(player) * 10.0
            trait_modifier = self._physique_float(player, "body_breakthrough_modifier", 0.0)
            equipment_modifier = float(self._equipment_modifiers(player).get("cultivation_modifiers", {}).get("body_breakthrough_modifier", 0.0))
        else:
            foundation = player.cultivation_state.essence.foundation
            support = self.calculate_body_support_for_essence(player) * 10.0
            trait_modifier = self._spiritual_root_float(player, "essence_breakthrough_modifier", 0.0)
            equipment_modifier = float(self._equipment_modifiers(player).get("cultivation_modifiers", {}).get("essence_breakthrough_modifier", 0.0))
        chance = self.BREAKTHROUGH_SUCCESS_CHANCE + ((foundation - 50.0) / 200.0) + (support / 200.0)
        chance += trait_modifier
        chance += equipment_modifier
        chance += float(self._equipment_modifiers(player).get("cultivation_modifiers", {}).get("breakthrough_chance_modifier", 0.0))
        # Light comprehension aid: sharper insight modestly improves the odds.
        chance += (player.comprehension - 10) / 400.0
        return max(0.05, min(0.95, chance))

    def _risk_level(self, success_chance: float) -> str:
        if success_chance >= 80:
            return "Low"
        if success_chance >= 60:
            return "Moderate"
        if success_chance >= 35:
            return "High"
        return "Severe"

    def _training_method(self, group: str, method_id: str, default_id: str) -> Dict[str, Any]:
        methods = self._config.get(group, {})
        return dict(methods.get(method_id) or methods.get(default_id) or {})

    def _required_body_progress(self, realm: Dict[str, Any]) -> float:
        requirements = realm.get("breakthrough_requirements", {})
        return float(realm.get("required_progress", requirements.get("progress", realm.get("max_progress", 100.0))))

    def _required_essence_progress(self, realm: Dict[str, Any]) -> float:
        return float(
            realm.get(
                "required_progress",
                realm.get("max_progress_per_substage", realm.get("max_progress_per_fall", 100.0)),
            )
        )

    def _record_body_training_day(self, player: Player, state: Any) -> None:
        current_day = int(getattr(player, "current_day", 1))
        if state.last_cultivation_day != current_day:
            state.last_cultivation_day = current_day
            state.daily_cultivation_count = 0
        state.daily_cultivation_count += 1

    def _daily_cultivation_multiplier(self, daily_count: int) -> float:
        multipliers = list(self._config.get("body_progression", {}).get("daily_cultivation_multipliers", [1.0]))
        if not multipliers:
            return 1.0
        index = max(0, daily_count - 1)
        return float(multipliers[min(index, len(multipliers) - 1)])

    def _body_progression_float(self, key: str, default: float) -> float:
        return float(self._config.get("body_progression", {}).get(key, default))

    def _essence_progression_float(self, key: str, default: float) -> float:
        return float(self._config.get("essence_progression", {}).get(key, default))

    def _clamp(self, value: float, minimum: float = 0.0, maximum: float = 100.0) -> float:
        return max(minimum, min(maximum, value))

    def _spiritual_root_float(self, player: Player, key: str, default: float) -> float:
        trait = self._spiritual_roots_by_id.get(player.martial_talent_id) or self._spiritual_roots_by_id.get("earth_grade") or {}
        return float(trait.get(key, default))

    def _physique_float(self, player: Player, key: str, default: float) -> float:
        trait = self._physiques_by_id.get(player.body_talent_id) or self._physiques_by_id.get("iron_skin_grade") or {}
        return float(trait.get(key, default))

    def _scaled_body_gain(self, value: Any, multiplier: float, divisor: int) -> int:
        return max(0, int(round(float(value) * multiplier)) // divisor)

    def _equipment_modifiers(self, player: Player) -> Dict[str, Dict[str, float]]:
        modifiers = getattr(player, "equipment_modifiers", None)
        if callable(modifiers):
            return cast(Dict[str, Dict[str, float]], modifiers())
        return getattr(player, "_equipment_modifiers", {})

    def _next_realm(self, realms: Iterable[Dict[str, Any]], realm_id: str) -> Optional[Dict[str, Any]]:
        ordered = list(realms)
        for index, realm in enumerate(ordered):
            if realm.get("id") == realm_id and index + 1 < len(ordered):
                return ordered[index + 1]
        return None

    def _substages_for(self, realm: Dict[str, Any]) -> List[str]:
        return list(realm.get("substages", self._essence_data.get("default_substages", [])))

    def _opened_sequence(self, state: Any, realm: Dict[str, Any]) -> List[str]:
        sequence_key = realm.get("sequence_key")
        if sequence_key == "opened_stars":
            return state.opened_stars
        return state.opened_gates

    def _sequence_name(self, item_id: str) -> str:
        return str(self._config.get("sequence_display_names", {}).get(item_id, item_id))

    def _is_body_at_peak(self, state: Any, realm: Dict[str, Any]) -> bool:
        next_realm = self.get_next_body_realm(state.realm_id)
        if next_realm is not None:
            return False
        if realm.get("type") == "unlock_sequence":
            return len(self._opened_sequence(state, realm)) >= len(realm.get("sequence", []))
        return False

    def _is_essence_at_peak(self, state: Any, realm: Dict[str, Any]) -> bool:
        next_realm = self._next_realm(self._essence_realms, state.realm_id)
        if next_realm is None:
            return True
        if next_realm.get("reachable") is False or next_realm.get("type") == "theoretical_endpoint":
            substages = self._substages_for(realm)
            return state.substage == (substages[-1] if substages else state.substage)
        return False

    # -- validation ------------------------------------------------------
    def _validate_track(self, track_id: str, realms: List[Dict[str, Any]]) -> List[str]:
        errors: List[str] = []
        ids = [realm.get("id") for realm in realms]
        orders = [realm.get("order") for realm in realms]
        if len(ids) != len(set(ids)):
            errors.append(f"{track_id} has duplicate realm IDs.")
        if len(orders) != len(set(orders)):
            errors.append(f"{track_id} has duplicate realm order values.")
        required = {"id", "display_name", "order", "type"}
        for realm in realms:
            missing = required - set(realm)
            if missing:
                errors.append(f"{track_id}.{realm.get('id', '<missing>')} missing fields: {sorted(missing)}")
            if realm.get("type") == "unlock_sequence" and not realm.get("sequence"):
                errors.append(f"{track_id}.{realm.get('id')} unlock_sequence must define sequence.")
            if realm.get("type") == "late_game_stub" and "substages" not in realm:
                errors.append(f"{track_id}.{realm.get('id')} late_game_stub must define substages.")
            if realm.get("type") not in {"late_game_stub", "theoretical_endpoint"}:
                required_progress = realm.get("required_progress")
                if not isinstance(required_progress, (int, float)) or required_progress <= 0:
                    errors.append(f"{track_id}.{realm.get('id')} required_progress must be positive.")
            gains = realm.get("success_stat_gains", {})
            if gains and not isinstance(gains, dict):
                errors.append(f"{track_id}.{realm.get('id')} success_stat_gains must be an object.")
            elif isinstance(gains, dict):
                for stat_name, value in gains.items():
                    if stat_name not in {"body_strength", "max_hp", "max_qi", "attack", "defense"}:
                        errors.append(f"{track_id}.{realm.get('id')} success_stat_gains has unknown field {stat_name}.")
                    elif not isinstance(value, (int, float)) or value < 0:
                        errors.append(f"{track_id}.{realm.get('id')} success_stat_gains.{stat_name} must be non-negative.")
        return errors

    def _validate_sequence_display_names(self) -> List[str]:
        errors: List[str] = []
        names = self._config.get("sequence_display_names", {})
        for realm in self._body_realms:
            for item_id in realm.get("sequence", []):
                if item_id not in names:
                    errors.append(f"Missing sequence display name for {item_id}.")
        return errors

    def _validate_required_resources(self) -> List[str]:
        errors: List[str] = []
        known = set(self._config.get("known_resource_ids", []))
        for realm in self._body_realms:
            for resource_id in realm.get("breakthrough_requirements", {}).get("resources", []):
                if resource_id not in known:
                    errors.append(f"Unknown cultivation resource {resource_id}.")
        return errors

    def _validate_save_data(self, save_data: Dict[str, Any]) -> List[str]:
        errors: List[str] = []
        cultivation = save_data.get("cultivation", save_data)
        body = cultivation.get("body_transformation", {})
        essence = cultivation.get("essence_gathering", {})
        body_realm_id = body.get("realm_id")
        essence_realm_id = essence.get("realm_id")
        if body_realm_id not in self._body_by_id:
            errors.append(f"Save references unknown body realm {body_realm_id}.")
        if essence_realm_id not in self._essence_by_id:
            errors.append(f"Save references unknown essence realm {essence_realm_id}.")
        if essence_realm_id in self._essence_by_id:
            realm = self._essence_by_id[essence_realm_id]
            substages = self._substages_for(realm)
            substage = essence.get("substage", "")
            if substages and substage not in substages:
                errors.append(f"Save references invalid essence substage {substage}.")
        return errors
