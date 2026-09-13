"""Collection validators for characters, factions, prose and the legacy tree.

Split out of ``data_validator`` (V.5) so the social/faction lane owns its own
file. Called by :func:`game.validation.data_validator.validate_all_game_data`;
every function keeps the signature and verdict it had before the split.

This module reads data only; it never mutates the registry or touches gameplay.
"""
from __future__ import annotations

import re
from typing import Set, Tuple

from game.data.registry import GameDataRegistry
from game.systems.combat_system import COMBO_ROLES
from game.systems.origin_system import STAT_FIELDS
from game.validation.narrative_lint import lint_narrative_templates
from game.validation.support import _id_set
from game.validation.validation_error import ValidationResult


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
        min_story_tier = character.get("min_story_tier")
        if min_story_tier is not None and (not isinstance(min_story_tier, int) or isinstance(min_story_tier, bool) or not 1 <= min_story_tier <= 6):
            result.add("bad_character", f"character '{character_id}' min_story_tier must be an integer between 1 and 6")
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


# -- trainers ------------------------------------------------------------
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


# -- sects ---------------------------------------------------------------
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
        tier = sect.get("tier")
        if tier is not None and (not isinstance(tier, int) or isinstance(tier, bool) or not 1 <= tier <= 6):
            result.add("bad_sect", f"sect '{sect_id}' tier must be an integer between 1 and 6")
        min_story_tier = (sect.get("join_requirements", {}) or {}).get("min_story_tier")
        if min_story_tier is not None and (not isinstance(min_story_tier, int) or isinstance(min_story_tier, bool) or not 1 <= min_story_tier <= 6):
            result.add("bad_sect", f"sect '{sect_id}' min_story_tier must be an integer between 1 and 6")
        techniques = sect.get("techniques", [])
        if techniques and not isinstance(techniques, list):
            result.add("bad_sect", f"sect '{sect_id}' techniques must be a list")

    # Technique halls are validated in a second pass so path locks may point at
    # any sect's path (a sect can teach another lineage's art it has seized).
    skill_ids = {skill.get("id") for skill in registry.skills}
    supported_currencies = {"gold", "spirit_stone"}
    for sect in registry.sects:
        sect_id = sect.get("id")
        techniques = sect.get("techniques", [])
        if not isinstance(techniques, list):
            continue
        seen_skill_ids: Set[str] = set()
        for entry in techniques:
            if not isinstance(entry, dict):
                result.add("bad_sect", f"sect '{sect_id}' technique entries must be objects")
                continue
            skill_id = entry.get("skill_id")
            if skill_id not in skill_ids:
                result.add("bad_sect", f"sect '{sect_id}' offers missing skill '{skill_id}'")
            if skill_id in seen_skill_ids:
                result.add("bad_sect", f"sect '{sect_id}' lists skill '{skill_id}' more than once")
            if isinstance(skill_id, str):
                seen_skill_ids.add(skill_id)
            price = entry.get("price")
            if not isinstance(price, dict) or not price:
                result.add("bad_sect", f"sect '{sect_id}' skill '{skill_id}' price must be a non-empty object")
            else:
                for currency_name, amount in price.items():
                    if currency_name not in supported_currencies:
                        result.add("bad_sect", f"sect '{sect_id}' skill '{skill_id}' has unsupported currency '{currency_name}'")
                    if not isinstance(amount, int) or isinstance(amount, bool) or amount <= 0:
                        result.add("bad_sect", f"sect '{sect_id}' skill '{skill_id}' price.{currency_name} must be a positive integer")
            required_path = entry.get("required_path")
            if required_path and required_path not in seen_paths:
                result.add("bad_sect", f"sect '{sect_id}' skill '{skill_id}' required_path '{required_path}' is not a known sect path")
            min_tier = entry.get("min_tier")
            if min_tier is not None and (not isinstance(min_tier, int) or isinstance(min_tier, bool) or min_tier < 1):
                result.add("bad_sect", f"sect '{sect_id}' skill '{skill_id}' min_tier must be a positive integer")


# -- daos ----------------------------------------------------------------
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


# -- skills --------------------------------------------------------------
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
        # B.6 combo roles: an optional stance role on active combat techniques.
        # Chain order is fixed (opening -> response -> finisher) and enforced by
        # CombatSystem; data declares only the role.
        role = skill.get("combo_role")
        if role is not None:
            if role not in COMBO_ROLES:
                result.add("bad_skill", f"skill '{skill_id}' combo_role '{role}' must be one of {sorted(COMBO_ROLES)}")
            elif skill.get("type") != "active":
                result.add("bad_skill", f"skill '{skill_id}' combo_role is only meaningful on active skills")


# -- prose ---------------------------------------------------------------
def _validate_lore_glossary(registry: GameDataRegistry, result: ValidationResult) -> None:
    """A.6: glossary entries must be well-formed, unique per slot, and slot-valid."""
    from game.validation.narrative_lint import GLOSSARY_SLOTS

    seen: Set[Tuple[str, str]] = set()
    for entry in registry.lore_glossary:
        if not isinstance(entry, dict):
            result.add("bad_glossary", "lore glossary entry must be an object")
            continue
        term = entry.get("term")
        slot = entry.get("slot", "any")
        if not isinstance(term, str) or not term:
            result.add("bad_glossary", "lore glossary entry is missing a non-empty 'term'")
            continue
        if not isinstance(slot, str) or not slot:
            result.add("bad_glossary", f"glossary term '{term}' has an invalid 'slot'")
            continue
        if slot != "any" and slot not in GLOSSARY_SLOTS:
            result.add("bad_glossary", f"glossary term '{term}' declares unknown slot '{slot}'")
        key = (slot, term)
        if key in seen:
            result.add("duplicate_id", f"lore glossary: duplicate term '{term}' for slot '{slot}'")
        seen.add(key)
        if not isinstance(entry.get("summary", ""), str):
            result.add("bad_glossary", f"glossary term '{term}' summary must be a string")


def _validate_narrative_templates(registry: GameDataRegistry, result: ValidationResult) -> None:
    """Lint narrative templates (structure, slots, when-clauses, coverage)."""
    for category, message in lint_narrative_templates(registry.narrative_templates):
        result.add(category, message)


# -- origins -------------------------------------------------------------
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


# -- legacy tree ---------------------------------------------------------
def _validate_legacy_tree(registry: GameDataRegistry, result: ValidationResult) -> None:
    """Validate the legacy unlock tree (ROADMAP C.5).

    Checks tier/node structure, snake_case ids, positive costs, ``kind`` values,
    per-kind target resolution (sects/skills; titles are free-form snake_case),
    and tier reachability (a tier's requirement cannot exceed its position).
    """
    tree = registry.legacy_tree
    if not tree:
        return
    sect_ids = _id_set(registry.sects)
    skill_ids = _id_set(registry.skills)
    kinds = ("sect", "technique", "title")
    seen_nodes: Set[str] = set()
    tiers = tree.get("tiers")
    if not isinstance(tiers, list) or not tiers:
        result.add("bad_legacy_tree", "legacy_tree.tiers must be a non-empty list")
        return
    for position, tier in enumerate(tiers):
        if not isinstance(tier, dict):
            result.add("bad_legacy_tree", "legacy tier entry must be an object")
            continue
        tier_id = tier.get("id")
        if not isinstance(tier_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", tier_id):
            result.add("bad_legacy_tree", f"legacy tier id '{tier_id}' must be stable snake_case")
            continue
        if not isinstance(tier.get("display_name"), str) or not tier.get("display_name"):
            result.add("bad_legacy_tree", f"legacy tier '{tier_id}' display_name is required")
        required = tier.get("required_meta_tier", 0)
        if isinstance(required, bool) or not isinstance(required, int) or required < 0:
            result.add("bad_legacy_tree", f"legacy tier '{tier_id}' required_meta_tier must be a non-negative integer")
        elif required > position:
            result.add("bad_legacy_tree", f"legacy tier '{tier_id}' requires {required} earlier tiers but only {position} exist before it")
        unlocks = tier.get("unlocks")
        if not isinstance(unlocks, list) or not unlocks:
            result.add("bad_legacy_tree", f"legacy tier '{tier_id}' unlocks must be a non-empty list")
            continue
        for node in unlocks:
            if not isinstance(node, dict):
                result.add("bad_legacy_tree", f"legacy tier '{tier_id}' unlock entry must be an object")
                continue
            node_id = node.get("id")
            if not isinstance(node_id, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", node_id):
                result.add("bad_legacy_tree", f"legacy unlock id '{node_id}' must be stable snake_case")
                continue
            if node_id in seen_nodes:
                result.add("duplicate_id", f"legacy unlock: duplicate id '{node_id}'")
            seen_nodes.add(node_id)
            kind = node.get("kind")
            if kind not in kinds:
                result.add("bad_legacy_tree", f"legacy unlock '{node_id}' has unknown kind '{kind}'")
                continue
            target = node.get("target_id")
            if kind == "sect" and target not in sect_ids:
                result.add("bad_legacy_tree", f"legacy unlock '{node_id}' references missing sect '{target}'")
            if kind == "technique" and target not in skill_ids:
                result.add("bad_legacy_tree", f"legacy unlock '{node_id}' references missing skill '{target}'")
            if kind == "title" and (not isinstance(target, str) or not re.fullmatch(r"[a-z][a-z0-9_]*", target or "")):
                result.add("bad_legacy_tree", f"legacy unlock '{node_id}' title target must be stable snake_case")
            cost = node.get("cost", 0)
            if isinstance(cost, bool) or not isinstance(cost, int) or cost <= 0:
                result.add("bad_legacy_tree", f"legacy unlock '{node_id}' cost must be a positive integer")
