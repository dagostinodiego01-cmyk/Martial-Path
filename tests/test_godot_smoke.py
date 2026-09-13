"""Runs the Godot client smoke check as part of the Python gate (T.5).

``frontend-godot/tests/check_smoke.gd`` drives the client shell: a refresh with
``enemy: null`` and ``encounter: null``, a combat refresh, an encounter refresh,
every tab open/closed, and a render of every result payload a real run produced.
This wrapper writes that payload from an actual seeded playthrough, invokes the
script, and fails on any client-side error.

The payload half runs everywhere (it needs only the engine), so a machine without
Godot still proves the fixtures are real; the Godot half skips with a message
explaining how to enable it (``GODOT_BIN``).
"""

from __future__ import annotations

import json
import subprocess

import pytest

from replay_harness import GODOT_PROJECT, find_godot, playthrough_report

report = playthrough_report()

#: A scene, not a `-s` script: a script run with `-s` has no autoload context, so
#: `MainController.gd` (which reads the `Profile` autoload) cannot compile there
#: and the check would silently test nothing.
SMOKE_SCENE = "res://tests/SmokeRunner.tscn"
TIMEOUT_SECONDS = 300

#: Enough distinct events that the event table is genuinely exercised.
MIN_DISTINCT_EVENTS = 10

#: Seeds tried until one run yields all three captured states.
SEEDS = (1, 2, 3, 4, 5, 6)


def _payload() -> dict:
    """Capture the smoke payload from the first seed that has all three states."""
    for seed in SEEDS:
        captured = report.collect_render_payloads(seed=seed, max_actions=120)
        if {"explore", "combat", "encounter"} <= set(captured["states"]):
            return captured
    pytest.fail("no seed produced all three render states; the policy or the engine changed shape")


# -- the payload itself is real engine output ----------------------------
def test_payload_carries_the_null_keys_the_client_must_survive():
    payload = _payload()
    explore = payload["states"]["explore"]

    assert explore["enemy"] is None
    assert explore["encounter"] is None
    assert "player" in explore and explore["location"]["id"]


def test_payload_covers_combat_and_encounters_and_many_events():
    payload = _payload()

    assert payload["states"]["combat"]["enemy"] is not None
    assert payload["states"]["encounter"]["encounter"] is not None
    distinct = {str(result.get("event", "")) for result in payload["events"]}
    assert len(distinct) >= MIN_DISTINCT_EVENTS, f"only {len(distinct)} distinct event(s): {sorted(distinct)}"
    assert "" not in distinct, "every captured payload must name its event"


def test_payload_is_json_serialisable():
    """It is handed to Godot as a file, so it has to survive the round trip."""
    payload = _payload()

    text = json.dumps(payload, default=str)
    assert json.loads(text)["states"]["explore"]["enemy"] is None


# -- the Godot half ------------------------------------------------------
def test_client_shell_survives_a_real_run(tmp_path):
    godot = find_godot()
    if godot is None:
        pytest.skip("no Godot binary found; set GODOT_BIN to run the client smoke check")

    payload_path = tmp_path / "smoke_payload.json"
    payload_path.write_text(json.dumps(_payload(), default=str), encoding="utf-8")

    result = subprocess.run(
        [godot, "--headless", "--path", str(GODOT_PROJECT), SMOKE_SCENE, "--", str(payload_path)],
        capture_output=True,
        text=True,
        timeout=TIMEOUT_SECONDS,
    )
    output = result.stdout + result.stderr

    assert result.returncode == 0, f"smoke check failed:\n{output}"
    # The per-case OK lines are the proof the checks actually ran: a script that
    # quits early would otherwise look like a quiet success.
    for expected in (
        "OK   explore (enemy null, encounter null)",
        "OK   explore again (refresh is repeatable)",
        "OK   combat (enemy set, encounter null)",
        "OK   encounter (encounter set, enemy null)",
        "OK   tab 0 (Inventory) opened and closed",
        "OK   tab 4 (Techniques) opened and closed",
        "0 failure(s)",
    ):
        assert expected in output, f"{expected!r} never reported:\n{output}"
    # Coverage floor: a run that rendered almost nothing proves almost nothing.
    assert "rendered 0 event payload(s)" not in output, output
