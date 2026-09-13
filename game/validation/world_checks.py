"""Collection validators for locations, the map, and the encounter layer.

Split out of ``data_validator`` (V.5) so the world/exploration lane owns its own
file. Called by :func:`game.validation.data_validator.validate_all_game_data`;
every function keeps the signature and verdict it had before the split.

This module reads data only; it never mutates the registry or touches gameplay.
"""
from __future__ import annotations

from typing import Any, Dict, List, Set

from game.core.constants import AVAILABLE_SYSTEMS
from game.data.registry import GameDataRegistry
from game.validation.support import _id_set
from game.validation.validation_error import ValidationResult


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
        story_tier = location.get("story_tier")
        if story_tier is not None and (not isinstance(story_tier, int) or isinstance(story_tier, bool) or not 1 <= story_tier <= 6):
            result.add("bad_location", f"location '{location_id}' story_tier must be an integer between 1 and 6")
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

        # A minimum_realm the travel service cannot resolve is a gate that never
        # fires (``TravelService._realm_ok`` fails open on unknown values), so the
        # endgame location would quietly be walk-in accessible.
        for track, realms, label in (
            ("body_transformation", registry.body_realms, "body"),
            ("essence_gathering", registry.essence_realms, "essence"),
        ):
            minimum = (requirements.get(track) or {}).get("minimum_realm")
            if minimum is None or str(minimum).strip().lower() in _realm_keys(realms):
                continue
            result.add(
                "dead_travel_gate",
                f"location '{location_id}' {track} minimum_realm '{minimum}' is not a known "
                f"{label} realm id or name, so travel is never gated by it",
            )


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
    # Location-scoped hazards name a hazard from the choice-driven encounter data.
    hazard_ids = {hazard.get("id") for hazard in (registry.encounters.get("hazards") or [])}

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
        for entry in pool.get("hazards", []):
            if entry.get("hazard_id") not in hazard_ids:
                result.add(
                    "bad_hazard_ref",
                    f"encounter pool '{location_id}' hazard references missing hazard '{entry.get('hazard_id')}'",
                )


def _validate_encounters(registry: GameDataRegistry, result: ValidationResult) -> None:
    """Validate ``data/encounters.json`` (the choice-driven encounter layer).

    The expensive mistakes here are silent: a hazard whose "people" list names
    an enemy that no longer exists simply never applies, and a chance outside
    0-1 makes a choice always-or-never. Both are caught here.
    """
    data = registry.encounters
    if not data:
        return

    for choice_id, option in (data.get("options") or {}).items():
        if not isinstance(option, dict) or not option.get("label") or not option.get("hint"):
            result.add("bad_encounter_option", f"encounter option '{choice_id}' needs a label and a hint")

    for section, limits in (
        ("parley", ("base_chance", "min_chance", "max_chance", "offend_ambush_chance")),
        ("sneak", ("base_chance", "min_chance", "max_chance", "cache_chance")),
        ("bribe", ("base_chance", "min_chance", "max_chance")),
        ("observe", ("provoke_chance",)),
    ):
        for key in limits:
            value = (data.get(section) or {}).get(key)
            if value is None:
                continue
            if not _is_probability(value):
                result.add("bad_encounter_chance", f"encounters.{section}.{key} must be between 0 and 1 (got {value!r})")

    for key in ("chance_by_danger", "hazard_chance_by_danger"):
        table = (data.get("formation") or {}).get(key) or (data.get("encounter") or {}).get(key)
        if table is not None and (not isinstance(table, list) or any(not _is_probability(v) for v in table)):
            result.add("bad_encounter_chance", f"encounters.{key} must be a list of probabilities between 0 and 1")
    for key in ("strike_multiplier",):
        value = (data.get("ambush") or {}).get(key)
        if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0):
            result.add("bad_encounter_tuning", f"encounters.ambush.{key} must be a non-negative number")
    for key in ("max_extra_foes", "max_pack_presses", "pack_stat_scale", "pack_exp_ratio", "pack_loot_ratio"):
        value = (data.get("formation") or {}).get(key)
        if value is not None and (not isinstance(value, (int, float)) or isinstance(value, bool) or value < 0):
            result.add("bad_encounter_tuning", f"encounters.formation.{key} must be a non-negative number")

    seen: Set[str] = set()
    for entry in data.get("hazards") or []:
        hazard_id = str(entry.get("id", ""))
        if not hazard_id or hazard_id in seen:
            result.add("bad_hazard", f"hazard '{hazard_id}' is missing an id or duplicates another hazard")
            continue
        seen.add(hazard_id)
        if not entry.get("name") or not entry.get("text"):
            result.add("bad_hazard", f"hazard '{hazard_id}' needs a name and flavour text")
        effect = entry.get("effect") or {}
        if effect.get("type") != "damage" or int(effect.get("magnitude", 0)) <= 0:
            result.add("bad_hazard", f"hazard '{hazard_id}' must deal damage with a positive magnitude")
        for key in ("push_base_chance", "defuse_base_chance", "comprehension_bonus"):
            if not _is_probability(entry.get(key)):
                result.add("bad_hazard", f"hazard '{hazard_id}' {key} must be between 0 and 1")

    seen_traps: Set[str] = set()
    for entry in data.get("traps") or []:
        trap_id = str(entry.get("id", ""))
        if not trap_id or trap_id in seen_traps:
            result.add("bad_trap", f"trap '{trap_id}' is missing an id or duplicates another trap")
            continue
        seen_traps.add(trap_id)
        effect = entry.get("effect") or {}
        if int(effect.get("magnitude", 0)) <= 0:
            result.add("bad_trap", f"trap '{trap_id}' needs a positive damage magnitude")

    # Parley/toll eligibility is derived from the enemy catalogue; a name that
    # matches nothing would silently never apply.
    known_enemies = _id_set(registry.enemies) | _id_set(registry.character_enemies)
    mindless = data.get("mindless") or {}
    for enemy_id in (mindless.get("people") or []):
        if enemy_id not in known_enemies:
            result.add("bad_mindless_ref", f"encounters.mindless.people names unknown enemy '{enemy_id}'")
    for enemy_id in (mindless.get("overrides") or {}):
        if enemy_id not in known_enemies:
            result.add("bad_mindless_ref", f"encounters.mindless.overrides names unknown enemy '{enemy_id}'")


def _is_probability(value: Any) -> bool:
    """Return ``True`` when ``value`` is a number inside the 0-1 range."""
    return isinstance(value, (int, float)) and not isinstance(value, bool) and 0.0 <= float(value) <= 1.0


# -- travel gates --------------------------------------------------------
def _realm_keys(realms: Dict[str, Any]) -> Set[str]:
    """Lowercased realm ids/display names a gate may legitimately name.

    Mirrors ``TravelService._build_order`` (ids *and* display names) plus the
    open-realm sentinels, so acceptance here matches runtime acceptance.
    """
    keys = {"", "none", "any"}
    for realm in (realms or {}).get("realms", []):
        for key in (realm.get("id"), realm.get("display_name")):
            if key:
                keys.add(str(key).strip().lower())
    return keys


def _connections(location: Dict[str, Any]) -> List[str]:
    for key in ("connected_locations", "connections"):
        if key in location:
            return list(location.get(key) or [])
    return []
