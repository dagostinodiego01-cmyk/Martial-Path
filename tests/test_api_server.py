"""Smoke tests for the HTTP API layer.

These call the route functions directly (the engine returns plain dicts), so no
running server or extra HTTP client dependency is required.
"""
from game.api import server
from game.api.server import ActionRequest, NewGameRequest, SaveRequest
from game.core.constants import EventType
from game.services.save_service import SaveService


def test_health_ok():
    assert server.health() == {"status": "ok"}


def test_state_has_player_and_running():
    state = server.get_state()
    assert "player" in state
    assert state["running"] is True
    assert "mode" in state
    assert "in_combat" in state


def test_action_train_returns_train_result():
    server.new_game(NewGameRequest(seed=1))
    result = server.process_action(ActionRequest(action="TRAIN"))
    assert result["event"] == EventType.TRAIN_RESULT


def test_action_excludes_none_fields():
    # A bare TRAIN command must not carry item_id/skill_id keys into the engine.
    server.new_game(NewGameRequest(seed=1))
    result = server.process_action(ActionRequest(action="STATUS"))
    assert result["event"] == EventType.STATUS


def test_action_buy_accepts_quantity_field():
    request = ActionRequest(action="BUY_ITEM", item_id="qi_pill", quantity=2)
    assert request.model_dump(exclude_none=True) == {"action": "BUY_ITEM", "item_id": "qi_pill", "quantity": 2}


def test_action_request_carries_every_dispatch_argument():
    """Every argument key the engine's dispatch table reads must survive the model.

    A field missing from ActionRequest is silently dropped by pydantic, so the
    engine receives an empty argument (the "talent elixir upgrade always errors"
    bug: UPGRADE_TALENT lost ``track``/``target_id`` in transit).
    """
    args = {
        "item_id": "x", "shop_id": "s", "quantity": 1, "skill_id": "k",
        "method_id": "m", "location_id": "l", "slot": "a", "character_id": "c",
        "dialogue_choice": "d", "choice_id": "ch", "track": "martial",
        "target_id": "t", "sect_id": "sec", "trainer_id": "tr", "years": 3,
        "recipe_id": "r", "dao_id": "dao", "unlock_id": "u", "rumor_id": "ru",
        "payload": "p", "raw": "raw text",
    }
    dumped = ActionRequest(action="STATUS", **args).model_dump(exclude_none=True)
    for key, value in args.items():
        assert dumped.get(key) == value, f"ActionRequest dropped field {key!r}"


def test_action_upgrade_talent_reaches_engine_end_to_end():
    """UPGRADE_TALENT through the API layer must carry track/target_id intact."""
    server.new_game(NewGameRequest(seed=1))
    server.engine.player.inventory["talent_refining_elixir"] = 3
    current = server.engine.player.martial_talent_id

    view = server.process_action(ActionRequest(action="TALENTS"))
    options = view.get("martial_upgrades", [])
    assert options, "martial talent must have an upgrade path"

    result = server.process_action(
        ActionRequest(action="UPGRADE_TALENT", track="martial", target_id=options[0]["target_id"])
    )
    assert result["event"] != EventType.ERROR, f"upgrade failed: {result.get('reason')}"
    assert result["event"] == EventType.TALENT_UPGRADED
    assert server.engine.player.martial_talent_id == options[0]["target_id"]
    assert server.engine.player.inventory.get("talent_refining_elixir", 0) == 2


def test_new_game_resets_state():
    server.process_action(ActionRequest(action="TRAIN"))
    state = server.new_game(NewGameRequest(player_name="Tester", seed=1))
    assert state["player"]["name"] == "Tester"
    assert state["player"]["progress"] == 0.0
    assert state["awaiting_fate_acceptance"] is False
    assert state["player"]["martial_talent_id"]
    assert state["player"]["body_talent_id"]


def test_meta_endpoint_returns_meta_shape():
    server.new_game(NewGameRequest(seed=1))
    meta = server.get_meta()
    assert "ancestral_memory" in meta
    assert "chronicle" in meta
    assert "origins" in meta
    assert isinstance(meta["origins"], list)
    assert any(o["id"] == "orphan" for o in meta["origins"])


def test_new_game_accepts_origin_and_hardcore():
    state = server.new_game(NewGameRequest(seed=1, origin_id="orphan", hardcore=False))
    assert state["player"]["origin_id"] == "orphan"
    assert server.engine._hardcore is False


def test_save_and_load_endpoints(tmp_path):
    server.new_game(NewGameRequest(seed=1))
    server.engine.saves = SaveService(tmp_path)
    server.engine.player.gold = 77

    saved = server.save_game(SaveRequest(slot="apitest"))
    assert saved["success"] is True

    server.engine.player.gold = 0
    loaded = server.load_game(SaveRequest(slot="apitest"))
    assert loaded["success"] is True
    assert server.engine.player.gold == 77

    listing = server.list_saves()
    assert any(s["slot"] == "apitest" for s in listing["saves"])
