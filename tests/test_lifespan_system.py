"""Tests for lifespan tracking, ageing, and old-age death."""
from game.core.constants import Action, EventType
from game.core.game_engine import GameEngine
from game.models.player import Player
from game.systems.lifespan_system import LifespanSystem
from game.utils.data_loader import load_json


def _make_system():
    return LifespanSystem(
        load_json("cultivation/essence_gathering_realms.json"),
        load_json("cultivation/cultivation_config.json"),
    )


def test_pre_essence_uses_mortal_base_lifespan():
    system = _make_system()
    player = Player(name="Mortal")

    assert system.current_max_lifespan(player, essence_unlocked=False) == 100


def test_essence_realm_sets_max_lifespan():
    system = _make_system()
    player = Player(name="Cultivator")
    player.cultivation_state.essence.realm_id = "xiantian"

    assert system.current_max_lifespan(player, essence_unlocked=True) == 400


def test_higher_essence_realm_extends_lifespan():
    system = _make_system()
    player = Player(name="Cultivator")
    player.cultivation_state.essence.realm_id = "houtian"
    houtian = system.current_max_lifespan(player, essence_unlocked=True)
    player.cultivation_state.essence.realm_id = "divine_sea"
    divine_sea = system.current_max_lifespan(player, essence_unlocked=True)

    assert divine_sea > houtian


def test_immortal_realm_has_no_max_lifespan():
    system = _make_system()
    player = Player(name="Immortal")
    player.cultivation_state.essence.realm_id = "beyond_divinity"

    assert system.current_max_lifespan(player, essence_unlocked=True) is None


def test_lifespan_passive_bonus_extends_realm_lifespan():
    system = _make_system()
    player = Player(name="Cultivator", lifespan_bonus_years=400)
    player.cultivation_state.essence.realm_id = "xiantian"

    assert system.current_max_lifespan(player, essence_unlocked=True) == 800


def test_lifespan_passive_bonus_extends_mortal_base():
    system = _make_system()
    player = Player(name="Mortal", lifespan_bonus_years=50)

    assert system.current_max_lifespan(player, essence_unlocked=False) == 150


def test_lifespan_passive_bonus_ignored_when_immortal():
    system = _make_system()
    player = Player(name="Immortal", lifespan_bonus_years=999)
    player.cultivation_state.essence.realm_id = "beyond_divinity"

    assert system.current_max_lifespan(player, essence_unlocked=True) is None


def test_lifespan_passive_bonus_raises_lifespan_view_max_years():
    system = _make_system()
    player = Player(name="Cultivator", lifespan_bonus_years=400)
    player.cultivation_state.essence.realm_id = "xiantian"

    view = system.lifespan_view(player, essence_unlocked=True)

    assert view["max_lifespan_years"] == 800


def test_advance_age_uses_configured_time_cost():
    config = load_json("cultivation/cultivation_config.json")
    cost = config["lifespan"]["time_costs"]["train_body"]
    system = _make_system()
    player = Player(name="Ager")
    before = player.age_years

    added = system.advance_age(player, "train_body")

    assert added == cost
    assert player.age_years == round(before + cost, 4)


def test_lifespan_view_reports_elapsed_year_from_spawn():
    system = _make_system()
    player = Player(name="Traveler", age_years=12.0)

    assert system.lifespan_view(player, essence_unlocked=False)["year"] == 0

    player.age_years = 15.5

    assert system.lifespan_view(player, essence_unlocked=False)["year"] == 3


def test_is_expired_when_age_reaches_cap():
    system = _make_system()
    player = Player(name="Old", age_years=100.0)

    assert system.is_expired(player, essence_unlocked=False) is True


def test_immortal_never_expires():
    system = _make_system()
    player = Player(name="Immortal", age_years=1_000_000_000_000.0)
    player.cultivation_state.essence.realm_id = "beyond_divinity"

    assert system.is_expired(player, essence_unlocked=True) is False


def test_lifespan_view_shape():
    system = _make_system()
    player = Player(name="View", age_years=20.0)

    view = system.lifespan_view(player, essence_unlocked=False)

    assert view["age_years"] == 20.0
    assert view["max_lifespan_years"] == 100
    assert view["remaining_years"] == 80.0
    assert view["immortal"] is False
    assert "Age 20" in view["display"]


def test_new_game_starts_at_age_twelve_with_lifespan_view():
    engine = GameEngine.new_game(seed=1)

    state = engine.get_game_state()
    life = state["player"]["lifespan"]

    assert state["player"]["age_years"] == 12.0
    assert life["age_years"] == 12.0
    assert life["max_lifespan_years"] == 100
    assert life["immortal"] is False


def test_training_advances_age():
    engine = GameEngine.new_game(seed=1)
    before = engine.player.age_years

    result = engine.process_action({"action": Action.TRAIN_BODY})

    assert engine.player.age_years > before
    assert result["lifespan"]["age_years"] >= before


def test_reaching_lifespan_cap_ends_the_run():
    engine = GameEngine.new_game(seed=1)
    engine.player.age_years = 99.9

    result = engine.process_action({"action": Action.TRAIN_BODY})

    assert result["event"] == EventType.PLAYER_DIED
    assert result["cause"] == "old_age"
    assert engine.is_running() is False
