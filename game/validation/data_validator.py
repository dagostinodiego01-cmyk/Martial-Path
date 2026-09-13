"""Central data validation.

Loads the :class:`GameDataRegistry` and checks the cross-references that break
most easily as content grows: dangling item/enemy/character/location ids, id
collisions, and mismatched morality/relationship keys. Everything is collected
into one :class:`ValidationResult`, so ``validate_all_game_data()`` answers a
single question -- "is the shipped content internally consistent?" -- for tests,
tooling, or a pre-flight check.

This module is the entry point only. The per-collection checks live in one
module per domain, so the lanes that own those systems own their validator too:

* :mod:`game.validation.world_checks` -- locations, map, encounter layer
* :mod:`game.validation.progression_checks` -- cultivation, realms, talents
* :mod:`game.validation.character_checks` -- characters, factions, prose
* :mod:`game.validation.economy_checks` -- items, gear, markets, recipes, quests
* :mod:`game.validation.support` -- primitives every domain reuses

The validators read data only; they never mutate the registry or touch gameplay.
"""
from __future__ import annotations

from typing import Optional, Set

from game.data.registry import GameDataRegistry
from game.validation.validation_error import ValidationResult

# -- domain validators (V.5 split) ---------------------------------------
from game.validation.character_checks import (
    _validate_character_enemy_links,
    _validate_character_hooks,
    _validate_character_reaction_keys,
    _validate_daos,
    _validate_enemy_realms,
    _validate_legacy_tree,
    _validate_lore_glossary,
    _validate_narrative_templates,
    _validate_origins,
    _validate_sects,
    _validate_skills,
    _validate_trainers,
)
from game.validation.economy_checks import (
    _validate_dead_content,
    _validate_equipment_data,
    _validate_find_config,
    _validate_gathering,
    _validate_item_references,
    _validate_quests,
    _validate_refining_recipes,
    _validate_secret_realm,
    _validate_shop_data,
    _validate_technique_manuals,
)
from game.validation.progression_checks import (
    _validate_cultivation_schema,
    _validate_defeat_penalty,
    _validate_realm_lifespans,
    _validate_talent_ladder,
    _validate_talent_tracks,
    _validate_talent_upgrade_costs,
)
from game.validation.support import _id_set
from game.validation.world_checks import (
    _validate_encounter_pools,
    _validate_encounters,
    _validate_enemy_abilities,
    _validate_locations,  # noqa: F401  (re-exported: tests import it from here)
    _validate_map_positions,
)


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
    _validate_encounters(registry, result)
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
    _validate_lore_glossary(registry, result)
    _validate_origins(registry, result)
    _validate_legacy_tree(registry, result)
    _validate_gathering(registry, result)
    _validate_refining_recipes(registry, result)
    _validate_secret_realm(registry, result)
    _validate_technique_manuals(registry, result)
    _validate_find_config(registry, result)
    _validate_quests(registry, result)
    _validate_dead_content(registry, result)

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
