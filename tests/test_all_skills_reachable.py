"""Every skill must be obtainable through at least one acquisition path.

Technique manuals are auto-generated per skill; this test asserts the content
layer actually routes them into the game through a trainer, a shop, an enemy
loot table, an encounter-pool loot entry, or a sect technique hall. It is the
regression guard for the "martial identity never grows" gap: add a new skill
without seeding it and this fails, naming exactly which skills are stranded.
"""
from game.data.registry import GameDataRegistry


def _manual_to_skill(registry: GameDataRegistry) -> dict[str, str]:
    """Map a manual item id back to its skill id (mirrors engine generation)."""
    overrides = {entry["skill_id"]: entry for entry in registry.technique_manuals if entry.get("skill_id")}
    mapping: dict[str, str] = {}
    for skill in registry.skills:
        skill_id = skill["id"]
        override = overrides.get(skill_id, {})
        mapping[str(override.get("id", f"{skill_id}_manual"))] = skill_id
    return mapping


def test_every_skill_is_reachable() -> None:
    registry = GameDataRegistry.load()
    manual_to_skill = _manual_to_skill(registry)
    all_skills = {skill["id"] for skill in registry.skills}

    reachable: set[str] = set()

    # Trainers teach skills directly (the canonical path).
    for trainer in registry.trainers:
        for entry in trainer.get("techniques", []):
            reachable.add(str(entry["skill_id"]))

    # Shops sell manuals.
    for shop in registry.shops:
        for entry in shop.get("stock", []):
            skill_id = manual_to_skill.get(entry.get("item_id"))
            if skill_id:
                reachable.add(skill_id)

    # Enemies (random pool + named foes) drop manuals.
    for enemy in registry.enemies + registry.character_enemies:
        for drop in enemy.get("loot_table", []):
            skill_id = manual_to_skill.get(drop.get("item_id"))
            if skill_id:
                reachable.add(skill_id)

    # Encounter pools offer manuals.
    for pool in registry.encounter_pools.values():
        for entry in pool.get("loot", []):
            skill_id = manual_to_skill.get(entry.get("item_id"))
            if skill_id:
                reachable.add(skill_id)

    # Sect technique halls teach skills directly.
    for sect in registry.sects:
        for entry in sect.get("techniques", []):
            reachable.add(str(entry["skill_id"]))

    missing = all_skills - reachable
    assert not missing, f"unreachable skills: {sorted(missing)}"
    assert reachable == all_skills
