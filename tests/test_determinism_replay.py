"""T.6: a seed plus a recorded action log reproduces an identical run.

The fixtures under ``tests/fixtures/replay_logs/`` are real playthroughs written
by ``tools/playthrough_report.py --record``: a seed, the exact action dicts the
policy sent, and the digest of the state after the last one. Replaying them is
the strongest determinism check the project has -- it covers every system a whole
run touches (cultivation, combat, encounters, travel, quests, the living world),
not just one code path.

A log that stops reproducing means state leaked between runs, a system started
reading an unseeded RNG, or a save/load round trip lost something. Because the
fixtures are data, a regression shows up as a diff rather than as a mystery.

Regenerate after an intentional gameplay change, and say so in the same commit:
    python tools/playthrough_report.py --runs 20 --max-actions 200 --record tests/fixtures/replay_logs
"""

from __future__ import annotations

import json

import pytest

from game.core.game_engine import GameEngine
from replay_harness import REPLAY_LOG_DIR, playthrough_report

report = playthrough_report()

#: T.6 asks for twenty recorded logs.
REQUIRED_LOGS = 20

LOGS = sorted(REPLAY_LOG_DIR.glob("seed_*.json"))


def _load(path):
    return json.loads(path.read_text(encoding="utf-8"))


def _replay(log) -> tuple[str, list[str]]:
    """Play a recorded log on a fresh engine; return the state digest and events."""
    engine = GameEngine.new_game(player_name=str(log.get("player_name", "Sim")), seed=int(log["seed"]))
    events = []
    for action in log["actions"]:
        result = engine.process_action(dict(action))
        events.append(str(result.get("event", "")))
    return report.state_digest(engine.get_game_state()), events


def test_twenty_logs_are_recorded():
    assert len(LOGS) == REQUIRED_LOGS, f"expected {REQUIRED_LOGS} replay logs, found {len(LOGS)}"
    seeds = sorted(_load(path)["seed"] for path in LOGS)
    assert seeds == sorted(set(seeds)), "each log is a distinct seed"


def test_logs_were_recorded_by_the_current_policy():
    stale = [path.name for path in LOGS if _load(path).get("policy") != report.POLICY_VERSION]
    assert stale == [], f"logs recorded by another policy: {stale}"


@pytest.mark.parametrize("path", LOGS, ids=lambda path: path.stem)
def test_recorded_log_replays_to_the_same_state(path):
    log = _load(path)

    digest, events = _replay(log)

    assert events == log["events"], "the run diverged from the recorded event sequence"
    assert digest == log["final_state_sha256"], "state diverged from the recorded run"


def test_replay_is_stable_across_repeats():
    """Replaying twice in one process must not drift either."""
    log = _load(LOGS[0])

    assert _replay(log) == _replay(log)


def test_a_tampered_log_is_detected():
    """The check has to be able to fail, or it proves nothing."""
    log = _load(LOGS[0])
    tampered = dict(log)
    actions = [dict(action) for action in log["actions"]]
    actions[-1] = {"action": "EXPLORE"}
    tampered["actions"] = actions

    digest, _ = _replay(tampered)

    if actions != log["actions"]:
        assert digest != log["final_state_sha256"]
