"""Smoke tests for the HTTP API layer.

These call the route functions directly (the engine returns plain dicts), so no
running server or extra HTTP client dependency is required. The *live* HTTP
path (API.3) is covered separately by ``tests/test_api_live_http.py``.

Covers the M1 transport gates: the versioned action contract (API.1) and
single-session ownership (API.2), plus the SV.2 autosave wiring.
"""
import json
import threading
import time
from pathlib import Path

import pytest
from pydantic import ValidationError

from game.api import server
from game.api.server import ActionRequest, NewGameRequest, SaveRequest
from game.core.constants import EventType
from game.services.save_service import SAVE_VERSION, SaveService

ROOT = Path(__file__).resolve().parents[1]


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
        "dialogue_choice": "d", "choice_id": "ch", "foe_id": "f", "track": "martial",
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


def _explore_until_encounter(seed: int = 5, tries: int = 40) -> dict:
    """Explore until the land asks a question, returning the ENCOUNTER payload."""
    server.new_game(NewGameRequest(seed=seed, hardcore=False))
    for _ in range(tries):
        result = server.process_action(ActionRequest(action="EXPLORE"))
        if result["event"] == EventType.ENCOUNTER:
            return result
    raise AssertionError("no encounter rolled in 40 explores")


def test_explore_returns_a_choosable_encounter_over_the_api():
    encounter = _explore_until_encounter()
    assert encounter["kind"] in {"combat", "loot", "special", "hazard"}
    assert encounter["title"] and encounter["narrative"]
    options = encounter["options"]
    assert options, "an encounter must offer at least one choice"
    for option in options:
        assert option["choice_id"] and option["label"] and option["hint"]
        assert isinstance(option["available"], bool)
        # A withheld option must say why: the UI shows that reason verbatim.
        assert option["available"] or option.get("reason")


def test_other_actions_are_refused_until_the_choice_is_made():
    _explore_until_encounter()
    blocked = server.process_action(ActionRequest(action="REST"))
    assert blocked["event"] == EventType.ERROR
    assert blocked["reason"] == "INVALID_IN_ENCOUNTER"
    state = server.get_state()
    assert state["in_encounter"] is True and state["encounter"] is not None


def test_a_choice_resolves_and_clears_the_pending_encounter():
    encounter = _explore_until_encounter()
    choice_id = next(o["choice_id"] for o in encounter["options"] if o["available"])
    result = server.process_action(ActionRequest(action="ENCOUNTER_CHOICE", choice_id=choice_id))
    assert result["event"] in {EventType.ENCOUNTER_RESULT, EventType.COMBAT, EventType.ENCOUNTER}
    if result["event"] != EventType.ENCOUNTER:
        assert server.get_state()["in_encounter"] is False


def test_withheld_choice_reports_the_engine_reason():
    encounter = _explore_until_encounter(seed=77, tries=60)
    withheld = [o for o in encounter["options"] if not o["available"]]
    if not withheld:
        return  # this roll had no withheld option; the shape is covered above
    refused = server.process_action(ActionRequest(action="ENCOUNTER_CHOICE", choice_id=withheld[0]["choice_id"]))
    assert refused["event"] == EventType.ERROR
    assert refused["reason"] == withheld[0].get("reason_code", "CHOICE_UNAVAILABLE")


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


# -- API.1: the versioned action contract --------------------------------


def _type_name(annotation) -> str:
    """Mirror of the fixture generator's type naming, kept next to the check."""
    import typing

    origin = typing.get_origin(annotation)
    if origin is typing.Union:
        args = [a for a in typing.get_args(annotation) if a is not type(None)]
        return f"{_type_name(args[0]) if args else 'any'}|null"
    return {str: "str", int: "int", float: "float", bool: "bool"}.get(annotation, "any")


def test_action_contract_matches_the_shared_fixture():
    """ActionRequest and game/api/action_contract.json must agree exactly.

    The fixture is the contract the Godot client is checked against too: a
    field added to the model without regenerating it (or vice versa) fails
    here rather than silently dropping a command in transit.
    """
    fixture = json.loads((ROOT / "game" / "api" / "action_contract.json").read_text(encoding="utf-8"))
    model = ActionRequest.model_fields

    assert set(fixture["fields"]) == set(model)
    for name, spec in fixture["fields"].items():
        field = model[name]
        assert spec["required"] == field.is_required(), name
        assert spec["type"] == _type_name(field.annotation), name
    assert fixture["errors"] == {"missing_action": 422, "unknown_field": 422, "wrong_type": 422}


def test_unknown_action_field_is_rejected_not_dropped():
    """A typo'd key (itemId vs item_id) must not silently no-op."""
    with pytest.raises(ValidationError):
        ActionRequest(action="STATUS", itemId="qi_pill")


def test_missing_action_is_rejected():
    with pytest.raises(ValidationError):
        ActionRequest()


# -- API.2: single-session ownership -------------------------------------


def test_mutating_endpoint_blocks_while_the_session_lock_is_held():
    """A second mutation cannot interleave while one is in flight."""
    server.new_game(NewGameRequest(seed=1))
    finished = threading.Event()

    def mutate():
        server.process_action(ActionRequest(action="TRAIN"))
        finished.set()

    with server._session_lock:
        worker = threading.Thread(target=mutate)
        worker.start()
        # The worker must be parked on the lock, not racing the mutation.
        assert not finished.wait(timeout=0.3), "the lock did not serialise a concurrent mutation"

    worker.join(timeout=10)
    assert finished.is_set(), "the queued mutation never completed after the lock was released"


def test_concurrent_mutations_all_complete_without_interleaving_errors(tmp_path):
    """A burst of mixed actions/saves/loads must all succeed under the lock."""
    server.new_game(NewGameRequest(seed=1))
    server.engine.saves = SaveService(tmp_path)
    assert server.save_game(SaveRequest(slot="race"))["success"] is True

    errors = []

    def hammer(action):
        try:
            for _ in range(5):
                if action == "TRAIN":
                    result = server.process_action(ActionRequest(action="TRAIN"))
                    if result.get("event") not in (EventType.TRAIN_RESULT, EventType.ERROR):
                        errors.append(result)
                elif action == "SAVE":
                    if not server.save_game(SaveRequest(slot="race"))["success"]:
                        errors.append("save failed")
                else:
                    if not server.load_game(SaveRequest(slot="race"))["success"]:
                        errors.append("load failed")
        except Exception as exc:  # noqa: BLE001 - the test's job is to catch races
            errors.append(repr(exc))

    threads = [
        threading.Thread(target=hammer, args=(action,))
        for action in ("TRAIN", "TRAIN", "SAVE", "LOAD")
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert errors == []
    assert server.get_state()["player"]["name"]


# -- SV.2: the API's autosave wiring -------------------------------------


def test_successful_turn_autosaves_at_the_safe_point(tmp_path):
    server.new_game(NewGameRequest(seed=1))
    server.engine.saves = SaveService(tmp_path)

    result = server.process_action(ActionRequest(action="TRAIN"))

    assert result["event"] == EventType.TRAIN_RESULT
    autosave = tmp_path / "autosave.json"
    assert autosave.exists(), "a successful turn at a safe point must autosave"
    assert json.loads(autosave.read_text(encoding="utf-8"))["version"] == SAVE_VERSION


def test_autosave_is_skipped_while_an_encounter_is_pending(tmp_path):
    server.new_game(NewGameRequest(seed=5, hardcore=False))
    server.engine.saves = SaveService(tmp_path)
    autosave = tmp_path / "autosave.json"

    for _ in range(60):
        autosave.unlink(missing_ok=True)
        result = server.process_action(ActionRequest(action="EXPLORE"))
        if result.get("event") == EventType.ENCOUNTER:
            # The turn that opened the scene was a successful action, but the
            # scene makes it unsafe: no autosave may fire.
            assert not autosave.exists(), "autosave fired mid-encounter"
            return
        if server.engine.at_safe_point():
            assert autosave.exists(), "a resolved turn at a safe point must autosave"
        else:
            assert not autosave.exists(), "autosave fired outside a safe point"
    raise AssertionError("no encounter rolled in 60 explores")


def test_refused_action_does_not_autosave(tmp_path):
    server.new_game(NewGameRequest(seed=1))
    server.engine.saves = SaveService(tmp_path)

    result = server.process_action(ActionRequest(action="BUY_ITEM"))  # refused: no shop here

    assert result["event"] == EventType.ERROR
    assert not (tmp_path / "autosave.json").exists(), "a refusal did not advance the turn"
