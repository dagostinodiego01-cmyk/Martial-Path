"""Central data validation.

Loads the :class:`GameDataRegistry` and checks the cross-references that break
most easily as content grows: dangling item/enemy/character/location ids, id
collisions, and mismatched morality/relationship keys. Everything is collected
into one :class:`ValidationResult`, so ``validate_all_game_data()`` answers a
single question -- "is the shipped content internally consistent?" -- for tests,
tooling, or a pre-flight check.

This module reads data only; it never mutates the registry or touches gameplay.
"""
from __future__ import annotations

import re
from typing import Any, Dict, Iterable, List, Optional, Set

from game.core.constants import AVAILABLE_SYSTEMS
from game.data.registry import GameDataRegistry
from game.systems.origin_system import STAT_FIELDS
from game.validation.validation_error import ValidationResult


def validate_all_game_data(registry: Optional[GameDataRegistry] = None) -> ValidationResult:
    """Validate every static content collection and return the collected result."""
    registry = registry or GameDataRegistry.load()
    result = ValidationResult()

    _validate_unique_ids(registry, result)
    _validate_item_references(registry, result)
    _validate_character_enemy_links(registry, result)
    _validate_enemy_realms(registry, result)
    _validate_character_reaction_keys(registry, result)
    _validate_character_hooks(registry, result)
    _validate_locations(registry, result)
    _validate_encounter_pools(registry, result)
    _validate_map_positions(registry, result)
    _validate_enemy_abilities(registry, result)
    _validate_cultivation_schema(registry, result)
    _validate_defeat_penalty(registry, result)
    _validate_realm_lifespans(registry, result)
    _validate_talent_tracks(registry, result)
    _validate_talent_upgrade_costs(registry, result)
    _validate_talent_ladder(registry, result)
    _validate_equipment_data(registry, result)
    _validate_shop_data(registry, result)
    _validate_trainers(registry, result)
    _validate_sects(registry, result)
    _validate_daos(registry, result)
    _validate_skills(registry, result)
    _validate_narrative_templates(registry, result)
    _validate_origins(registry, result)
    _validate_gathering(registry, result)
    _validate_refining_recipes(registry, result)
    _validate_secret_realm(registry, result)
    _validate_technique_manuals(registry, result)
    _validate_find_config(registry, result)
    _validate_quests(registry, result)

    return result


# -- unique ids ----------------------------------------------------------
def _validate_unique_ids(registry: GameDataRegistry, result: ValidationResult) -> None:
    collections = {
        "items": registry.items,
        "skills": registry.skills,
        "enemies": registry.enemies,
        "character_enemies": registry.character_enemies,
        "characters": registry.characters,
        "quests": registry.quests,
        "locations": registry.locations,
        "shops": registry.shops,
    }
    for label, entries in collections.items():
        seen: Set[str] = set()
        for entry in entries:
            entry_id = entry.get("id")
            if entry_id is None:
                result.add("missing_id", f"{label}: an entry has no 'id'")
                continue
            if entry_id in seen:
                result.add("duplicate_id", f"{label}: duplicate id '{entry_id}'")
            seen.add(entry_id)

    # Named foes must not leak into the random exploration pool.
    random_ids = _id_set(registry.enemies)
    named_ids = _id_set(registry.character_enemies)
    for shared in sorted(random_ids & named_ids):
        result.add("pool_overlap", f"enemy id '{shared}' is in both the random pool and named foes")


# -- item references -----------------------------------------------------
def _validate_item_references(registry: GameDataRegistry, result: ValidationResult) -> None:
    item_ids = _id_set(registry.items) | _id_set(registry.equipment) | registry.manual_item_ids()

    for enemy in registry.enemies:
        _check_loot(enemy, item_ids, "enemy_loot", result)
    for enemy in registry.character_enemies:
        _check_loot(enemy, item_ids, "character_enemy_loot", result)

    for quest in registry.quests:
        reward_items = quest.get("rewards", {}).get("items", {})
        for item_id in reward_items:
            if item_id not in item_ids:
                result.add("bad_item_ref", f"quest '{quest.get('id')}' rewards missing item '{item_id}'")

    for loot in registry.events.get("loot_pool", []):
        if loot.get("item_id") not in item_ids:
            result.add("bad_item_ref", f"event loot_pool references missing item '{loot.get('item_id')}'")

    for realm in registry.body_realms.get("realms", []):
        for resource_id in realm.get("breakthrough_requirements", {}).get("resources", []):
            if resource_id not in item_ids:
                result.add(
                    "bad_item_ref",
                    f"body realm '{realm.get('id')}' breakthrough needs missing item '{resource_id}'",
                )
    for realm in registry.essence_realms.get("realms", []):
        for resource_id in realm.get("breakthrough_requirements", {}).get("resources", []):
            if resource_id not in item_ids:
                result.add(
                    "bad_item_ref",
                    f"essence realm '{realm.get('id')}' breakthrough needs missing item '{resource_id}'",
                )


def _check_loot(entity: Dict[str, Any], item_ids: Set[str], category: str, result: ValidationResult) -> None:
    for drop in entity.get("loot_table", []):
        item_id = drop.get("item_id")
        if item_id not in item_ids:
            result.add(category, f"'{entity.get('id')}' drops missing item '{item_id}'")


# -- character <-> enemy links -------------------------------------------
def _validate_character_enemy_links(registry: GameDataRegistry, result: ValidationResult) -> None:
    character_ids = _id_set(registry.characters)
    enemy_ids = _id_set(registry.enemies) | _id_set(registry.character_enemies)

    for foe in registry.character_enemies:
        character_id = foe.get("character_id")
        if character_id not in character_ids:
            result.add(
                "bad_character_ref",
                f"character_enemy '{foe.get('id')}' points at missing character '{character_id}'",
            )

    for character in registry.characters:
        enemy_id = character.get("gameplay_hooks", {}).get("enemy_id", "")
        if enemy_id and enemy_id not in enemy_ids:
            result.add(
                "bad_enemy_ref",
                f"character '{character.get('id')}' hook references missing enemy '{enemy_id}'",
            )


def _validate_enemy_realms(registry: GameDataRegistry, result: ValidationResult) -> None:
    body_ids = {realm.get("id") for realm in registry.body_realms.get("realms", [])}
    essence_ids = {realm.get("id") for realm in registry.essence_realms.get("realms", [])}
    for collection_name, enemies in (
        ("enemy", registry.enemies),
        ("character_enemy", registry.character_enemies),
    ):
        for enemy in enemies:
            enemy_id = enemy.get("id")
            if "level" in enemy:
                result.add("bad_enemy_realm", f"{collection_name} '{enemy_id}' must use realms, not level")
            body_realm_id = enemy.get("body_realm_id")
            if body_realm_id not in body_ids:
                result.add("bad_enemy_realm", f"{collection_name} '{enemy_id}' has unknown body_realm_id '{body_realm_id}'")
            essence_realm_id = enemy.get("essence_realm_id")
            if essence_realm_id is not None and essence_realm_id not in essence_ids:
                result.add("bad_enemy_realm", f"{collection_name} '{enemy_id}' has unknown essence_realm_id '{essence_realm_id}'")

# -- morality / relationship keys ----------------------------------------
def _validate_character_reaction_keys(registry: GameDataRegistry, result: ValidationResult) -> None:
    band_ids = {band["id"] for band in registry.morality.get("bands", [])}
    tier_ids = {tier["id"] for tier in registry.relationships.get("tiers", [])}

    for character in registry.characters:
        personality = character.get("personality", {})
        reaction_keys = set(personality.get("morality_reaction", {}).keys())
        if band_ids and reaction_keys != band_ids:
            result.add(
                "morality_key_mismatch",
                f"character '{character.get('id')}' morality_reaction keys {sorted(reaction_keys)} "
                f"!= bands {sorted(band_ids)}",
            )
        behavior_keys = set(personality.get("relationship_behavior", {}).keys())
        if tier_ids and behavior_keys != tier_ids:
            result.add(
                "relationship_key_mismatch",
                f"character '{character.get('id')}' relationship_behavior keys {sorted(behavior_keys)} "
                f"!= tiers {sorted(tier_ids)}",
            )


def _validate_character_hooks(registry: GameDataRegistry, result: ValidationResult) -> None:
    """Check relationship/morality gates and relationship rewards reference real
    tiers, bands, items, and skills."""
    band_ids = {band["id"] for band in registry.morality.get("bands", [])}
    tier_ids = {tier["id"] for tier in registry.relationships.get("tiers", [])}
    skill_ids = {skill["id"] for skill in registry.skills}
    item_ids = _id_set(registry.items) | set(registry.manual_item_ids())

    for character in registry.characters:
        character_id = character.get("id")
        hooks = character.get("gameplay_hooks", {})
        for hook_key in ("spar_min_tier", "duel_min_tier"):
            tier = hooks.get(hook_key)
            if tier and tier_ids and tier not in tier_ids:
                result.add("bad_relationship_tier", f"character '{character_id}' {hook_key} references unknown tier '{tier}'")
        for hook_key in ("spar_morality_band", "duel_morality_band"):
            band = hooks.get(hook_key)
            if band and band_ids and band not in band_ids:
                result.add("bad_morality_band", f"character '{character_id}' {hook_key} references unknown band '{band}'")

        for reward in hooks.get("relationship_rewards", []):
            if not isinstance(reward, dict):
                continue
            min_tier = reward.get("min_tier")
            if min_tier and tier_ids and min_tier not in tier_ids:
                result.add("bad_relationship_tier", f"character '{character_id}' reward min_tier references unknown tier '{min_tier}'")
            band = reward.get("morality_band")
            if band and band_ids and band not in band_ids:
                result.add("bad_morality_band", f"character '{character_id}' reward morality_band references unknown band '{band}'")
            payload = reward.get("reward", {})
            item_id = payload.get("item_id")
            if item_id and item_id not in item_ids:
                result.add("bad_item_ref", f"character '{character_id}' reward references unknown item '{item_id}'")
            skill_id = payload.get("skill_id")
            if skill_id and skill_id not in skill_ids:
                result.add("bad_skill_ref", f"character '{character_id}' reward references unknown skill '{skill_id}'")


# -- locations -----------------------------------------------------------
def _validate_locations(registry: GameDataRegistry, result: ValidationResult) -> None:
    location_ids = _id_set(registry.locations)
    character_ids = _id_set(registry.characters)

    for location in registry.locations:
        location_id = location.get("id")
        for neighbor in _connections(location):
            if neighbor not in location_ids:
                result.add("bad_location_ref", f"location '{location_id}' connects to missing '{neighbor}'")

        for npc_id in location.get("npc_ids", []):
            if npc_id not in character_ids:
                result.add("bad_npc_ref", f"location '{location_id}' lists missing NPC '{npc_id}'")

        _check_level(location_id, "danger_level", location.get("danger_level"), result)
        _check_level(location_id, "qi_density", location.get("qi_density"), result)
        _check_map_position(location_id, location.get("map_position"), result)

        for system in location.get("available_systems", []):
            if system not in AVAILABLE_SYSTEMS:
                result.add(
                    "dead_available_system",
                    f"location '{location_id}' declares unimplemented system '{system}'",
                )

        requirements = location.get("requirements", {})
        for track in ("body_transformation", "essence_gathering"):
            if track not in requirements:
                result.add("missing_requirement", f"location '{location_id}' requirements missing '{track}'")


def _check_level(location_id: Any, field_name: str, value: Any, result: ValidationResult) -> None:
    if value is None:
        return
    if not isinstance(value, (int, float)) or not 0 <= value <= 10:
        result.add("bad_level", f"location '{location_id}' {field_name} must be 0-10, got {value!r}")


def _check_map_position(location_id: Any, value: Any, result: ValidationResult) -> None:
    if not isinstance(value, dict):
        result.add("bad_map_position", f"location '{location_id}' map_position must be an object with x/y values")
        return
    for axis in ("x", "y"):
        coordinate = value.get(axis)
        if not isinstance(coordinate, (int, float)) or isinstance(coordinate, bool) or not 0 <= coordinate <= 1:
            result.add("bad_map_position", f"location '{location_id}' map_position.{axis} must be between 0 and 1")


# -- encounter pools -----------------------------------------------------
def _validate_map_positions(registry: GameDataRegistry, result: ValidationResult) -> None:
    """Flag locations whose map markers sit exactly on top of another's."""
    seen: Dict[str, str] = {}
    for location in registry.locations:
        position = location.get("map_position")
        if not isinstance(position, dict):
            continue
        key = (round(float(position.get("x", 0)), 3), round(float(position.get("y", 0)), 3))
        if key in seen:
            result.add(
                "duplicate_map_position",
                f"locations '{seen[key]}' and '{location.get('id')}' share map position {key}",
            )
        else:
            seen[key] = location.get("id")


def _validate_enemy_abilities(registry: GameDataRegistry, result: ValidationResult) -> None:
    """Check enemy ``abilities`` entries are well-formed."""
    valid_types = {"heavy", "poison", "stun"}
    for collection_name, enemies in (
        ("enemy", registry.enemies),
        ("character_enemy", registry.character_enemies),
    ):
        for enemy in enemies:
            abilities = enemy.get("abilities", [])
            if not isinstance(abilities, list):
                result.add("bad_enemy_ability", f"{collection_name} '{enemy.get('id')}' abilities must be a list")
                continue
            for ability in abilities:
                if not isinstance(ability, dict):
                    result.add("bad_enemy_ability", f"{collection_name} '{enemy.get('id')}' has a non-object ability")
                    continue
                if ability.get("type") not in valid_types:
                    result.add("bad_enemy_ability", f"{collection_name} '{enemy.get('id')}' has unknown ability type '{ability.get('type')}'")
                chance = ability.get("chance")
                if not isinstance(chance, (int, float)) or isinstance(chance, bool) or not 0 <= chance <= 1:
                    result.add("bad_enemy_ability", f"{collection_name} '{enemy.get('id')}' ability chance must be between 0 and 1")


def _validate_encounter_pools(registry: GameDataRegistry, result: ValidationResult) -> None:
    if not registry.encounter_pools:
        return
    location_ids = _id_set(registry.locations)
    enemy_ids = _id_set(registry.enemies)
    item_ids = _id_set(registry.items) | _id_set(registry.equipment) | registry.manual_item_ids()
    special_ids = {special.get("id") for special in registry.events.get("special_events", [])}

    for location_id, pool in registry.encounter_pools.items():
        if location_id not in location_ids:
            result.add("bad_pool_location", f"encounter pool for unknown location '{location_id}'")
        for entry in pool.get("combat", []):
            if entry.get("enemy_id") not in enemy_ids:
                result.add(
                    "bad_enemy_ref",
                    f"encounter pool '{location_id}' combat references missing enemy '{entry.get('enemy_id')}'",
                )
        for entry in pool.get("loot", []):
            if entry.get("item_id") not in item_ids:
                result.add(
                    "bad_item_ref",
                    f"encounter pool '{location_id}' loot references missing item '{entry.get('item_id')}'",
                )
        for entry in pool.get("special", []):
            if entry.get("special_id") not in special_ids:
                result.add(
                    "bad_special_ref",
                    f"encounter pool '{location_id}' special references missing special '{entry.get('special_id')}'",
                )


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
    multipliers = config.get("daily_cultivation_multipliers")
    if not isinstance(multipliers, list) or not multipliers:
        result.add("bad_cultivation_config", "body_progression.daily_cultivation_multipliers must be a non-empty list")
        return
    for multiplier in multipliers:
        if not isinstance(multiplier, (int, float)) or multiplier <= 0 or multiplier > 1:
            result.add("bad_cultivation_config", "body_progression.daily_cultivation_multipliers values must be > 0 and <= 1")
            return


def _validate_essence_progression_config(config: Dict[str, Any], result: ValidationResult) -> None:
    for field_name in ("max_strain_for_breakthrough", "required_foundation_stability"):
        value = config.get(field_name)
        if not isinstance(value, (int, float)) or not 0 <= value <= 100:
            result.add("bad_cultivation_config", f"essence_progression.{field_name} must be between 0 and 100")
    for field_name in ("training_strain_gain", "failed_breakthrough_strain_gain", "failed_breakthrough_foundation_loss"):
        value = config.get(field_name)
        if not isinstance(value, (int, float)) or value < 0:
            result.add("bad_cultivation_config", f"essence_progression.{field_name} must be a non-negative number")


# -- talent tracks ------------------------------------------------------
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


# -- equipment ----------------------------------------------------------
def _validate_equipment_data(registry: GameDataRegistry, result: ValidationResult) -> None:
    valid_slots = {"weapon", "armor", "boots", "cloak", "ring_1", "ring_2", "amulet", "talisman", "artifact_1", "artifact_2", "flying_sword"}
    valid_categories = {"martial_weapon", "robe", "light_armor", "heavy_armor", "boots", "cloak", "ring", "amulet", "talisman", "artifact", "flying_sword", "cultivation_aid", "body_tempering_tool", "utility_tool", "sect_token"}
    # Canonical rarity ladder (low -> high), matching events.json find_config.rarity_order.
    valid_rarities = {"mortal_grade", "low_spirit_grade", "middle_spirit_grade", "high_spirit_grade", "earth_grade", "heaven_grade", "dao_grade"}
    stat_keys = {"strength", "body_strength", "attack", "defense", "max_hp", "max_qi", "speed", "evasion", "comprehension"}
    cultivation_keys = {"body_cultivation_flat_bonus", "essence_cultivation_flat_bonus", "body_strain_gain_multiplier", "qi_strain_gain_multiplier", "foundation_stability_bonus", "breakthrough_chance_modifier", "body_breakthrough_modifier", "essence_breakthrough_modifier", "comprehension_bonus"}
    utility_keys = {"travel_safety_bonus", "herb_gathering_bonus", "rare_event_chance_bonus", "shop_discount_modifier", "spirit_stone_find_bonus", "stealth_bonus", "ambush_avoidance_bonus", "corpse_qi_resistance", "weather_resistance"}
    body_ids = {realm.get("id") for realm in registry.body_realms.get("realms", [])}
    essence_ids = {realm.get("id") for realm in registry.essence_realms.get("realms", [])}
    seen: Set[str] = set()
    for item in registry.equipment:
        item_id = item.get("id")
        if not isinstance(item_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", item_id):
            result.add("bad_equipment", f"equipment id '{item_id}' must be stable snake_case")
            continue
        if item_id in seen:
            result.add("duplicate_id", f"equipment: duplicate id '{item_id}'")
        seen.add(item_id)
        if not item.get("display_name"):
            result.add("bad_equipment", f"equipment '{item_id}' display_name is required")
        if item.get("rarity") not in valid_rarities:
            result.add("bad_equipment", f"equipment '{item_id}' rarity is invalid")
        category = item.get("category")
        if category not in valid_categories:
            result.add("bad_equipment", f"equipment '{item_id}' category is invalid")
        slots = item.get("valid_slots")
        if not isinstance(slots, list) or not slots or any(slot not in valid_slots for slot in slots):
            result.add("bad_equipment", f"equipment '{item_id}' valid_slots must contain valid slots")
        elif category == "ring" and not set(slots) <= {"ring_1", "ring_2"}:
            result.add("bad_equipment", f"equipment '{item_id}' ring must use ring slots")
        elif category == "artifact" and not set(slots) <= {"artifact_1", "artifact_2"}:
            result.add("bad_equipment", f"equipment '{item_id}' artifact must use artifact slots")
        elif category == "flying_sword" and slots != ["flying_sword"]:
            result.add("bad_equipment", f"equipment '{item_id}' flying_sword must use flying_sword slot")
        if item.get("equippable") is not True:
            result.add("bad_equipment", f"equipment '{item_id}' must be equippable")
        if item.get("stackable") is not False:
            result.add("bad_equipment", f"equipment '{item_id}' must not be stackable")
        if not isinstance(item.get("value", 0), (int, float)) or item.get("value", 0) < 0:
            result.add("bad_equipment", f"equipment '{item_id}' value must be non-negative")
        _validate_modifier_group(item_id, "stat_modifiers", item.get("stat_modifiers", {}), stat_keys, result)
        _validate_modifier_group(item_id, "cultivation_modifiers", item.get("cultivation_modifiers", {}), cultivation_keys, result)
        _validate_modifier_group(item_id, "utility_modifiers", item.get("utility_modifiers", {}), utility_keys, result)
        set_id = item.get("set_id")
        if set_id is not None and (not isinstance(set_id, str) or not set_id):
            result.add("bad_equipment", f"equipment '{item_id}' set_id must be a non-empty string")
        for bonus in item.get("set_bonuses", []) or []:
            if not isinstance(bonus, dict) or not isinstance(bonus.get("pieces_required"), int) or isinstance(bonus.get("pieces_required"), bool) or bonus["pieces_required"] <= 0:
                result.add("bad_equipment", f"equipment '{item_id}' set bonus pieces_required must be a positive integer")
                continue
            for group in ("stat_modifiers", "cultivation_modifiers", "utility_modifiers"):
                if group in bonus and not isinstance(bonus[group], dict):
                    result.add("bad_equipment", f"equipment '{item_id}' set bonus {group} must be an object")
        durability = item.get("durability")
        if durability is not None and (not isinstance(durability, int) or isinstance(durability, bool) or durability <= 0):
            result.add("bad_equipment", f"equipment '{item_id}' durability must be a positive integer")
        requirements = item.get("requirements", {}) or {}
        if requirements.get("minimum_body_realm") and requirements["minimum_body_realm"] not in body_ids:
            result.add("bad_equipment", f"equipment '{item_id}' minimum_body_realm is unknown")
        if requirements.get("minimum_essence_realm") and requirements["minimum_essence_realm"] not in essence_ids:
            result.add("bad_equipment", f"equipment '{item_id}' minimum_essence_realm is unknown")


# -- shops ---------------------------------------------------------------
def _validate_shop_data(registry: GameDataRegistry, result: ValidationResult) -> None:
    location_ids = _id_set(registry.locations)
    item_ids = _id_set(registry.items) | _id_set(registry.equipment) | registry.manual_item_ids()
    supported_currencies = {"gold", "spirit_stone"}
    seen: Set[str] = set()
    for shop in registry.shops:
        shop_id = shop.get("id")
        if not isinstance(shop_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", shop_id):
            result.add("bad_shop", f"shop id '{shop_id}' must be stable snake_case")
            continue
        if shop_id in seen:
            result.add("duplicate_id", f"shop: duplicate id '{shop_id}'")
        seen.add(shop_id)
        if not isinstance(shop.get("display_name"), str) or not shop.get("display_name"):
            result.add("bad_shop", f"shop '{shop_id}' display_name is required")
        locations = shop.get("location_ids")
        if not isinstance(locations, list) or not locations:
            result.add("bad_shop", f"shop '{shop_id}' location_ids must be a non-empty list")
        else:
            for location_id in locations:
                if location_id not in location_ids:
                    result.add("bad_shop", f"shop '{shop_id}' references missing location '{location_id}'")
        stock = shop.get("stock")
        if not isinstance(stock, list) or not stock:
            result.add("bad_shop", f"shop '{shop_id}' stock must be a non-empty list")
            continue
        seen_stock_items: Set[str] = set()
        for entry in stock:
            item_id = entry.get("item_id") if isinstance(entry, dict) else None
            if item_id not in item_ids:
                result.add("bad_shop", f"shop '{shop_id}' stock references missing item '{item_id}'")
            if item_id in seen_stock_items:
                result.add("bad_shop", f"shop '{shop_id}' lists item '{item_id}' more than once")
            if isinstance(item_id, str):
                seen_stock_items.add(item_id)
            price = entry.get("price") if isinstance(entry, dict) else None
            if not isinstance(price, dict) or not price:
                result.add("bad_shop", f"shop '{shop_id}' item '{item_id}' price must be a non-empty object")
            else:
                for currency, amount in price.items():
                    if currency not in supported_currencies:
                        result.add("bad_shop", f"shop '{shop_id}' item '{item_id}' has unsupported currency '{currency}'")
                    if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
                        result.add("bad_shop", f"shop '{shop_id}' item '{item_id}' price.{currency} must be a positive integer")
            stock_limit = entry.get("stock") if isinstance(entry, dict) else None
            if stock_limit is not None and (not isinstance(stock_limit, int) or isinstance(stock_limit, bool) or stock_limit <= 0):
                result.add("bad_shop", f"shop '{shop_id}' item '{item_id}' stock must be a positive integer when present")


def _validate_trainers(registry: GameDataRegistry, result: ValidationResult) -> None:
    location_ids = _id_set(registry.locations)
    skill_ids = _id_set(registry.skills)
    sect_paths = {sect.get("path") for sect in registry.sects if sect.get("path")}
    supported_currencies = {"gold", "spirit_stone"}
    seen: Set[str] = set()
    for trainer in registry.trainers:
        trainer_id = trainer.get("id")
        if not isinstance(trainer_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", trainer_id):
            result.add("bad_trainer", f"trainer id '{trainer_id}' must be stable snake_case")
            continue
        if trainer_id in seen:
            result.add("duplicate_id", f"trainer: duplicate id '{trainer_id}'")
        seen.add(trainer_id)
        if not isinstance(trainer.get("display_name"), str) or not trainer.get("display_name"):
            result.add("bad_trainer", f"trainer '{trainer_id}' display_name is required")
        locations = trainer.get("location_ids")
        if not isinstance(locations, list) or not locations:
            result.add("bad_trainer", f"trainer '{trainer_id}' location_ids must be a non-empty list")
        else:
            for location_id in locations:
                if location_id not in location_ids:
                    result.add("bad_trainer", f"trainer '{trainer_id}' references missing location '{location_id}'")
        techniques = trainer.get("techniques")
        if not isinstance(techniques, list) or not techniques:
            result.add("bad_trainer", f"trainer '{trainer_id}' techniques must be a non-empty list")
            continue
        seen_skills: Set[str] = set()
        for entry in techniques:
            skill_id = entry.get("skill_id") if isinstance(entry, dict) else None
            if skill_id not in skill_ids:
                result.add("bad_trainer", f"trainer '{trainer_id}' offers missing skill '{skill_id}'")
            if skill_id in seen_skills:
                result.add("bad_trainer", f"trainer '{trainer_id}' lists skill '{skill_id}' more than once")
            if isinstance(skill_id, str):
                seen_skills.add(skill_id)
            price = entry.get("price") if isinstance(entry, dict) else None
            if not isinstance(price, dict) or not price:
                result.add("bad_trainer", f"trainer '{trainer_id}' skill '{skill_id}' price must be a non-empty object")
            else:
                for currency, amount in price.items():
                    if currency not in supported_currencies:
                        result.add("bad_trainer", f"trainer '{trainer_id}' skill '{skill_id}' has unsupported currency '{currency}'")
                    if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
                        result.add("bad_trainer", f"trainer '{trainer_id}' skill '{skill_id}' price.{currency} must be a positive integer")
            required_path = entry.get("required_path") if isinstance(entry, dict) else None
            if required_path and required_path not in sect_paths:
                result.add("bad_trainer", f"trainer '{trainer_id}' skill '{skill_id}' required_path '{required_path}' is not a known sect path")


def _validate_sects(registry: GameDataRegistry, result: ValidationResult) -> None:
    location_ids = _id_set(registry.locations)
    body_ids = {realm.get("id") for realm in registry.body_realms.get("realms", [])}
    seen: Set[str] = set()
    seen_paths: Set[str] = set()
    for sect in registry.sects:
        sect_id = sect.get("id")
        if not isinstance(sect_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", sect_id):
            result.add("bad_sect", f"sect id '{sect_id}' must be stable snake_case")
            continue
        if sect_id in seen:
            result.add("duplicate_id", f"sect: duplicate id '{sect_id}'")
        seen.add(sect_id)
        if not isinstance(sect.get("display_name"), str) or not sect.get("display_name"):
            result.add("bad_sect", f"sect '{sect_id}' display_name is required")
        path = sect.get("path")
        if not isinstance(path, str) or not path:
            result.add("bad_sect", f"sect '{sect_id}' path is required")
        elif path in seen_paths:
            result.add("bad_sect", f"sect '{sect_id}' path '{path}' duplicates another sect's path")
        if isinstance(path, str):
            seen_paths.add(path)
        locations = sect.get("location_ids")
        if not isinstance(locations, list) or not locations:
            result.add("bad_sect", f"sect '{sect_id}' location_ids must be a non-empty list")
        else:
            for location_id in locations:
                if location_id not in location_ids:
                    result.add("bad_sect", f"sect '{sect_id}' references missing location '{location_id}'")
        requirements = sect.get("join_requirements", {}) or {}
        min_realm = requirements.get("min_body_realm")
        if min_realm is not None and min_realm not in body_ids:
            result.add("bad_sect", f"sect '{sect_id}' min_body_realm '{min_realm}' is not a known body realm")
        for field in ("min_reputation", "max_reputation"):
            value = requirements.get(field)
            if value is not None and (not isinstance(value, int) or isinstance(value, bool)):
                result.add("bad_sect", f"sect '{sect_id}' {field} must be an integer")
        ranks = sect.get("contribution_ranks")
        if not isinstance(ranks, list) or not ranks or not all(isinstance(rank, str) and rank for rank in ranks):
            result.add("bad_sect", f"sect '{sect_id}' contribution_ranks must be a non-empty list of names")


def _validate_daos(registry: GameDataRegistry, result: ValidationResult) -> None:
    dao_ids = {dao.get("id") for dao in registry.daos if isinstance(dao, dict) and dao.get("id")}
    elements = {"metal", "wood", "water", "fire", "earth"}
    seen: Set[str] = set()
    for dao in registry.daos:
        if not isinstance(dao, dict):
            result.add("bad_dao", "dao entry must be an object")
            continue
        dao_id = dao.get("id")
        if not isinstance(dao_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", dao_id):
            result.add("bad_dao", f"dao id '{dao_id}' must be stable snake_case")
            continue
        if dao_id in seen:
            result.add("duplicate_id", f"dao: duplicate id '{dao_id}'")
        seen.add(dao_id)
        if not isinstance(dao.get("display_name"), str) or not dao.get("display_name"):
            result.add("bad_dao", f"dao '{dao_id}' display_name is required")
        affinities = dao.get("affinities")
        if not isinstance(affinities, list) or not all(isinstance(a, str) for a in affinities):
            result.add("bad_dao", f"dao '{dao_id}' affinities must be a list of strings")
        else:
            for affinity in affinities:
                if affinity not in elements:
                    result.add("bad_dao", f"dao '{dao_id}' has unknown affinity '{affinity}'")
        for field in ("counters", "countered_by"):
            value = dao.get(field, [])
            if not isinstance(value, list):
                result.add("bad_dao", f"dao '{dao_id}' {field} must be a list")
                continue
            for target in value:
                if target not in dao_ids:
                    result.add("bad_dao", f"dao '{dao_id}' {field} references missing dao '{target}'")
                elif target == dao_id:
                    result.add("bad_dao", f"dao '{dao_id}' cannot {field} itself")
    # Symmetry: A counters B <-> B lists A in countered_by (and vice versa).
    by_id = {dao["id"]: dao for dao in registry.daos if isinstance(dao, dict) and dao.get("id")}
    for dao in registry.daos:
        if not isinstance(dao, dict):
            continue
        dao_id = dao.get("id")
        for target in dao.get("counters", []):
            target_entry = by_id.get(target)
            if target_entry is not None and dao_id not in target_entry.get("countered_by", []):
                result.add("bad_dao", f"dao '{dao_id}' counters '{target}' but '{target}' does not list it in countered_by")
        for source in dao.get("countered_by", []):
            source_entry = by_id.get(source)
            if source_entry is not None and dao_id not in source_entry.get("counters", []):
                result.add("bad_dao", f"dao '{dao_id}' lists '{source}' in countered_by but '{source}' does not counter it")
    # Enemy dao references must resolve to a known dao.
    for collection in (registry.enemies, registry.character_enemies):
        for enemy in collection:
            dao_id = enemy.get("dao_id")
            if dao_id is not None and dao_id not in dao_ids:
                result.add("bad_dao", f"enemy '{enemy.get('id')}' references missing dao '{dao_id}'")


def _validate_skills(registry: GameDataRegistry, result: ValidationResult) -> None:
    for skill in registry.skills:
        if not isinstance(skill, dict):
            continue
        skill_id = skill.get("id", "?")
        insight_required = skill.get("insight_required", 0)
        if isinstance(insight_required, bool) or not isinstance(insight_required, int) or insight_required < 0:
            result.add("bad_skill", f"skill '{skill_id}' insight_required must be a non-negative integer")
        elif insight_required > 0 and skill.get("type") != "active":
            result.add("bad_skill", f"skill '{skill_id}' insight_required is only meaningful on active skills")


# Core verbs every narrative catalogue must cover with at least three weighted
# variants (ROADMAP A.1).
_NARRATIVE_CORE_VERBS = (
    "train_body",
    "train_essence",
    "rest",
    "meditate",
    "explore_nothing",
    "explore_combat",
    "explore_loot",
    "explore_special",
    "travel",
    "attack",
    "breakthrough_success",
    "breakthrough_failure",
    "death",
)
_NARRATIVE_OPS = ("gte", "lte", "gt", "lt", "eq", "ne")
_SLOT_RE = re.compile(r"\{([a-z_][a-z0-9_]*)\}")


def _validate_narrative_templates(registry: GameDataRegistry, result: ValidationResult) -> None:
    templates = registry.narrative_templates
    if not isinstance(templates, dict):
        result.add("bad_narrative", "narrative_templates must be an object mapping verbs to variants")
        return
    for verb, entry in templates.items():
        if not isinstance(entry, dict):
            result.add("bad_narrative", f"narrative verb '{verb}' must be an object")
            continue
        variants = entry.get("variants")
        if not isinstance(variants, list) or not variants:
            result.add("bad_narrative", f"narrative verb '{verb}' must declare a non-empty 'variants' list")
            continue
        declared = entry.get("variables", [])
        if not isinstance(declared, list) or not all(isinstance(name, str) and name for name in declared):
            result.add("bad_narrative", f"narrative verb '{verb}' 'variables' must be a list of strings")
            declared = []
        declared_set = set(declared)
        for variant in variants:
            if not isinstance(variant, dict):
                result.add("bad_narrative", f"narrative verb '{verb}' has a non-object variant")
                continue
            template = variant.get("template")
            if not isinstance(template, str) or not template:
                result.add("bad_narrative", f"narrative verb '{verb}' has a variant missing a 'template' string")
            weight = variant.get("weight", 1)
            if isinstance(weight, bool) or not isinstance(weight, (int, float)) or weight < 0:
                result.add("bad_narrative", f"narrative verb '{verb}' has a variant with a non-numeric 'weight'")
            if declared_set:
                for slot in _SLOT_RE.findall(str(template)):
                    if slot not in declared_set:
                        result.add("bad_narrative", f"narrative verb '{verb}' uses undeclared slot '{{{slot}}}'")
            when = variant.get("when")
            if when is not None:
                predicates = when if isinstance(when, list) else [when]
                for predicate in predicates:
                    if not isinstance(predicate, dict):
                        result.add("bad_narrative", f"narrative verb '{verb}' has a non-object when-predicate")
                        continue
                    if not isinstance(predicate.get("field"), str) or not predicate.get("field"):
                        result.add("bad_narrative", f"narrative verb '{verb}' when-predicate is missing a 'field'")
                    if predicate.get("op", "eq") not in _NARRATIVE_OPS:
                        result.add("bad_narrative", f"narrative verb '{verb}' has an unknown op '{predicate.get('op')}'")
                    if "value" not in predicate:
                        result.add("bad_narrative", f"narrative verb '{verb}' when-predicate is missing a 'value'")
    for verb in _NARRATIVE_CORE_VERBS:
        entry = templates.get(verb)
        count = (
            len(entry.get("variants", []))
            if isinstance(entry, dict) and isinstance(entry.get("variants"), list)
            else 0
        )
        if count < 3:
            result.add("bad_narrative", f"core narrative verb '{verb}' must have >= 3 weighted variants (has {count})")


def _validate_origins(registry: GameDataRegistry, result: ValidationResult) -> None:
    dao_ids = {dao.get("id") for dao in registry.daos if isinstance(dao, dict) and dao.get("id")}
    skill_ids = _id_set(registry.skills)
    seen: Set[str] = set()
    for origin in registry.origins:
        if not isinstance(origin, dict):
            result.add("bad_origin", "origin entry must be an object")
            continue
        origin_id = origin.get("id")
        if not isinstance(origin_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", origin_id):
            result.add("bad_origin", f"origin id '{origin_id}' must be stable snake_case")
            continue
        if origin_id in seen:
            result.add("duplicate_id", f"origin: duplicate id '{origin_id}'")
        seen.add(origin_id)
        if not isinstance(origin.get("display_name"), str) or not origin.get("display_name"):
            result.add("bad_origin", f"origin '{origin_id}' display_name is required")
        cost = origin.get("cost", 0)
        if isinstance(cost, bool) or not isinstance(cost, int) or cost < 0:
            result.add("bad_origin", f"origin '{origin_id}' cost must be a non-negative integer")
        dao_id = origin.get("dao_id")
        if dao_id is not None and dao_id not in dao_ids:
            result.add("bad_origin", f"origin '{origin_id}' references missing dao '{dao_id}'")
        skills = origin.get("starting_skills")
        if not isinstance(skills, list):
            result.add("bad_origin", f"origin '{origin_id}' starting_skills must be a list")
        else:
            for skill_id in skills:
                if skill_id not in skill_ids:
                    result.add("bad_origin", f"origin '{origin_id}' references missing skill '{skill_id}'")
        modifiers = origin.get("stat_modifiers", {})
        if not isinstance(modifiers, dict):
            result.add("bad_origin", f"origin '{origin_id}' stat_modifiers must be an object")
        else:
            for field, delta in modifiers.items():
                if field not in STAT_FIELDS:
                    result.add("bad_origin", f"origin '{origin_id}' has unknown stat modifier '{field}'")
                if isinstance(delta, bool) or not isinstance(delta, int):
                    result.add("bad_origin", f"origin '{origin_id}' stat modifier '{field}' must be an integer")
    if not any(int(entry.get("cost", 0)) == 0 for entry in registry.origins if isinstance(entry, dict)):
        result.add("bad_origin", "at least one origin must be free (cost 0)")


def _validate_gathering(registry: GameDataRegistry, result: ValidationResult) -> None:
    item_ids = _id_set(registry.items) | _id_set(registry.equipment) | registry.manual_item_ids()
    location_ids = _id_set(registry.locations)
    gathering = registry.gathering or {}
    for label, table in [("default", gathering.get("default", []))] + [
        (str(location_id), entries) for location_id, entries in (gathering.get("locations") or {}).items()
    ]:
        if not isinstance(table, list) or not table:
            result.add("bad_gathering", f"gathering '{label}' must be a non-empty list")
            continue
        for entry in table:
            if not isinstance(entry, dict) or not entry.get("item_id"):
                result.add("bad_gathering", f"gathering '{label}' has a malformed entry")
                continue
            if entry.get("item_id") not in item_ids:
                result.add("bad_gathering", f"gathering '{label}' references missing item '{entry.get('item_id')}'")
            weight = entry.get("weight", 1)
            if isinstance(weight, bool) or not isinstance(weight, (int, float)) or weight <= 0:
                result.add("bad_gathering", f"gathering '{label}' has an invalid weight")
    for location_id in (gathering.get("locations") or {}):
        if location_id not in location_ids:
            result.add("bad_gathering", f"gathering references missing location '{location_id}'")


def _validate_refining_recipes(registry: GameDataRegistry, result: ValidationResult) -> None:
    item_ids = _id_set(registry.items) | _id_set(registry.equipment) | registry.manual_item_ids()
    body_ids = {realm.get("id") for realm in registry.body_realms.get("realms", [])}
    essence_ids = {realm.get("id") for realm in registry.essence_realms.get("realms", [])}
    seen: Set[str] = set()
    for recipe in registry.refining_recipes:
        if not isinstance(recipe, dict):
            result.add("bad_recipe", "recipe entry must be an object")
            continue
        recipe_id = recipe.get("id")
        if not isinstance(recipe_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", recipe_id):
            result.add("bad_recipe", f"recipe id '{recipe_id}' must be stable snake_case")
            continue
        if recipe_id in seen:
            result.add("duplicate_id", f"recipe: duplicate id '{recipe_id}'")
        seen.add(recipe_id)
        inputs = recipe.get("inputs", {})
        if not isinstance(inputs, dict) or not inputs:
            result.add("bad_recipe", f"recipe '{recipe_id}' inputs must be a non-empty object")
        else:
            for item_id, quantity in inputs.items():
                if item_id not in item_ids:
                    result.add("bad_recipe", f"recipe '{recipe_id}' input references missing item '{item_id}'")
                if isinstance(quantity, bool) or not isinstance(quantity, int) or quantity <= 0:
                    result.add("bad_recipe", f"recipe '{recipe_id}' input '{item_id}' must be a positive integer")
        output = recipe.get("output", {})
        if not isinstance(output, dict) or not output.get("item_id") or output.get("item_id") not in item_ids:
            result.add("bad_recipe", f"recipe '{recipe_id}' output references a missing/absent item")
        elif isinstance(output.get("count"), bool) or not isinstance(output.get("count", 1), int) or int(output.get("count", 1)) <= 0:
            result.add("bad_recipe", f"recipe '{recipe_id}' output count must be a positive integer")
        body_realm = recipe.get("minimum_body_realm")
        if body_realm and body_realm not in body_ids:
            result.add("bad_recipe", f"recipe '{recipe_id}' minimum_body_realm is unknown")
        essence_realm = recipe.get("minimum_essence_realm")
        if essence_realm and essence_realm not in essence_ids:
            result.add("bad_recipe", f"recipe '{recipe_id}' minimum_essence_realm is unknown")


def _validate_secret_realm(registry: GameDataRegistry, result: ValidationResult) -> None:
    realms = registry.secret_realm or []
    if not realms:
        return
    location_ids = _id_set(registry.locations)
    random_enemy_ids = _id_set(registry.enemies)
    named_enemy_ids = _id_set(registry.character_enemies)
    item_ids = _id_set(registry.items) | _id_set(registry.equipment) | registry.manual_item_ids()
    seen: Set[str] = set()
    for realm in realms:
        if not isinstance(realm, dict):
            result.add("bad_realm", "secret_realm entry must be an object")
            continue
        realm_id = realm.get("id")
        if not isinstance(realm_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", realm_id):
            result.add("bad_realm", f"secret_realm id '{realm_id}' must be stable snake_case")
            continue
        if realm_id in seen:
            result.add("duplicate_id", f"secret_realm: duplicate id '{realm_id}'")
        seen.add(realm_id)
        location_id = realm.get("location_id")
        if location_id not in location_ids:
            result.add("bad_realm", f"secret_realm '{realm_id}' references missing location '{location_id}'")
        room_count = realm.get("room_count", 0)
        if isinstance(room_count, bool) or not isinstance(room_count, int) or room_count < 1:
            result.add("bad_realm", f"secret_realm '{realm_id}' room_count must be a positive integer")
        for enemy_id in realm.get("enemy_pool", []):
            if enemy_id not in random_enemy_ids:
                result.add("bad_realm", f"secret_realm '{realm_id}' enemy_pool references missing enemy '{enemy_id}'")
        boss_id = realm.get("boss_id")
        if boss_id and boss_id not in named_enemy_ids:
            result.add("bad_realm", f"secret_realm '{realm_id}' boss '{boss_id}' must be a named foe")
        for entry in realm.get("treasure_pool", []):
            if not isinstance(entry, dict) or entry.get("item_id") not in item_ids:
                result.add("bad_realm", f"secret_realm '{realm_id}' treasure_pool references a missing item")
        for item_id in realm.get("final_reward", {}).get("items", {}):
            if item_id not in item_ids:
                result.add("bad_realm", f"secret_realm '{realm_id}' final_reward references missing item '{item_id}'")


def _validate_technique_manuals(registry: GameDataRegistry, result: ValidationResult) -> None:
    skill_ids = _id_set(registry.skills)
    for override in registry.technique_manuals:
        skill_id = override.get("skill_id") if isinstance(override, dict) else None
        if not skill_id:
            result.add("bad_manual", "technique manual override is missing 'skill_id'")
        elif skill_id not in skill_ids:
            result.add("bad_manual", f"technique manual override references missing skill '{skill_id}'")


def _validate_quests(registry: GameDataRegistry, result: ValidationResult) -> None:
    quest_ids = _id_set(registry.quests)
    skill_ids = _id_set(registry.skills)
    manual_ids = registry.manual_item_ids()
    location_ids = _id_set(registry.locations)
    for quest in registry.quests:
        quest_id = quest.get("id")
        requires = quest.get("requires", {}) or {}
        for completed_id in requires.get("completed", []):
            if completed_id not in quest_ids:
                result.add("bad_quest_ref", f"quest '{quest_id}' requires missing quest '{completed_id}'")
            elif completed_id == quest_id:
                result.add("bad_quest_ref", f"quest '{quest_id}' cannot require itself")
        location = requires.get("location")
        if location and location not in location_ids:
            result.add("bad_quest_ref", f"quest '{quest_id}' requires missing location '{location}'")
        for skill_id in quest.get("rewards", {}).get("skills", []):
            if skill_id not in skill_ids:
                result.add("bad_quest_ref", f"quest '{quest_id}' rewards missing skill '{skill_id}'")
        for manual_id in quest.get("rewards", {}).get("manuals", {}):
            if manual_id not in manual_ids:
                result.add("bad_quest_ref", f"quest '{quest_id}' rewards missing manual '{manual_id}'")


def _validate_find_config(registry: GameDataRegistry, result: ValidationResult) -> None:
    config = (registry.events or {}).get("find_config")
    if not config:
        return
    rarity_order = config.get("rarity_order")
    if not isinstance(rarity_order, list) or not rarity_order:
        result.add("bad_find_config", "find_config.rarity_order must be a non-empty list")
        return
    order_set = set(rarity_order)
    for rarity in config.get("rarity_weights", {}):
        if rarity not in order_set:
            result.add("bad_find_config", f"find_config.rarity_weights has unknown rarity '{rarity}'")
    default_rarity = config.get("default_item_rarity")
    if default_rarity is not None and default_rarity not in order_set:
        result.add("bad_find_config", f"find_config.default_item_rarity '{default_rarity}' is not in rarity_order")
    max_index = len(rarity_order) - 1
    for danger, index in config.get("danger_max_rarity_index", {}).items():
        if not isinstance(index, int) or isinstance(index, bool) or not 0 <= index <= max_index:
            result.add("bad_find_config", f"find_config.danger_max_rarity_index['{danger}'] must be between 0 and {max_index}")


def _validate_modifier_group(item_id: str, group_name: str, modifiers: Any, valid_keys: Set[str], result: ValidationResult) -> None:
    if not isinstance(modifiers, dict):
        result.add("bad_equipment", f"equipment '{item_id}' {group_name} must be an object")
        return
    for key, value in modifiers.items():
        if key not in valid_keys:
            result.add("bad_equipment", f"equipment '{item_id}' has unsupported {group_name}.{key}")
        if not isinstance(value, (int, float)):
            result.add("bad_equipment", f"equipment '{item_id}' {group_name}.{key} must be numeric")
        if key.endswith("_multiplier") and isinstance(value, (int, float)) and value <= 0:
            result.add("bad_equipment", f"equipment '{item_id}' {group_name}.{key} must be positive")


# -- helpers -------------------------------------------------------------
def _id_set(entries: Iterable[Dict[str, Any]]) -> Set[str]:
    return {entry["id"] for entry in entries if "id" in entry}


def _connections(location: Dict[str, Any]) -> List[str]:
    for key in ("connected_locations", "connections"):
        if key in location:
            return list(location.get(key) or [])
    return []
