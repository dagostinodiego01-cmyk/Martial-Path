"""Collection validators for items, gear, markets, recipes and quest content.

Split out of ``data_validator`` (V.5) so the economy/loot lane owns its own file
instead of sharing one 1,300-line module with four other lanes. Called by
:func:`game.validation.data_validator.validate_all_game_data`; every function
keeps the signature and verdict it had before the split.

This module reads data only; it never mutates the registry or touches gameplay.
"""
from __future__ import annotations

import re
from typing import Set

from game.data.registry import GameDataRegistry
from game.validation.support import _check_loot, _id_set, _validate_modifier_group
from game.validation.validation_error import ValidationResult


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


# -- gathering -----------------------------------------------------------
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


# -- alchemy -------------------------------------------------------------
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


# -- secret realms -------------------------------------------------------
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


# -- technique manuals ---------------------------------------------------
def _validate_technique_manuals(registry: GameDataRegistry, result: ValidationResult) -> None:
    skill_ids = _id_set(registry.skills)
    for override in registry.technique_manuals:
        skill_id = override.get("skill_id") if isinstance(override, dict) else None
        if not skill_id:
            result.add("bad_manual", "technique manual override is missing 'skill_id'")
        elif skill_id not in skill_ids:
            result.add("bad_manual", f"technique manual override references missing skill '{skill_id}'")


# -- quests --------------------------------------------------------------
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


# -- exploration finds ---------------------------------------------------
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


# -- reachability (ROADMAP G.2) ------------------------------------------
def _validate_dead_content(registry: GameDataRegistry, result: ValidationResult) -> None:
    """ROADMAP G.2: nothing shipped may be unreachable or a trap option.

    The checks above prove the content graph is internally consistent; this one
    proves every entry is actually obtainable in play and does something once
    obtained. See :mod:`game.validation.dead_content` for the criteria.
    """
    from game.validation.dead_content import build_report, collect_issues

    for category, message in collect_issues(build_report(registry)):
        result.add(category, message)
