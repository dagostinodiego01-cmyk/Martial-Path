"""API.3: a *real* local server accepts state, action, save and load over HTTP.

Everything else in ``test_api_server.py`` calls route functions directly. This
test starts ``uvicorn`` as a genuine subprocess and speaks the client-facing
contract to it, so it also proves the transport FastAPI actually serves:
serialised sessions under concurrency (API.2), 422s for contract violations
(API.1), and the SV.2 autosave firing through the wire.

Skipped when uvicorn/fastapi are not installed.
"""
from __future__ import annotations

import importlib.util
import json
import os
import socket
import subprocess
import sys
import threading
import time
import urllib.error
import urllib.request
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
HAVE_SERVER_DEPS = (
    importlib.util.find_spec("uvicorn") is not None
    and importlib.util.find_spec("fastapi") is not None
)

pytestmark = pytest.mark.skipif(not HAVE_SERVER_DEPS, reason="uvicorn/fastapi not installed")


def _free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return int(sock.getsockname()[1])


def _request(port: int, method: str, path: str, payload=None):
    """Return ``(status, parsed_body)`` for one HTTP call."""
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = urllib.request.Request(
        f"http://127.0.0.1:{port}{path}",
        data=data,
        method=method,
        headers={"Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:  # 4xx/5xx still carry a JSON body
        return exc.code, json.loads(exc.read().decode("utf-8"))


@pytest.fixture(scope="module")
def live_server(tmp_path_factory):
    """Boot the real API server on a loopback port with hermetic saves."""
    save_dir = tmp_path_factory.mktemp("live_saves")
    port = _free_port()
    log_path = save_dir.parent / "uvicorn.log"
    env = dict(os.environ)
    env["MARTIAL_PATH_SAVE_DIR"] = str(save_dir)
    env["PYTHONPATH"] = str(ROOT) + os.pathsep + env.get("PYTHONPATH", "")

    log = open(log_path, "w", encoding="utf-8")
    proc = subprocess.Popen(
        [
            sys.executable, "-m", "uvicorn", "game.api.server:app",
            "--host", "127.0.0.1", "--port", str(port), "--log-level", "error",
        ],
        cwd=str(ROOT),
        env=env,
        stdout=log,
        stderr=subprocess.STDOUT,
        text=True,
    )
    try:
        healthy = False
        for _ in range(150):  # up to ~30s for import + registry load
            if proc.poll() is not None:
                log.close()
                pytest.fail(f"server exited early:\n{log_path.read_text(encoding='utf-8')}")
            try:
                status, body = _request(port, "GET", "/health")
                if status == 200 and body == {"status": "ok"}:
                    healthy = True
                    break
            except (urllib.error.URLError, ConnectionError, OSError, ValueError):
                time.sleep(0.2)
        if not healthy:
            pytest.fail(f"server never became healthy:\n{log_path.read_text(encoding='utf-8')}")
        yield port
    finally:
        proc.terminate()
        try:
            proc.wait(timeout=10)
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait(timeout=10)
        log.close()


def test_live_state_shape(live_server):
    status, state = _request(live_server, "GET", "/state")
    assert status == 200
    for key in ("player", "mode", "running", "in_combat", "quests"):
        assert key in state


def test_live_action_round_trip(live_server):
    status, state = _request(live_server, "POST", "/new-game", {"seed": 1})
    assert status == 200 and state["player"]["name"] == "Daoist"

    status, result = _request(live_server, "POST", "/action", {"action": "TRAIN"})
    assert status == 200
    assert result["event"] == "TRAIN_RESULT"


def test_live_save_and_load_round_trip(live_server):
    status, _ = _request(live_server, "POST", "/new-game", {"seed": 1})
    assert status == 200
    status, initial = _request(live_server, "GET", "/state")
    assert status == 200

    status, saved = _request(live_server, "POST", "/save", {"slot": "live"})
    assert status == 200 and saved["success"] is True

    # Advance the run, then restore it over HTTP.
    status, trained = _request(live_server, "POST", "/action", {"action": "TRAIN"})
    assert status == 200 and trained["event"] == "TRAIN_RESULT"
    status, advanced = _request(live_server, "GET", "/state")
    assert advanced["player"]["progress"] > initial["player"]["progress"]

    status, loaded = _request(live_server, "POST", "/load", {"slot": "live"})
    assert status == 200 and loaded["success"] is True

    status, restored = _request(live_server, "GET", "/state")
    assert status == 200
    assert restored["player"]["progress"] == initial["player"]["progress"]

    status, listing = _request(live_server, "GET", "/saves")
    assert status == 200
    assert any(entry["slot"] == "live" for entry in listing["saves"])


def test_live_contract_violations_return_422(live_server):
    status, body = _request(live_server, "POST", "/action", {"action": "STATUS", "itemId": "typo"})
    assert status == 422, body

    status, body = _request(live_server, "POST", "/action", {})
    assert status == 422, body

    status, body = _request(live_server, "POST", "/action", {"action": 5})
    assert status == 422, body


def test_live_concurrent_mutations_never_error(live_server):
    """API.2 over the wire: a burst of parallel mutations must all be 2xx."""
    _request(live_server, "POST", "/new-game", {"seed": 1})
    statuses = []
    lock = threading.Lock()

    def hammer(method, path, payload):
        for _ in range(4):
            status, _body = _request(live_server, method, path, payload)
            with lock:
                statuses.append(status)

    threads = [
        threading.Thread(target=hammer, args=("POST", "/action", {"action": "TRAIN"})),
        threading.Thread(target=hammer, args=("POST", "/action", {"action": "STATUS"})),
        threading.Thread(target=hammer, args=("POST", "/save", {"slot": "race"})),
        threading.Thread(target=hammer, args=("GET", "/state", None)),
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=60)

    assert len(statuses) == 16
    assert all(200 <= status < 300 for status in statuses), statuses

    status, state = _request(live_server, "GET", "/state")
    assert status == 200 and "player" in state
