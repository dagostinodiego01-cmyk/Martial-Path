"""ROADMAP Phase 3 G.2: dead-content sweep acceptance criteria.

Two things are pinned here. First, the shipped data contains nothing reachable
but meaningless, and nothing unreachable at all (``game.validation.dead_content``
is the checker). Second, the *vocabularies* that decide "meaningful" stay honest:
every effect the sweep treats as implemented is really resolved by the system
that owns it, so the check can never pass by drifting away from the engine.
"""
from types import SimpleNamespace

from game.core.constants import MAX_STORY_TIER
from game.core.engine.views import (
    _GROWTH_PASSIVE_EFFECTS,
    _STAT_PASSIVE_EFFECTS,
    EFFECT_LABELS,
)
from game.data.registry import GameDataRegistry
from game.models.enemy import Enemy
from game.models.player import Player
from game.models.skill import Skill
from game.services.character_service import CharacterService, required_story_tier
from game.systems.combat_system import SUPPORTED_ACTIVE_EFFECTS, CombatSystem
from game.systems.effect_system import SUPPORTED_EFFECTS, EffectSystem
from game.systems.location_system import LocationSystem
from game.systems.morality_system import MoralitySystem
from game.systems.relationship_system import RelationshipSystem
from game.systems.skill_system import GROWTH_PASSIVE_EFFECTS
from game.systems.stats_system import STAT_PASSIVE_EFFECTS, StatsSystem
from game.utils.rng import RNG
from game.validation import validate_all_game_data
from game.validation.dead_content import build_report, collect_issues

# Effects the engine resolves outside EffectSystem (a technique manual is
# consumed by the USE_ITEM path, which teaches the skill directly).
ENGINE_HANDLED_ITEM_EFFECTS = {"learn_skill"}
INERT_EFFECTS = {"", "none"}


def _report():
    return build_report(GameDataRegistry.load())


# -- the sweep is clean --------------------------------------------------------

def test_nothing_shipped_is_unreachable():
    report = _report()
    dead = {kind: ids for kind, ids in report["unreachable"].items() if ids}
    assert not dead, f"content with no acquisition path: {dead}"


def test_no_trap_options():
    report = _report()
    traps = {kind: entries for kind, entries in report["traps"].items() if entries}
    assert not traps, f"reachable but meaningless content: {traps}"


def test_validator_reports_the_same_verdict():
    # The sweep is wired into the central gate, so a data wave cannot add dead
    # content without validate_all_game_data() noticing.
    result = validate_all_game_data()
    dead_categories = sorted(
        {error.category for error in result.errors if error.category.startswith(("unreachable_", "trap_"))}
    )
    assert dead_categories == [], f"validator flagged dead content: {dead_categories}"


def test_issues_flatten_into_validator_categories():
    """The (category, message) contract the central validator consumes."""
    synthetic = {
        "unreachable": {"skills": ["ghost_art"], "items": []},
        "traps": {
            "inert_items": [{"id": "junk", "reason": "no use"}],
            "dead_recipes": [],
        },
    }
    assert collect_issues(synthetic) == [
        ("unreachable_skill", "'ghost_art' has no acquisition path"),
        ("trap_inert_item", "'junk': no use"),
    ]


# -- enemy pools ---------------------------------------------------------------

def test_every_random_enemy_has_a_pool_to_live_in():
    registry = GameDataRegistry.load()
    pooled = {
        entry.get("enemy_id")
        for pool in registry.encounter_pools.values()
        for entry in (pool.get("combat", []) or [])
    }
    stranded = sorted(enemy["id"] for enemy in registry.enemies if enemy["id"] not in pooled)
    assert not stranded, f"enemies no location can roll: {stranded}"


def test_every_location_has_a_curated_combat_pool():
    # A pool-less location would silently fall back to a uniform draw over the
    # whole bestiary (EventSystem), so the sweep's enemy reachability depends on
    # this staying true or being handled explicitly.
    registry = GameDataRegistry.load()
    location_ids = {location["id"] for location in registry.locations}
    assert set(registry.encounter_pools) <= location_ids
    for location_id in sorted(location_ids):
        pool = registry.encounter_pools.get(location_id, {})
        assert pool.get("combat"), f"location '{location_id}' has no combat pool"
        assert len(pool["combat"]) <= 8, f"location '{location_id}' pool is a grab bag"


# -- item effects --------------------------------------------------------------

def test_every_supported_item_effect_does_something():
    """Each name in the vocabulary must actually move a player's state."""
    effects = EffectSystem()
    for effect in sorted(SUPPORTED_EFFECTS):
        player = Player(name="Tester", hp=10, max_hp=100, qi=5, max_qi=100)
        result = effects.apply_to_player(player, effect, 25)
        assert result.get("note") != "no_effect", f"item effect '{effect}' resolves to nothing"


def test_consumables_only_advertise_implemented_effects():
    registry = GameDataRegistry.load()
    allowed = SUPPORTED_EFFECTS | ENGINE_HANDLED_ITEM_EFFECTS | INERT_EFFECTS
    bad = [
        item["id"]
        for item in registry.items
        if item.get("type") == "consumable" and str(item.get("effect", "")) not in allowed
    ]
    assert bad == [], f"consumables promising an unimplemented effect: {bad}"


def test_lifespan_pills_extend_lifespan_instead_of_burning_the_stack():
    engine_effects = EffectSystem()
    player = Player(name="Tester")
    before = player.lifespan_bonus_years
    engine_effects.apply_to_player(player, "lifespan_extension", 300)
    assert player.lifespan_bonus_years == before + 300


def test_breakthrough_aid_steadies_the_foundation():
    player = Player(name="Tester")
    player.cultivation_state.body.foundation_stability = 40.0
    EffectSystem().apply_to_player(player, "breakthrough_aid", 15)
    assert player.cultivation_state.body.foundation_stability == 55.0


def test_cleanse_poison_strips_afflictions_and_keeps_counter():
    player = Player(name="Tester")
    player.statuses = {
        "dot_damage": {"turns": 3, "magnitude": 5.0},
        "debuff_attack": {"turns": 2, "magnitude": 0.5},
        "counter": {"turns": 2, "magnitude": 12.0},
    }
    result = EffectSystem().apply_to_player(player, "cleanse_poison", 1)
    assert result["statuses_cleared"] == 2
    assert "counter" in player.statuses


# -- skill vocabularies --------------------------------------------------------

def test_every_active_effect_resolves_in_combat():
    """No technique in the vocabulary may come back as ``no_combat_effect``."""
    for effect in sorted(SUPPORTED_ACTIVE_EFFECTS):
        skill = Skill.from_dict(
            {
                "id": f"probe_{effect}",
                "name": effect,
                "type": "active",
                "effect": effect,
                "scaling": 1.0,
                "cooldown": 0,
                "qi_cost": 0,
            }
        )
        combat = CombatSystem(RNG(0), StatsSystem({skill.id: skill}))
        player = Player(name="Tester", attack=50, hp=500, max_hp=500, qi=100, max_qi=100)
        enemy = Enemy.from_dict(
            {"id": "e", "name": "E", "body_realm_id": "mortal", "attack": 5, "defense": 1, "hp": 500}
        )
        result = combat.use_skill(player, enemy, skill)
        events = result.get("turn_events", []) or []
        assert any(event.get("skill") == skill.name for event in events), effect
        assert not any(event.get("note") == "no_combat_effect" for event in events), (
            f"active effect '{effect}' is not handled by CombatSystem"
        )


def test_passive_vocabularies_are_shared_with_the_view_layer():
    # views.py labels and categorises passives for the Techniques tab; the sweep
    # validates against the same sets, so they must not fork.
    assert _STAT_PASSIVE_EFFECTS == STAT_PASSIVE_EFFECTS
    assert _GROWTH_PASSIVE_EFFECTS == GROWTH_PASSIVE_EFFECTS


def test_every_supported_effect_has_a_ui_label():
    supported = SUPPORTED_ACTIVE_EFFECTS | STAT_PASSIVE_EFFECTS | GROWTH_PASSIVE_EFFECTS
    missing = sorted(effect for effect in supported if effect not in EFFECT_LABELS)
    assert missing == [], f"techniques whose effect the UI cannot name: {missing}"


def test_passive_effects_split_between_stat_and_growth_without_overlap():
    overlap = STAT_PASSIVE_EFFECTS & GROWTH_PASSIVE_EFFECTS
    assert overlap == set(), f"passive handled twice: {sorted(overlap)}"


# -- character gates ----------------------------------------------------------

def _stub_service(registry: GameDataRegistry) -> CharacterService:
    return CharacterService(
        registry.characters,
        LocationSystem(registry.locations),
        MoralitySystem(registry.morality),
        RelationshipSystem(registry.relationships),
    )


def test_character_gates_are_satisfiable():
    registry = GameDataRegistry.load()
    unsatisfiable = [
        character["id"]
        for character in registry.characters
        if required_story_tier(character) > MAX_STORY_TIER
    ]
    assert unsatisfiable == [], f"NPCs gated beyond the story ladder: {unsatisfiable}"


def test_every_character_opens_by_the_top_story_tier():
    """Regression guard: legacy ``unlock.min_stage`` gates used to be unsatisfiable.

    ``player.stage`` is pinned at 1 by the cultivation system, so the old gate
    silently locked ~60 NPCs out of sparring, duels, and boons. Gates now resolve
    onto the story ladder, so a fully progressed wanderer can meet every NPC
    anchored where they live.
    """
    registry = GameDataRegistry.load()
    service = _stub_service(registry)
    player = SimpleNamespace(max_story_tier=MAX_STORY_TIER, relationships={})
    missing = []
    for location in registry.locations:
        available = {brief["id"] for brief in service.get_available_characters(location["id"], player)}
        missing += [npc_id for npc_id in location.get("npc_ids", []) or [] if npc_id not in available]
    assert missing == [], f"NPCs still gated at the top story tier: {sorted(set(missing))}"
