"""SV.5: a save loaded in a *fresh process* continues the run deterministically.

The recorded replay logs (``tests/fixtures/replay_logs/``) are real playthroughs
with the exact action sequence and the final state digest. This test proves the
M1 persistence contract:

1. replay a log to get the original run's full event sequence and digest;
2. play the prefix on engine A, save at a safe point;
3. load that save in a **separate Python process** built from an unrelated
   seed, play the remaining actions there, and compare event-by-event and
   digest-to-digest against the original run.

A failure here is exactly the bug M1 exists to fix: RNG streams and the run
seed were not persisted, so a fresh process diverged after load.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

from game.core.game_engine import GameEngine
from game.services.save_service import SaveService
from replay_harness import REPLAY_LOG_DIR, playthrough_report

report = playthrough_report()
ROOT = Path(__file__).resolve().parents[1]
CHILD = ROOT / "tests" / "save_continuation_child.py"

#: Enough actions for the streams to have visibly diverged if anything is off.
MIN_PREFIX = 30
#: Two logs keep the evidence multi-seed without blowing the suite budget.
LOG_NAMES = ["seed_1.json", "seed_2.json"]


def _load(name: str) -> dict:
    return json.loads((REPLAY_LOG_DIR / name).read_text(encoding="utf-8"))


def _drive(engine: GameEngine, actions: list) -> list:
    events = []
    for action in actions:
        events.append(str(engine.process_action(dict(action)).get("event", "")))
    return events


def _play_prefix_to_safe_point(engine: GameEngine, actions: list) -> int:
    """Play actions until a safe point at/after the minimum prefix.

    Returns how many actions were played. Saves are only legal at safe points,
    so the split index is chosen by policy, not by arithmetic.
    """
    for index, action in enumerate(actions, start=1):
        engine.process_action(dict(action))
        if index >= MIN_PREFIX and engine.at_safe_point():
            return index
    raise AssertionError("the log never reached a safe point after the minimum prefix")


@pytest.mark.parametrize("name", LOG_NAMES)
def test_fresh_process_continues_the_saved_run_bit_for_bit(name, tmp_path):
    log = _load(name)
    actions = log["actions"]
    assert len(actions) > MIN_PREFIX + 5, "log too short to split"

    # 1. The original run, for the expected tail and final digest.
    original = GameEngine.new_game(player_name=str(log.get("player_name", "Sim")), seed=int(log["seed"]))
    expected_events = _drive(original, actions)
    expected_digest = report.state_digest(original.get_game_state())
    assert expected_digest == log["final_state_sha256"], "harness disagrees with the recorded log"

    # 2. Save mid-run (at a safe point) from a second, identical run.
    first = GameEngine.new_game(player_name=str(log.get("player_name", "Sim")), seed=int(log["seed"]))
    first.saves = SaveService(tmp_path)
    split = _play_prefix_to_safe_point(first, actions)
    assert first.save_game("cont")["success"] is True

    # 3. A brand-new process loads the save and plays the remainder.
    actions_path = tmp_path / "remaining.json"
    out_path = tmp_path / "child_result.json"
    actions_path.write_text(json.dumps({"actions": actions[split:]}), encoding="utf-8")
    proc = subprocess.run(
        [sys.executable, str(CHILD), str(tmp_path), "cont", str(actions_path), str(out_path)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=180,
    )
    assert proc.returncode == 0, f"child failed:\n{proc.stdout}\n{proc.stderr}"
    result = json.loads(out_path.read_text(encoding="utf-8"))

    assert result["events"] == expected_events[split:], (
        f"the fresh process diverged from the original run after action {split}"
    )
    assert result["digest"] == expected_digest, "final state digest diverged after a fresh-process load"


def test_in_process_load_continues_and_a_tampered_tail_is_detected(tmp_path):
    """In-process continuation, plus a negative control that can actually fail."""
    log = _load(LOG_NAMES[0])
    actions = log["actions"]

    original = GameEngine.new_game(player_name=str(log.get("player_name", "Sim")), seed=int(log["seed"]))
    expected_events = _drive(original, actions)
    expected_digest = report.state_digest(original.get_game_state())

    first = GameEngine.new_game(player_name=str(log.get("player_name", "Sim")), seed=int(log["seed"]))
    first.saves = SaveService(tmp_path)
    split = _play_prefix_to_safe_point(first, actions)
    assert first.save_game("cont")["success"] is True

    # Fresh engine, unrelated seed, loads the save and finishes the run.
    second = GameEngine.new_game(player_name="Reloaded", seed=424242)
    second.saves = SaveService(tmp_path)
    assert second.load_game("cont")["success"] is True
    events = _drive(second, actions[split:])
    assert events == expected_events[split:]
    assert report.state_digest(second.get_game_state()) == expected_digest

    # Negative control: if the continuation drifts at all, the comparison fails.
    third = GameEngine.new_game(player_name="Tampered", seed=242424)
    third.saves = SaveService(tmp_path)
    assert third.load_game("cont")["success"] is True
    tampered = [dict(action) for action in actions[split:]]
    tampered[-1] = {"action": "TRAIN"} if tampered[-1].get("action") != "TRAIN" else {"action": "REST"}
    tampered_events = _drive(third, tampered)
    tampered_digest = report.state_digest(third.get_game_state())
    assert tampered_events != expected_events[split:] or tampered_digest != expected_digest
