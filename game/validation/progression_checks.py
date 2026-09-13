"""Collection validators for cultivation, realms, talents and pacing config.

Split out of ``data_validator`` (V.5) so the cultivation lane owns its own file.
Called by :func:`game.validation.data_validator.validate_all_game_data`; every
function keeps the signature and verdict it had before the split.

This module reads data only; it never mutates the registry or touches gameplay.
"""
from __future__ import annotations

import re
from typing import Any, Dict, List, Set

from game.data.registry import GameDataRegistry
from game.validation.support import _id_set
from game.validation.validation_error import ValidationResult


# -- cultivation --------------------------------------------------------
def _validate_cultivation_schema(registry: GameDataRegistry, result: ValidationResult) -> None:
    _validate_cultivation_track("body_transformation", registry.body_realms.get("realms", []), result)
    _validate_cultivation_track("essence_gathering", registry.essence_realms.get("realms", []), result)
    _validate_body_progression_config(registry.cultivation_config.get("body_progression", {}), result)
    _validate_essence_progression_config(registry.cultivation_config.get("essence_progression", {}), result)


def _validate_cultivation_track(track_id: str, realms: List[Dict[str, Any]], result: ValidationResult) -> None:
    stat_fields = {"body_strength", "max_hp", "max_qi", "attack", "defense"}
    for realm in realms:
        realm_id = realm.get("id")
        realm_type = realm.get("type")
        if realm_type in {"theoretical_endpoint", "late_game_stub"}:
            continue
        required_progress = realm.get("required_progress")
        if not isinstance(required_progress, (int, float)) or required_progress <= 0:
            result.add(
                "bad_cultivation_progress",
                f"{track_id} realm '{realm_id}' required_progress must be positive",
            )
        gains = realm.get("success_stat_gains", {})
        if gains and not isinstance(gains, dict):
            result.add("bad_cultivation_gain", f"{track_id} realm '{realm_id}' success_stat_gains must be an object")
            continue
        for field_name, value in gains.items():
            if field_name not in stat_fields:
                result.add(
                    "bad_cultivation_gain",
                    f"{track_id} realm '{realm_id}' success_stat_gains has unknown field '{field_name}'",
                )
            elif not isinstance(value, (int, float)) or value < 0:
                result.add(
                    "bad_cultivation_gain",
                    f"{track_id} realm '{realm_id}' success_stat_gains.{field_name} must be a non-negative number",
                )


def _validate_body_progression_config(config: Dict[str, Any], result: ValidationResult) -> None:
    for field_name in ("max_strain_for_breakthrough", "required_foundation_stability"):
        value = config.get(field_name)
        if not isinstance(value, (int, float)) or not 0 <= value <= 100:
            result.add("bad_cultivation_config", f"body_progression.{field_name} must be between 0 and 100")
    for field_name in ("training_strain_gain", "failed_breakthrough_strain_gain", "failed_breakthrough_foundation_loss"):
        value = config.get(field_name)
        if not isinstance(value, (int, float)) or value < 0:
            result.add("bad_cultivation_config", f"body_progression.{field_name} must be a non-negative number")
    ratio = config.get("failed_breakthrough_progress_ratio")
    if not isinstance(ratio, (int, float)) or not 0 <= ratio <= 1:
        result.add("bad_cultivation_config", "body_progression.failed_breakthrough_progress_ratio must be between 0 and 1")


def _validate_essence_progression_config(config: Dict[str, Any], result: ValidationResult) -> None:
    for field_name in ("max_strain_for_breakthrough", "required_foundation_stability"):
        value = config.get(field_name)
        if not isinstance(value, (int, float)) or not 0 <= value <= 100:
            result.add("bad_cultivation_config", f"essence_progression.{field_name} must be between 0 and 100")
    for field_name in ("training_strain_gain", "failed_breakthrough_strain_gain", "failed_breakthrough_foundation_loss"):
        value = config.get(field_name)
        if not isinstance(value, (int, float)) or value < 0:
            result.add("bad_cultivation_config", f"essence_progression.{field_name} must be a non-negative number")


# -- realms & defeat penalty --------------------------------------------
def _validate_defeat_penalty(registry: GameDataRegistry, result: ValidationResult) -> None:
    config = registry.cultivation_config.get("defeat_penalty", {})
    if not config:
        return
    for field in ("progress_loss_ratio", "revive_hp_ratio", "revive_qi_ratio"):
        value = config.get(field)
        if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
            result.add("bad_cultivation_config", f"defeat_penalty.{field} must be between 0 and 1")


def _validate_realm_lifespans(registry: GameDataRegistry, result: ValidationResult) -> None:
    for realm in registry.essence_realms.get("realms", []):
        if "max_lifespan_years" not in realm:
            continue
        value = realm["max_lifespan_years"]
        if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or value <= 0):
            result.add(
                "bad_realm_lifespan",
                f"essence realm '{realm.get('id')}' max_lifespan_years must be a positive number or null",
            )


# -- talent tracks ------------------------------------------------------
def _validate_talent_tracks(registry: GameDataRegistry, result: ValidationResult) -> None:
    _validate_trait_collection(
        "martial_talent",
        registry.martial_talents,
        {
            "essence_cultivation_multiplier",
            "comprehension_multiplier",
            "qi_strain_gain_multiplier",
        },
        {"essence_breakthrough_modifier"},
        result,
    )
    _validate_trait_collection(
        "body_talent",
        registry.body_talents,
        {
            "body_cultivation_multiplier",
            "body_stat_gain_multiplier",
            "injury_resistance_multiplier",
            "body_strain_gain_multiplier",
        },
        {"body_breakthrough_modifier"},
        result,
    )


def _validate_trait_collection(
    label: str,
    entries: List[Dict[str, Any]],
    positive_multiplier_fields: Set[str],
    modifier_fields: Set[str],
    result: ValidationResult,
) -> None:
    ids = _id_set(entries)
    if len(ids) != len([entry for entry in entries if "id" in entry]):
        result.add("duplicate_id", f"{label}: duplicate trait IDs")
    if not any(float(entry.get("roll_weight", 0)) > 0 for entry in entries):
        result.add("bad_fate_trait", f"{label}: at least one entry must be rollable")
    for entry in entries:
        entry_id = entry.get("id")
        if not isinstance(entry_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", entry_id):
            result.add("bad_fate_trait", f"{label}: id '{entry_id}' must be stable snake_case")
        if not isinstance(entry.get("display_name"), str) or not entry.get("display_name"):
            result.add("bad_fate_trait", f"{label} '{entry_id}' display_name is required")
        if not isinstance(entry.get("tier"), int) or isinstance(entry.get("tier"), bool) or entry.get("tier", 0) <= 0:
            result.add("bad_fate_trait", f"{label} '{entry_id}' tier must be positive")
        if not isinstance(entry.get("rarity"), str) or not entry.get("rarity"):
            result.add("bad_fate_trait", f"{label} '{entry_id}' rarity is required")
        if not isinstance(entry.get("roll_weight"), (int, float)) or entry.get("roll_weight", -1) < 0:
            result.add("bad_fate_trait", f"{label} '{entry_id}' roll_weight must be non-negative")
        for field_name in positive_multiplier_fields:
            value = entry.get(field_name)
            if not isinstance(value, (int, float)) or value <= 0:
                result.add("bad_fate_trait", f"{label} '{entry_id}' {field_name} must be positive")
        for field_name in modifier_fields:
            value = entry.get(field_name)
            if not isinstance(value, (int, float)) or not -1.0 <= value <= 1.0:
                result.add("bad_fate_trait", f"{label} '{entry_id}' {field_name} must be between -1.0 and 1.0")
        upgrades = entry.get("upgrade_options", [])
        if not isinstance(upgrades, list):
            result.add("bad_fate_trait", f"{label} '{entry_id}' upgrade_options must be a list")
            continue
        for upgrade in upgrades:
            target_id = upgrade.get("target_id") if isinstance(upgrade, dict) else None
            if target_id not in ids:
                result.add("bad_fate_trait", f"{label} '{entry_id}' upgrade target '{target_id}' does not exist")
            if target_id == entry_id:
                result.add("bad_fate_trait", f"{label} '{entry_id}' upgrade target cannot be itself")


def _validate_talent_upgrade_costs(registry: GameDataRegistry, result: ValidationResult) -> None:
    """Check talent upgrade costs reference real items with positive quantities."""
    item_ids = _id_set(registry.items) | _id_set(registry.equipment) | registry.manual_item_ids()
    for label, entries in (
        ("martial_talent", registry.martial_talents),
        ("body_talent", registry.body_talents),
    ):
        for entry in entries:
            entry_id = entry.get("id")
            for upgrade in entry.get("upgrade_options", []):
                if not isinstance(upgrade, dict):
                    continue
                cost = upgrade.get("cost", {})
                if not isinstance(cost, dict) or not cost:
                    result.add("bad_fate_trait", f"{label} '{entry_id}' upgrade cost must be a non-empty object")
                    continue
                for item_id, amount in cost.items():
                    if item_id not in item_ids:
                        result.add("bad_fate_trait", f"{label} '{entry_id}' upgrade cost references missing item '{item_id}'")
                    if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
                        result.add("bad_fate_trait", f"{label} '{entry_id}' upgrade cost '{item_id}' must be a positive integer")


# -- talent ladder ------------------------------------------------------
def _validate_talent_ladder(registry: GameDataRegistry, result: ValidationResult) -> None:
    tiers = registry.talents.get("tiers", [])
    if not tiers:
        result.add("bad_talent", "talent ladder has no tiers")
        return
    essence_ids = {realm.get("id") for realm in registry.essence_realms.get("realms", [])}
    valid_sources = {"canon", "extrapolated", "mixed"}
    name_fields = ("martial_talent_name", "body_talent_name", "cultivation_realm", "lifespan_display")
    seen_ids: Set[str] = set()
    seen_tiers: Set[int] = set()
    apex_count = 0
    for entry in tiers:
        entry_id = entry.get("id")
        if not isinstance(entry_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", entry_id):
            result.add("bad_talent", f"talent id '{entry_id}' must be stable snake_case")
            continue
        if entry_id in seen_ids:
            result.add("duplicate_id", f"talent: duplicate id '{entry_id}'")
        seen_ids.add(entry_id)
        tier = entry.get("tier")
        if not isinstance(tier, int) or isinstance(tier, bool) or tier <= 0:
            result.add("bad_talent", f"talent '{entry_id}' tier must be a positive integer")
        elif tier in seen_tiers:
            result.add("bad_talent", f"talent '{entry_id}' has duplicate tier {tier}")
        else:
            seen_tiers.add(tier)
        for field_name in name_fields:
            if not isinstance(entry.get(field_name), str) or not entry.get(field_name):
                result.add("bad_talent", f"talent '{entry_id}' {field_name} is required")
        lifespan = entry.get("max_lifespan_years")
        if lifespan is not None and (not isinstance(lifespan, int) or isinstance(lifespan, bool) or lifespan <= 0):
            result.add("bad_talent", f"talent '{entry_id}' max_lifespan_years must be a positive integer or null")
        if entry.get("source") not in valid_sources:
            result.add("bad_talent", f"talent '{entry_id}' source must be one of {sorted(valid_sources)}")
        realm_id = entry.get("realm_id")
        if realm_id is not None and realm_id not in essence_ids:
            result.add("bad_talent", f"talent '{entry_id}' realm_id '{realm_id}' is not a known essence realm")
        if entry.get("is_apex") is True:
            apex_count += 1
    if apex_count != 1:
        result.add("bad_talent", f"talent ladder must define exactly one apex tier, found {apex_count}")
