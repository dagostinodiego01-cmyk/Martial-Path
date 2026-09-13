"""Dead-content sweep (ROADMAP Phase 3, task G.2).

The central validator answers "is the shipped content *internally consistent*?"
(every reference resolves, every id unique). This module answers the next
question the roadmap cares about: **is every entry reachable and meaningful in
play?** Content that no acquisition path can ever produce, or that resolves to
nothing when used, is invisible work -- and worse than absent, because it
promises the player something the engine cannot deliver.

Two failure classes are detected:

* **Unreachable** -- no path in the live game produces the entry. Skills need a
  trainer/shop/loot/pool/sect-hall/manual path; enemies must sit in an encounter
  pool, a secret realm, or an authored quest; NPCs must be anchored to a
  location and have a satisfiable unlock gate; quests must be rooted in an
  ``auto_start`` quest chain.
* **Trap options** -- the entry *is* reachable but does nothing, or strictly
  worse than a neighbour at the same price. A consumable whose ``effect`` the
  engine cannot interpret burns the stack for nothing; equipment with no
  modifiers changes no number; an active technique whose effect has no branch in
  ``CombatSystem`` resolves to ``no_combat_effect``; a shop offer that is
  dominated by a cheaper item in the same rack is a purchase the player can only
  regret.

Everything is read-only and derived from the live data files plus the *same*
effect vocabularies the systems execute against, so the sweep cannot drift from
the engine. ``tools/dead_content_report.py`` prints it;
``tests/test_dead_content.py`` holds the acceptance criteria and
``validate_all_game_data()`` runs it as part of the standard data gate.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from game.core.constants import MAX_STORY_TIER
from game.data.registry import GameDataRegistry
from game.systems.combat_system import SUPPORTED_ACTIVE_EFFECTS
from game.systems.effect_system import SUPPORTED_EFFECTS as SUPPORTED_ITEM_EFFECTS
from game.systems.skill_system import GROWTH_PASSIVE_EFFECTS
from game.systems.stats_system import STAT_PASSIVE_EFFECTS

# NPC gates resolve through ``CharacterService.required_story_tier``, which folds
# the legacy 1-8 ``unlock.min_stage`` ladder (against which ``player.stage`` never
# advances past 1) onto ``MAX_STORY_TIER``; a gate above that could never open.

# Equipment modifier groups compared when looking for dominated shop offers.
_MODIFIER_GROUPS = ("stat_modifiers", "cultivation_modifiers", "utility_modifiers")

# Item effects the engine resolves *outside* EffectSystem: a technique manual is
# consumed by the engine's USE_ITEM path, which teaches the skill directly.
_ENGINE_HANDLED_ITEM_EFFECTS = frozenset({"learn_skill"})

# Effect values that mean "deliberately inert" (a crafting material). Using such
# an item is refused with ITEM_NOT_USABLE rather than silently wasted.
_INERT_EFFECTS = frozenset({"", "none"})


class _Sources:
    """Index of content ids to the acquisition paths that produce them.

    ``find`` is tracked separately from the authored paths: the rarity-weighted
    exploration find roll draws from the whole item/equipment catalogue, so an
    entry reachable *only* that way is technically obtainable but has no hook
    anywhere in the world.
    """

    def __init__(self) -> None:
        self._authored: Dict[str, Set[str]] = {}
        self._findable: Set[str] = set()

    def add(self, content_id: Any, source: str) -> None:
        if not isinstance(content_id, str) or not content_id:
            return
        self._authored.setdefault(content_id, set()).add(source)

    def add_many(self, content_ids: Any, source: str) -> None:
        for content_id in content_ids or []:
            self.add(content_id, source)

    def mark_findable(self, content_id: Any) -> None:
        if isinstance(content_id, str) and content_id:
            self._findable.add(content_id)

    def has(self, content_id: str) -> bool:
        return content_id in self._authored or content_id in self._findable

    def is_authored(self, content_id: str) -> bool:
        return content_id in self._authored

    def sources_of(self, content_id: str) -> List[str]:
        return sorted(self._authored.get(content_id, ()))

    def authored_ids(self) -> Set[str]:
        return set(self._authored)

    def findable_ids(self) -> Set[str]:
        return set(self._findable)


def build_report(registry: Optional[GameDataRegistry] = None) -> Dict[str, Any]:
    """Return the full dead-content report as a JSON-safe dict."""
    registry = registry or GameDataRegistry.load()

    item_sources = _item_sources(registry)
    skill_sources = _skill_sources(registry, item_sources)
    enemy_sources, foe_sources = _enemy_sources(registry)
    poolless_locations = _locations_without_a_combat_pool(registry)
    if poolless_locations:
        # A location with no curated pool falls back to a uniform draw over the
        # whole random catalogue (EventSystem._combat_event), which makes every
        # random enemy reachable there. Record that so the sweep neither misses
        # dead foes nor reports false ones.
        for enemy in registry.enemies:
            enemy_sources.add(enemy.get("id"), f"fallback:{poolless_locations[0]}")
    character_sources = _character_sources(registry)
    dao_sources = _dao_sources(registry)
    quest_report = _quest_report(registry)
    recipe_report = _recipe_report(registry, item_sources)

    item_ids = _ids(registry.items)
    equipment_ids = _ids(registry.equipment)
    skill_ids = _ids(registry.skills)
    return {
        "counts": {
            "skills": len(skill_ids),
            "items": len(item_ids),
            "equipment": len(equipment_ids),
            "enemies": len(registry.enemies),
            "named_foes": len(registry.character_enemies),
            "characters": len(registry.characters),
            "daos": len(registry.daos),
            "quests": len(registry.quests),
            "recipes": len(registry.refining_recipes),
            "secret_realms": len(registry.secret_realm),
            "origins": len(registry.origins),
        },
        "unreachable": {
            "skills": sorted(skill_ids - skill_sources.authored_ids()),
            "items": sorted(i for i in item_ids if not item_sources.has(i)),
            "equipment": sorted(i for i in equipment_ids if not item_sources.has(i)),
            "enemies": sorted(_ids(registry.enemies) - enemy_sources.authored_ids()),
            "named_foes": sorted(_ids(registry.character_enemies) - foe_sources.authored_ids()),
            "characters": sorted(_ids(registry.characters) - character_sources),
            "daos": sorted(_ids(registry.daos) - dao_sources),
            "quests": sorted(quest_report["permanently_locked"]),
            "recipes": sorted(recipe_report["dead"]),
            "secret_realms": sorted(_unreachable_secret_realms(registry)),
        },
        "traps": {
            "consumables_with_dead_effects": _consumables_with_dead_effects(registry),
            "consumables_without_effect": _consumables_without_effect(registry),
            "inert_items": _inert_items(registry, item_sources),
            "inert_equipment": _inert_equipment(registry),
            "unresolvable_active_skills": _unresolvable_active_skills(registry),
            "unresolvable_passive_skills": _unresolvable_passive_skills(registry),
            "dead_recipes": sorted(recipe_report["traps"]),
            "unsatisfiable_character_gates": _unsatisfiable_character_gates(registry),
            "dominated_shop_equipment": _dominated_shop_equipment(registry),
        },
        "info": {
            # Content whose only acquisition path is the generic find roll: it
            # exists, but no shop/loot/pool/quest/realm hook mentions it.
            "find_only_items": sorted(
                i for i in item_ids if not item_sources.is_authored(i) and item_sources.has(i)
            ),
            "find_only_equipment": sorted(
                i for i in equipment_ids if not item_sources.is_authored(i) and item_sources.has(i)
            ),
            "daos_without_a_foe": sorted(_daos_without_a_foe(registry)),
            "locations_without_a_combat_pool": poolless_locations,
            "quests": quest_report,
        },
    }


def collect_issues(report: Dict[str, Any]) -> List[tuple]:
    """Flatten a report into ``(category, message)`` pairs (empty = clean)."""
    issues: List[tuple] = []
    for content, ids in report["unreachable"].items():
        category = f"unreachable_{content[:-1]}"  # 'skills' -> 'unreachable_skill'
        for content_id in ids:
            issues.append((category, f"'{content_id}' has no acquisition path"))
    for kind, entries in report["traps"].items():
        category = f"trap_{kind[:-1]}" if kind.endswith("s") else f"trap_{kind}"
        for entry in entries:
            if isinstance(entry, dict):
                issues.append((category, f"'{entry.get('id')}': {entry.get('reason')}"))
            else:
                issues.append((category, str(entry)))
    return issues


def collect_problems(report: Dict[str, Any]) -> List[str]:
    """Flatten a report into human-readable problem strings (empty = clean)."""
    return [f"{category}: {message}" for category, message in collect_issues(report)]


def is_clean(report: Dict[str, Any]) -> bool:
    """Return ``True`` when nothing unreachable or trap-like was found."""
    return not collect_problems(report)


# -- acquisition paths ---------------------------------------------------------

def _ids(entries: Any) -> Set[str]:
    return {str(entry["id"]) for entry in entries or [] if isinstance(entry, dict) and "id" in entry}


def _items_by_id(registry: GameDataRegistry) -> Dict[str, Dict[str, Any]]:
    return {str(entry["id"]): entry for entry in registry.items if isinstance(entry, dict) and "id" in entry}


def _equipment_by_id(registry: GameDataRegistry) -> Dict[str, Dict[str, Any]]:
    return {str(entry["id"]): entry for entry in registry.equipment if isinstance(entry, dict) and "id" in entry}


def _manual_to_skill(registry: GameDataRegistry) -> Dict[str, str]:
    """Map a generated/overridden technique-manual item id to its skill id."""
    overrides = {entry["skill_id"]: entry for entry in registry.technique_manuals if entry.get("skill_id")}
    mapping: Dict[str, str] = {}
    for skill in registry.skills:
        skill_id = skill.get("id")
        if not skill_id:
            continue
        override = overrides.get(skill_id, {})
        mapping[str(override.get("id", f"{skill_id}_manual"))] = str(skill_id)
    return mapping


def _item_sources(registry: GameDataRegistry) -> _Sources:
    """Every way an item or piece of equipment can enter a player's inventory."""
    src = _Sources()

    for shop in registry.shops:
        for entry in shop.get("stock", []) or []:
            if isinstance(entry, dict):
                src.add(entry.get("item_id"), f"shop:{shop.get('id')}")

    for label, enemies in (("enemy", registry.enemies), ("foe", registry.character_enemies)):
        for enemy in enemies:
            for drop in enemy.get("loot_table", []) or []:
                if isinstance(drop, dict):
                    src.add(drop.get("item_id"), f"{label}:{enemy.get('id')}")

    for location_id, pool in (registry.encounter_pools or {}).items():
        if isinstance(pool, dict):
            for entry in pool.get("loot", []) or []:
                if isinstance(entry, dict):
                    src.add(entry.get("item_id"), f"pool:{location_id}")

    gathering = registry.gathering or {}
    for entry in gathering.get("default", []) or []:
        if isinstance(entry, dict):
            src.add(entry.get("item_id"), "gather:default")
    for location_id, entries in (gathering.get("locations") or {}).items():
        for entry in entries or []:
            if isinstance(entry, dict):
                src.add(entry.get("item_id"), f"gather:{location_id}")

    for quest in registry.quests:
        rewards = quest.get("rewards", {}) or {}
        for item_id in (rewards.get("items") or {}):
            src.add(item_id, f"quest:{quest.get('id')}")
        for manual_id in (rewards.get("manuals") or {}):
            src.add(manual_id, f"quest:{quest.get('id')}")

    for realm in registry.secret_realm or []:
        for entry in realm.get("treasure_pool", []) or []:
            if isinstance(entry, dict):
                src.add(entry.get("item_id"), f"realm:{realm.get('id')}")
        for item_id in (realm.get("final_reward", {}) or {}).get("items", {}) or {}:
            src.add(item_id, f"realm:{realm.get('id')}")

    for character in registry.characters:
        rewards = (character.get("gameplay_hooks", {}) or {}).get("relationship_rewards", []) or []
        for reward in rewards:
            payload = reward.get("reward", {}) if isinstance(reward, dict) else {}
            src.add(payload.get("item_id"), f"boon:{character.get('id')}")

    for entry in registry.events.get("loot_pool", []) or []:
        if isinstance(entry, dict):
            src.add(entry.get("item_id"), "event:loot_pool")

    # A recipe output is craftable once its inputs are obtainable; iterate to a
    # fixpoint so chained recipes (herb -> pill -> elixir) all resolve.
    for _ in range(4):
        changed = False
        for recipe in registry.refining_recipes:
            output = (recipe.get("output", {}) or {}).get("item_id")
            if not output or src.is_authored(str(output)):
                continue
            inputs = (recipe.get("inputs", {}) or {})
            if inputs and all(src.has(str(item_id)) for item_id in inputs):
                src.add(output, f"recipe:{recipe.get('id')}")
                changed = True
        if not changed:
            break

    # The exploration find roll draws from the whole catalogue (see FindSystem).
    for item_id in _ids(registry.items) | _ids(registry.equipment):
        src.mark_findable(item_id)

    return src


def _skill_sources(registry: GameDataRegistry, items: _Sources) -> _Sources:
    """Every way a technique can be learned (trainer, manual, hall, origin, boon)."""
    src = _Sources()
    manual_to_skill = _manual_to_skill(registry)

    for trainer in registry.trainers:
        for entry in trainer.get("techniques", []) or []:
            if isinstance(entry, dict):
                src.add(entry.get("skill_id"), f"trainer:{trainer.get('id')}")
    for sect in registry.sects:
        for entry in sect.get("techniques", []) or []:
            if isinstance(entry, dict):
                src.add(entry.get("skill_id"), f"sect_hall:{sect.get('id')}")
    for quest in registry.quests:
        src.add_many((quest.get("rewards", {}) or {}).get("skills"), f"quest:{quest.get('id')}")
        for manual_id in ((quest.get("rewards", {}) or {}).get("manuals") or {}):
            skill_id = manual_to_skill.get(str(manual_id))
            if skill_id:
                src.add(skill_id, f"quest:{quest.get('id')}")
    for origin in registry.origins:
        src.add_many(origin.get("starting_skills"), f"origin:{origin.get('id')}")
    for tier in (registry.legacy_tree or {}).get("tiers", []) or []:
        for node in tier.get("unlocks", []) or []:
            if isinstance(node, dict) and node.get("kind") == "technique":
                src.add(node.get("target_id"), f"legacy:{node.get('id')}")
    for character in registry.characters:
        rewards = (character.get("gameplay_hooks", {}) or {}).get("relationship_rewards", []) or []
        for reward in rewards:
            payload = reward.get("reward", {}) if isinstance(reward, dict) else {}
            src.add(payload.get("skill_id"), f"boon:{character.get('id')}")

    # Manuals reachable through shops/loot/pools make their skill reachable too.
    for manual_id in items.authored_ids():
        skill_id = manual_to_skill.get(manual_id)
        if skill_id:
            src.add(skill_id, f"manual:{manual_id}")
    return src


def _enemy_sources(registry: GameDataRegistry) -> "tuple[_Sources, _Sources]":
    """Where random enemies and named foes can actually be fought."""
    enemies = _Sources()
    foes = _Sources()

    for location_id, pool in (registry.encounter_pools or {}).items():
        if not isinstance(pool, dict):
            continue
        for entry in pool.get("combat", []) or []:
            if isinstance(entry, dict):
                enemies.add(entry.get("enemy_id"), f"pool:{location_id}")
    for realm in registry.secret_realm or []:
        enemies.add_many(realm.get("enemy_pool"), f"realm:{realm.get('id')}")
        foes.add(realm.get("boss_id"), f"realm:{realm.get('id')}")
    for character in registry.characters:
        foes.add((character.get("gameplay_hooks", {}) or {}).get("enemy_id"), f"character:{character.get('id')}")
    for quest in registry.quests:
        for objective in quest.get("objectives", []) or []:
            if isinstance(objective, dict) and objective.get("type") == "defeat":
                target = objective.get("target")
                if target and target != "any":
                    enemies.add(target, f"quest:{quest.get('id')}")
                    foes.add(target, f"quest:{quest.get('id')}")
    return enemies, foes


def _locations_without_a_combat_pool(registry: GameDataRegistry) -> List[str]:
    """Locations relying on the global fallback draw instead of a curated pool."""
    return sorted(
        str(location["id"])
        for location in registry.locations
        if isinstance(location, dict)
        and "id" in location
        and not ((registry.encounter_pools or {}).get(str(location["id"]), {}) or {}).get("combat")
    )


def _character_sources(registry: GameDataRegistry) -> Set[str]:
    """NPCs anchored to a location are meetable; unanchored ones never appear."""
    anchored: Set[str] = set()
    for location in registry.locations:
        anchored |= {str(npc_id) for npc_id in location.get("npc_ids", []) or []}
    return anchored


def _dao_sources(registry: GameDataRegistry) -> Set[str]:
    """Daos the player can actually hold: origin daos, the default, or DAO_AWAKEN.

    Every catalogue dao is selectable through the one-time dao awakening, so
    membership in ``daos.json`` is itself a path; the sweep only fails on daos
    that exist in data but are not in the catalogue the engine loads.
    """
    return _ids(registry.daos)


def _daos_without_a_foe(registry: GameDataRegistry) -> Set[str]:
    """Catalogue daos no enemy carries (content-quality signal for the dao wheel)."""
    used: Set[str] = set()
    for origin in registry.origins:
        if origin.get("dao_id"):
            used.add(str(origin["dao_id"]))
    for enemy in list(registry.enemies) + list(registry.character_enemies):
        if enemy.get("dao_id"):
            used.add(str(enemy["dao_id"]))
    return _ids(registry.daos) - used


# -- reachability details ------------------------------------------------------

def _unreachable_secret_realms(registry: GameDataRegistry) -> Set[str]:
    """Secret realms bound to a location that exists (and thus can be entered)."""
    location_ids = _ids(registry.locations)
    return {
        str(realm["id"])
        for realm in registry.secret_realm or []
        if isinstance(realm, dict)
        and "id" in realm
        and str(realm.get("location_id")) not in location_ids
    }


def _quest_report(registry: GameDataRegistry) -> Dict[str, Any]:
    """Compute which quests can ever activate, following the chain fixpoint."""
    definitions = {
        str(quest["id"]): quest
        for quest in registry.quests
        if isinstance(quest, dict) and "id" in quest
    }
    reachable: Set[str] = set()
    for quest_id, quest in definitions.items():
        if quest.get("auto_start", False):
            reachable.add(quest_id)
    changed = True
    while changed:
        changed = False
        for quest_id, quest in definitions.items():
            if quest_id in reachable:
                continue
            requires = quest.get("requires", {}) or {}
            if not requires:
                continue  # locked forever: nothing can open it
            prereqs = [str(p) for p in requires.get("completed", []) or []]
            if all(prereq in reachable for prereq in prereqs):
                reachable.add(quest_id)
                changed = True
    locked = sorted(set(definitions) - reachable)
    return {
        "total": len(definitions),
        "auto_start": sum(1 for quest in definitions.values() if quest.get("auto_start", False)),
        "reachable": sorted(reachable),
        "permanently_locked": locked,
    }


def _recipe_report(registry: GameDataRegistry, items: _Sources) -> Dict[str, Any]:
    """Recipes whose inputs can never be gathered, and recipes that craft junk."""
    items_by_id = _items_by_id(registry)
    dead: Set[str] = set()
    traps: List[Dict[str, str]] = []
    for recipe in registry.refining_recipes:
        if not isinstance(recipe, dict) or "id" not in recipe:
            continue
        recipe_id = str(recipe["id"])
        inputs = recipe.get("inputs", {}) or {}
        unobtainable = sorted(
            str(item_id) for item_id in inputs if not items.has(str(item_id))
        )
        if unobtainable:
            dead.add(recipe_id)
            continue
        output_id = str((recipe.get("output", {}) or {}).get("item_id", ""))
        output = items_by_id.get(output_id, {})
        if output and not _item_is_meaningful(output, output_id, registry):
            traps.append({"id": recipe_id, "reason": f"output '{output_id}' has no use"})
    return {"dead": dead, "traps": traps}


# -- trap detection ------------------------------------------------------------

def _supported_item_effect(item: Dict[str, Any]) -> bool:
    effect = str(item.get("effect", "") or "")
    return effect in SUPPORTED_ITEM_EFFECTS or effect in _ENGINE_HANDLED_ITEM_EFFECTS


def _consumables_with_dead_effects(registry: GameDataRegistry) -> List[Dict[str, str]]:
    """Consumables advertising an effect the engine cannot interpret.

    Using one removes the stack and reports ``no_effect``: the item promises
    something and delivers nothing.
    """
    flagged: List[Dict[str, str]] = []
    for item in registry.items:
        if not isinstance(item, dict):
            continue
        effect = str(item.get("effect", "") or "")
        if effect in _INERT_EFFECTS or _supported_item_effect(item):
            continue
        if item.get("consumed_on_use") or item.get("type") == "consumable":
            flagged.append({"id": str(item.get("id")), "reason": f"unsupported effect '{effect}'"})
    return flagged


def _consumables_without_effect(registry: GameDataRegistry) -> List[Dict[str, str]]:
    """Consumables the engine refuses to consume (``ITEM_NOT_USABLE``)."""
    flagged: List[Dict[str, str]] = []
    for item in registry.items:
        if not isinstance(item, dict):
            continue
        if item.get("type") != "consumable":
            continue
        effect = str(item.get("effect", "") or "")
        if effect not in _INERT_EFFECTS:
            continue
        flagged.append({"id": str(item.get("id")), "reason": "declared consumable but has no effect"})
    return flagged


def _item_is_meaningful(item: Dict[str, Any], item_id: str, registry: GameDataRegistry) -> bool:
    """Return whether an item does something for the player, beyond existing.

    Meaningful means: it has a resolvable use effect, it is an ingredient in a
    refining recipe, it is spent by a talent upgrade, it is required for a
    breakthrough, or it is a quest reward item (reward-only trophies are still
    content the player acts on by selling or hoarding).
    """
    if _supported_item_effect(item):
        return True
    for recipe in registry.refining_recipes:
        if isinstance(recipe, dict) and item_id in (recipe.get("inputs", {}) or {}):
            return True
    for collection in (registry.martial_talents, registry.body_talents):
        for trait in collection:
            for upgrade in trait.get("upgrade_options", []) or []:
                if isinstance(upgrade, dict) and item_id in (upgrade.get("cost", {}) or {}):
                    return True
    for track in (registry.body_realms, registry.essence_realms):
        for realm in track.get("realms", []) or []:
            if item_id in ((realm.get("breakthrough_requirements", {}) or {}).get("resources", []) or []):
                return True
    return False


def _inert_items(registry: GameDataRegistry, items: _Sources) -> List[Dict[str, str]]:
    """Materials with no effect, no crafting/upgrade role, and no source."""
    flagged: List[Dict[str, str]] = []
    for item in registry.items:
        if not isinstance(item, dict):
            continue
        item_id = str(item.get("id"))
        if str(item.get("type", "material")) == "equipment":
            continue
        if str(item.get("effect", "") or "") not in _INERT_EFFECTS:
            continue
        if _item_is_meaningful(item, item_id, registry):
            continue
        if items.is_authored(item_id):
            continue  # a plain material that drops/sells: economy content, not dead
        flagged.append({"id": item_id, "reason": "no effect, no recipe/upgrade role, no source"})
    return flagged


def _inert_equipment(registry: GameDataRegistry) -> List[Dict[str, str]]:
    """Equipment that modifies nothing: wearing it changes no number."""
    flagged: List[Dict[str, str]] = []
    for item in registry.equipment:
        if not isinstance(item, dict):
            continue
        has_modifier = any((item.get(group) or {}) for group in _MODIFIER_GROUPS)
        if has_modifier or item.get("set_bonuses"):
            continue
        flagged.append({"id": str(item.get("id")), "reason": "no stat/cultivation/utility modifiers"})
    return flagged


def _unresolvable_active_skills(registry: GameDataRegistry) -> List[Dict[str, str]]:
    """Active techniques whose effect resolves to ``no_combat_effect``."""
    flagged: List[Dict[str, str]] = []
    for skill in registry.skills:
        if not isinstance(skill, dict):
            continue
        if str(skill.get("type", "active")) != "active":
            continue
        effect = str(skill.get("effect", "damage") or "damage")
        if effect not in SUPPORTED_ACTIVE_EFFECTS:
            flagged.append({"id": str(skill.get("id")), "reason": f"unhandled active effect '{effect}'"})
    return flagged


def _unresolvable_passive_skills(registry: GameDataRegistry) -> List[Dict[str, str]]:
    """Passives whose effect is honoured by neither StatsSystem nor learn-time."""
    supported = STAT_PASSIVE_EFFECTS | GROWTH_PASSIVE_EFFECTS
    flagged: List[Dict[str, str]] = []
    for skill in registry.skills:
        if not isinstance(skill, dict):
            continue
        if str(skill.get("type", "active")) == "active":
            continue
        effect = str(skill.get("effect", "") or "")
        if effect not in supported:
            flagged.append({"id": str(skill.get("id")), "reason": f"unhandled passive effect '{effect}'"})
    return flagged


def _unsatisfiable_character_gates(registry: GameDataRegistry) -> List[Dict[str, str]]:
    """NPCs whose unlock gate can never open under the live progression model."""
    from game.services.character_service import required_story_tier

    flagged: List[Dict[str, str]] = []
    for character in registry.characters:
        if not isinstance(character, dict):
            continue
        required = required_story_tier(character)
        if required > MAX_STORY_TIER:
            flagged.append(
                {
                    "id": str(character.get("id")),
                    "reason": f"requires story tier {required} but the ladder ends at {MAX_STORY_TIER}",
                }
            )
    return flagged


def _dominated_shop_equipment(registry: GameDataRegistry) -> List[Dict[str, str]]:
    """Shop offers strictly beaten by a no-more-expensive item in the same rack."""
    equipment = _equipment_by_id(registry)
    flagged: List[Dict[str, str]] = []
    seen: Set[str] = set()
    for shop in registry.shops:
        stock: List[Dict[str, Any]] = []
        for entry in shop.get("stock", []) or []:
            if not isinstance(entry, dict):
                continue
            item = equipment.get(str(entry.get("item_id")))
            if item is None:
                continue
            price = entry.get("price", {}) if isinstance(entry.get("price"), dict) else {}
            stock.append({"item": item, "price": {str(k): int(v) for k, v in price.items()}})
        for dominated in stock:
            for dominator in stock:
                if dominated is dominator:
                    continue
                reason = domination_reason(dominator, dominated)
                if reason is None:
                    continue
                key = str(dominated["item"].get("id"))
                if key in seen:
                    continue
                seen.add(key)
                flagged.append(
                    {
                        "id": key,
                        "reason": (
                            f"beaten by '{dominator['item'].get('id')}' "
                            f"({_price_text(dominator['price'])} vs {_price_text(dominated['price'])}: {reason})"
                        ),
                    }
                )
                break
    return flagged


def domination_reason(dominator: Dict[str, Any], dominated: Dict[str, Any]) -> Optional[str]:
    """Describe how ``dominator`` strictly beats ``dominated``, or ``None``.

    Only equipment sharing a slot and category is compared, and only when the
    dominator is no more expensive (in gold) -- the case where a shopper has no
    reason to ever pick the other item.

    Public because it is the one definition of "trap option": the content seed
    tool asks this question both ways when it stocks a rack, so a placement can
    never create a trap the sweep would fail on later.
    """
    a_item, b_item = dominator["item"], dominated["item"]
    a_price, b_price = dominator["price"], dominated["price"]
    for currency in set(a_price) | set(b_price):
        if a_price.get(currency, 0) > b_price.get(currency, 0):
            return None  # a pricier upgrade is a ladder, not a trap
    if str(a_item.get("category")) != str(b_item.get("category")):
        return None
    if not set(a_item.get("valid_slots", []) or []) & set(b_item.get("valid_slots", []) or []):
        return None
    keys = {
        key
        for group in _MODIFIER_GROUPS
        for entry in (a_item, b_item)
        for key in (entry.get(group) or {})
    }
    better = False
    for key in sorted(keys):
        if not _higher_is_better(key):
            # Ambiguous direction (e.g. a strain or cost multiplier): refuse to
            # call it, so the sweep only reports domination it can defend.
            return None
        a_value = _modifier_value(a_item, key)
        b_value = _modifier_value(b_item, key)
        if a_value < b_value:
            return None
        if a_value > b_value:
            better = True
    return f"dominates on {_domination_label(a_item, b_item)}" if better else None


def _higher_is_better(key: str) -> bool:
    """Return whether a larger value is unambiguously the better item stat."""
    return key in _STAT_KEYS or key.endswith("_bonus")


# Flat stats where more is simply better (mirrors the combat stat vocabulary).
_STAT_KEYS = frozenset(
    {
        "strength",
        "body_strength",
        "attack",
        "defense",
        "max_hp",
        "max_qi",
        "speed",
        "evasion",
        "comprehension",
    }
)


def _domination_label(a_item: Dict[str, Any], b_item: Dict[str, Any]) -> str:
    keys = sorted(
        {
            key
            for group in _MODIFIER_GROUPS
            for entry in (a_item, b_item)
            for key in (entry.get(group) or {})
            if _higher_is_better(key)
        }
    )
    improved = [key for key in keys if _modifier_value(a_item, key) > _modifier_value(b_item, key)]
    return ", ".join(improved) if improved else "equal modifiers at a lower price"


def _price_text(price: Dict[str, int]) -> str:
    return " + ".join(f"{amount} {currency}" for currency, amount in sorted(price.items())) or "free"


def _modifier_value(entry: Dict[str, Any], key: str) -> float:
    for group in _MODIFIER_GROUPS:
        group_data = entry.get(group) or {}
        if key in group_data:
            try:
                return float(group_data[key])
            except (TypeError, ValueError):
                return 0.0
    return 0.0
