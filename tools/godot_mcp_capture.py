"""Prove MCP access: run the project, capture the game framebuffer, stop it."""
import base64
import json
import subprocess
import threading
import time
from pathlib import Path

CMD = r"C:\Users\Diego\AppData\Roaming\uv\python\cpython-3.14-windows-x86_64-none\pythonw.exe"
SHIM = ("import subprocess,sys; raise SystemExit(subprocess.call(sys.argv[1:], "
        "stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, "
        "creationflags=0x08000000))")
UVX = r"C:\Users\Diego\.local\bin\uvx.exe"

ARGS = [CMD, "-c", SHIM, UVX, "--link-mode", "copy", "--from", "godot-ai==3.2.5",
        "godot-ai", "attach", "--port", "8000", "--ws-port", "9500"]

proc = subprocess.Popen(ARGS, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL, text=True, encoding="utf-8")

lock = threading.Lock()
responses = {}
NEXT = [1]


def reader():
    for line in proc.stdout:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(msg, dict) and "id" in msg:
            with lock:
                responses[msg["id"]] = msg


threading.Thread(target=reader, daemon=True).start()


def send(obj):
    proc.stdin.write(json.dumps(obj) + "\n")
    proc.stdin.flush()


def wait_for(req_id, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        with lock:
            if req_id in responses:
                return responses[req_id]
        time.sleep(0.1)
    raise TimeoutError("no response for request %s" % req_id)


def request(method, params=None, timeout=90):
    i = NEXT[0]
    NEXT[0] += 1
    req = {"jsonrpc": "2.0", "id": i, "method": method}
    if params is not None:
        req["params"] = params
    send(req)
    return wait_for(i, timeout)


def tool(name, arguments, timeout=90):
    res = request("tools/call", {"name": name, "arguments": arguments},
                  timeout=timeout)
    return res.get("result", {})


request("initialize", {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "freebuff-probe", "version": "1.0"},
}, timeout=90)
send({"jsonrpc": "2.0", "method": "notifications/initialized"})

tools = request("tools/list", {}, timeout=30)
tnames = {t["name"]: t for t in tools["result"]["tools"]}

# Find the run/manage tools and their schemas
for nm in sorted(tnames):
    d = (tnames[nm].get("description") or "").strip().splitlines()
    print("TOOL", nm, "-", (d[0] if d else "")[:100])

run_tool = next((n for n in tnames if "run" in n), None)
stop_tool = next((n for n in tnames if n in ("game_manage", "game_stop", "project_stop")), None)
print("run_tool:", run_tool, "| stop_tool:", stop_tool)
if run_tool:
    print("run schema:", json.dumps((tnames[run_tool].get("inputSchema") or {}).get("properties", {}))[:600])
if stop_tool:
    print("stop schema:", json.dumps((tnames[stop_tool].get("inputSchema") or {}).get("properties", {}))[:600])

out = Path("graphify-out")
try:
    r = tool(run_tool, {}, timeout=60)
    print("RUN:", json.dumps(r)[:500])
    time.sleep(8)  # let the game boot and render the main menu

    for attempt in range(3):
        res = tool("editor_screenshot", {"source": "game", "include_image": True,
                                         "max_resolution": 0}, timeout=120)
        if res.get("isError"):
            print("SHOT ERROR:", res.get("content", [{}])[0].get("text", "")[:300])
            time.sleep(3)
            continue
        saved = False
        for item in res.get("content", []):
            if item.get("type") == "image":
                data = base64.b64decode(item["data"])
                p = out / "godot_game_capture.png"
                p.write_bytes(data)
                print("SAVED game frame %s bytes -> %s" % (format(len(data), ","), p))
                saved = True
            elif item.get("type") == "text":
                print("SHOT META:", item.get("text", "")[:300])
        if saved:
            break
finally:
    if stop_tool:
        try:
            r = tool(stop_tool, {"action": "stop"}, timeout=30)
            print("STOP:", json.dumps(r)[:300])
        except Exception as e:
            print("stop failed:", e)
    try:
        proc.stdin.close()
        proc.wait(timeout=10)
    except Exception:
        proc.kill()
