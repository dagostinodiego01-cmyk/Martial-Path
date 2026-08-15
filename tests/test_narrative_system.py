"""Tests for the procedural narrative engine (ROADMAP A.1-A.3)."""
from game.core.game_engine import GameEngine
from game.data.registry import GameDataRegistry
from game.systems.narrative_system import NarrativeSystem
from game.utils.rng import RNG


def _templates():
    registry = GameDataRegistry.load()
    return registry.narrative_templates


def _full_context() -> dict:
    return {
        "realm_rank": 0,
        "morality": "neutral",
        "reputation": 0,
        "comprehension": 10,
        "season": "Spring",
        "name": "Forest",
        "enemy": "Wolf",
        "item": "Pill",
        "destination": "Village",
        "realm": "Mortal",
        "cause": "old age",
        "age": 100,
        "tier": "neutral",
        "rarity": "common",
        "technique": "Iron Fist",
        "dao": "Sword Dao",
    }


# -- A.1 template engine ------------------------------------------------
def test_slots_filled_and_unknown_slots_left_verbatim():
    system = NarrativeSystem(
        {"v": {"variables": ["name"], "variants": [{"weight": 1, "template": "Hello {name}, {missing} stays."}]}},
        RNG(1),
        seed=1,
    )
    assert system.render("v", {"name": "Zhu Yan"}) == "Hello Zhu Yan, {missing} stays."


def test_when_clause_gates_variant():
    system = NarrativeSystem(
        {
            "greet": {
                "variables": [],
                "variants": [
                    {"weight": 1, "template": "summer-greeting", "when": {"field": "season", "op": "eq", "value": "Summer"}},
                    {"weight": 1, "template": "fallback-greeting"},
                ],
            }
        },
        RNG(1),
        seed=1,
    )
    assert system.render("greet", {"season": "Summer"}) == "summer-greeting"
    assert system.render("greet", {"season": "Winter"}) == "fallback-greeting"


def test_weighted_pool_produces_variety():
    system = NarrativeSystem(
        {"v": {"variables": [], "variants": [{"weight": 1, "template": "a"}, {"weight": 1, "template": "b"}]}},
        RNG(1),
        seed=1,
    )
    outputs = {system.render("v") for _ in range(20)}
    assert outputs >= {"a", "b"}


def test_unknown_verb_renders_empty():
    system = NarrativeSystem({}, RNG(1), seed=1)
    assert system.render("nope", {}) == ""
    assert system.variant_count("nope") == 0


# -- A.3 seeded determinism ---------------------------------------------
def test_seeded_determinism_and_variety_over_1000_seeds():
    templates = _templates()
    verbs = sorted(templates)
    context = _full_context()
    variety = {verb: set() for verb in verbs}
    for seed in range(1000):
        first = NarrativeSystem(templates, RNG(seed), seed=seed)
        second = NarrativeSystem(templates, RNG(seed), seed=seed)
        for verb in verbs:
            out_a = first.render(verb, context)
            out_b = second.render(verb, context)
            assert out_a == out_b, f"seed {seed} verb {verb}: {out_a!r} != {out_b!r}"
            variety[verb].add(out_a)
    # Different seeds must produce measurably different prose for at least one verb.
    assert any(len(outputs) > 1 for outputs in variety.values())


def test_render_stable_is_deterministic_per_key_and_seed():
    templates = {"d": {"variables": ["name"], "variants": [{"weight": 1, "template": "A {name}"}, {"weight": 1, "template": "B {name}"}]}}
    first = NarrativeSystem(templates, RNG(5), seed=5)
    second = NarrativeSystem(templates, RNG(5), seed=5)
    assert first.render_stable("d", {"name": "x"}, "key") == second.render_stable("d", {"name": "x"}, "key")
    # Stable within a run: the same key yields the same sentence every time.
    assert first.render_stable("d", {"name": "x"}, "key") == first.render_stable("d", {"name": "x"}, "key")


# -- A.2 description generators -----------------------------------------
def test_description_generators_fill_entity_names():
    system = NarrativeSystem(_templates(), RNG(1), seed=1)
    location = system.describe_location({"id": "outer_forest", "name": "Outer Forest", "danger": "Low"}, "Spring")
    assert "Outer Forest" in location
    npc = system.describe_npc("Zhu Yan", "friendly", "neutral")
    assert "Zhu Yan" in npc
    item = system.describe_item("Healing Pill", "common")
    assert "Healing Pill" in item
    technique = system.describe_technique("Iron Fist", "Sword Dao")
    assert "Iron Fist" in technique


def test_describe_npc_varies_by_relationship_and_morality():
    system = NarrativeSystem(_templates(), RNG(1), seed=1)
    texts = {
        system.describe_npc("Zhu Yan", tier, morality)
        for tier in ("hostile", "neutral", "friendly", "trusted")
        for morality in ("demonic", "neutral", "righteous")
    }
    assert len(texts) > 1


def test_describe_breakthrough_and_death_return_prose():
    system = NarrativeSystem(_templates(), RNG(1), seed=1)
    assert system.describe_breakthrough(True, "Strength Training", "Spring")
    assert system.describe_breakthrough(False, "", "Winter")
    death = system.describe_death("your lifespan runs dry", 137, "Autumn")
    assert "137" in death


# -- engine wiring ------------------------------------------------------
def test_engine_surfaces_narrative_in_state_and_describe_methods():
    engine = GameEngine.new_game(seed=1)
    state = engine.get_game_state()
    assert state["location"].get("narrative")
    assert engine.describe_technique("iron_fist")
    assert engine.describe_item("healing_pill")
    assert engine.describe_npc("zhu_yan")


def test_engine_narrative_is_seed_deterministic():
    a = GameEngine.new_game(seed=7)
    b = GameEngine.new_game(seed=7)
    assert a.get_game_state()["location"]["narrative"] == b.get_game_state()["location"]["narrative"]


# -- data coverage ------------------------------------------------------
def test_core_verbs_have_at_least_three_variants():
    system = NarrativeSystem(_templates(), RNG(1), seed=1)
    core = (
        "train_body", "train_essence", "rest", "meditate",
        "explore_nothing", "explore_combat", "explore_loot", "explore_special",
        "travel", "attack", "breakthrough_success", "breakthrough_failure", "death",
    )
    for verb in core:
        assert system.variant_count(verb) >= 3, verb
