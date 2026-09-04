"""Full click-through UI audit for Martial Path via the godot-ai MCP server.

Menu -> new game -> every tab -> refine popup -> real brew (verified through
the backend) -> travel/world-map/talents/dao/settings popups. Screenshots land
in tools/captures/.

Coordinate handling: the game helper injects raw mouse positions, which under
canvas_items stretch are WINDOW coordinates, while get_ui_elements reports
CANVAS coordinates. The driver derives the window/canvas scale empirically
(canvas extents from the UI dump, window size from the screenshot PNG header),
then VERIFIES the mapping with a real click before proceeding.
"""
import base64
import json
import struct
import subprocess
import threading
import time
import urllib.request
from pathlib import Path

CMD = r"C:\Users\Diego\AppData\Roaming\uv\python\cpython-3.14-windows-x86_64-none\pythonw.exe"
SHIM = ("import subprocess,sys; raise SystemExit(subprocess.call(sys.argv[1:], "
        "stdin=sys.stdin, stdout=sys.stdout, stderr=sys.stderr, "
        "creationflags=0x08000000))")
UVX = r"C:\Users\Diego\.local\bin\uvx.exe"
ARGS = [CMD, "-c", SHIM, UVX, "--link-mode", "copy", "--from", "godot-ai==3.2.5",
        "godot-ai", "attach", "--port", "8000", "--ws-port", "9500"]

OUT = Path("tools/captures")
OUT.mkdir(parents=True, exist_ok=True)

proc = subprocess.Popen(ARGS, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                        stderr=subprocess.DEVNULL, text=True, encoding="utf-8")
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
            responses[msg["id"]] = msg


threading.Thread(target=reader, daemon=True).start()


def send(obj):
    proc.stdin.write(json.dumps(obj) + "\n")
    proc.stdin.flush()


def wait_for(req_id, timeout):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if req_id in responses:
            return responses[req_id]
        time.sleep(0.1)
    raise TimeoutError("no response")


def request(method, params=None, timeout=120):
    i = NEXT[0]
    NEXT[0] += 1
    req = {"jsonrpc": "2.0", "id": i, "method": method}
    if params is not None:
        req["params"] = params
    send(req)
    return wait_for(i, timeout)


def tool(name, arguments, timeout=120):
    res = request("tools/call", {"name": name, "arguments": arguments}, timeout=timeout)
    result = res.get("result", {})
    if result.get("isError"):
        return {"__error__": "\n".join(i.get("text", "") for i in result.get("content", []) if i.get("type") == "text")}
    return result


def text_of(result):
    if isinstance(result, dict) and "__error__" in result:
        return result["__error__"]
    return "\n".join(i.get("text", "") for i in result.get("content", []) if i.get("type") == "text")


def shot(path):
    res = tool("editor_screenshot", {"source": "game", "include_image": True, "max_resolution": 0})
    if "__error__" in res:
        return "ERR: " + res["__error__"][:120]
    for item in res.get("content", []):
        if item.get("type") == "image":
            Path(path).write_bytes(base64.b64decode(item["data"]))
            return "saved"
    return "no image"


def png_size(path):
    with open(path, "rb") as f:
        head = f.read(24)
    w, h = struct.unpack(">II", head[16:24])
    return w, h


def editor_json():
    try:
        return json.loads(text_of(tool("editor_state", {})))
    except json.JSONDecodeError:
        return {}


def ui_dump(max_depth=40):
    res = tool("game_manage", {"op": "get_ui_elements", "params": {"max_depth": max_depth}})
    try:
        return json.loads(text_of(res))
    except json.JSONDecodeError:
        return {}


def flat_nodes(elements):
    flat = elements.get("elements", []) if isinstance(elements, dict) else elements
    nodes = []

    def walk(nodes_in):
        for n in nodes_in:
            if not isinstance(n, dict):
                continue
            nodes.append(n)
            walk(n.get("children", []) or [])
    walk(flat)
    return nodes


def rect_of(node):
    rect = node.get("global_rect", node.get("rect", {}))
    pos = rect.get("position", rect)
    size = rect.get("size", {})
    x, y = (float(pos.get("x", 0)), float(pos.get("y", 0))) if isinstance(pos, dict) else (float(pos[0]), float(pos[1]))
    if isinstance(size, dict):
        w, h = float(size.get("x", 1)), float(size.get("y", 1))
    else:
        w = float(size[0]) if size else 1.0
        h = float(size[1]) if size else 1.0
    return x, y, w, h


def rect_center(node):
    x, y, w, h = rect_of(node)
    return x + w / 2, y + h / 2


def canvas_extents(elements):
    """The canvas size as the max extents across all visible controls."""
    max_x = max_y = 0.0
    for n in flat_nodes(elements):
        if not n.get("visible", True):
            continue
        x, y, w, h = rect_of(n)
        if w > 4000 or h > 4000:  # nonsense guard
            continue
        max_x = max(max_x, x + w)
        max_y = max(max_y, y + h)
    return max_x, max_y


XFORM = {"sx": 1.0, "sy": 1.0}


def root_canvas_width():
    """Visible canvas width = the scene root Control's size.x (probes show the
    root reports e.g. 2019 in a maximized 2560 window under canvas_items+expand)."""
    try:
        info = json.loads(text_of(tool("game_manage", {"op": "get_node_info", "params": {"path": "/", "include_properties": True}})))
        sz = info.get("properties", {}).get("size", {})
        return float(sz.get("x", 0))
    except Exception:
        return 0.0


def compute_transform():
    """PROVEN empirically: input_mouse positions are WINDOW PIXELS, while UI
    dump rects are CANVAS coordinates. Under stretch canvas_items+expand the
    canvas is scaled uniformly to min(win/base); factor = shot_w / root_w.
    (In a 1920-wide window the factor is 1.0, which is why clicks once worked
    there by accident.)"""
    tmp = OUT / "_probe.png"
    if shot(str(tmp)) != "saved":
        return "shot failed"
    ww, wh = png_size(tmp)
    cw = root_canvas_width()
    s = (ww / cw) if cw > 100 else 1.0
    XFORM["sx"] = s
    XFORM["sy"] = s
    return ("window shot %dx%d, root canvas %.0f wide -> click factor %.4f (window pixels)"
            % (ww, wh, cw, s))


def raw_click(wx, wy):
    pos = {"x": wx, "y": wy}
    tool("game_manage", {"op": "input_mouse", "params": {"event": "motion", "position": pos}})
    tool("game_manage", {"op": "input_mouse", "params": {"event": "button", "button": "left", "pressed": True, "position": pos}})
    tool("game_manage", {"op": "input_mouse", "params": {"event": "button", "button": "left", "pressed": False, "position": pos}})


def click_node(node):
    cx, cy = rect_center(node)
    raw_click(cx * XFORM["sx"], cy * XFORM["sy"])
    time.sleep(1.6)
    return int(cx), int(cy)


def find_node(elements, needle, button_only=False, last=True, exact=False):
    found = []
    for n in flat_nodes(elements):
        ntype = str(n.get("type", n.get("class", ""))).lower()
        txt = str(n.get("text", n.get("label", "")))
        if not n.get("visible", True):
            continue
        if exact:
            if txt.strip().lower() != needle.lower():
                continue
        elif needle.lower() not in txt.lower():
            continue
        if button_only and "button" not in ntype:
            continue
        found.append(n)
    if not found:
        return None
    return found[-1] if last else found[0]


def click_text(needle, note="", button_only=False, expect=None, exact=False):
    """Click a node by text; if `expect` is given, verify it appears in the
    next dump (single attempt - coordinates are identity by proof)."""
    node = find_node(ui_dump(), needle, button_only=button_only, exact=exact)
    if node is None:
        return "MISS: %s (%s)" % (needle, note)
    cx, cy = click_node(node)
    result = "click %r [%s] at %d,%d" % (needle, str(node.get("type", "?")), cx, cy)
    if expect is None:
        return result
    joined = dump_texts()
    if expect.lower() in joined.lower():
        return "%s -> verified (%s visible)" % (result, expect)
    return "%s -> UNVERIFIED (expected %s)" % (result, expect)


def backend_state():
    with urllib.request.urlopen("http://127.0.0.1:8001/state", timeout=5) as r:
        return json.loads(r.read().decode())


def dump_texts():
    return " | ".join(str(n.get("text", "")) for n in flat_nodes(ui_dump()) if n.get("text"))


def note(m):
    print(m, flush=True)


request("initialize", {
    "protocolVersion": "2024-11-05",
    "capabilities": {},
    "clientInfo": {"name": "freebuff-audit", "version": "1.0"},
}, timeout=90)
send({"jsonrpc": "2.0", "method": "notifications/initialized"})

try:
    st = editor_json()
    if st.get("game_status", {}).get("active"):
        tool("project_manage", {"op": "stop"})
        time.sleep(3)
    tool("project_run", {})
    for _ in range(30):
        time.sleep(1)
        st = editor_json()
        if st.get("game_status", {}).get("active") and st.get("game_capture_ready"):
            break
    time.sleep(6)
    note("transform: %s" % compute_transform())

    # New game through the menu, verified by a marker that exists only in the
    # game dashboard (the detailed-status button), never in the menu.
    node = find_node(ui_dump(), "new game", button_only=True, exact=True)
    if node is None:
        note("FATAL: no New Game button")
        raise SystemExit(1)
    cx, cy = click_node(node)
    hud = "View Detailed Status" in dump_texts()
    if not hud:
        note("click at %d,%d did not enter game - retrying once" % (cx, cy))
        click_node(node)
        time.sleep(2.5)
        hud = "View Detailed Status" in dump_texts()
    note("in game: %s" % hud)
    if not hud:
        note("FATAL: could not enter the game")
        raise SystemExit(1)

    # Age at a glance: a top-bar "N / N" label must exist now
    import re
    texts = [str(n.get("text", "")).strip() for n in flat_nodes(ui_dump())]
    age_re = re.compile(r"^\d+ / \d+$")
    age_hits = [t for t in texts if age_re.match(t)]
    note("AGE label candidates: %s" % (age_hits or "NONE"))

    # --- Five tabs via the in-overlay strip ---
    for tab, marker, name in [
            ("Status", "LIFESPAN", "a_status"),
            ("Techniques", "KNOWN ARTS", "b_techniques"),
            ("Inventory", "STORAGE RING", "c_inventory"),
            ("Journal", "ACTIVE ENDEAVORS", "d_journal"),
            ("Equipment", "WORN ARTIFACTS", "e_equipment")]:
        note(click_text(tab, "overlay tab strip", button_only=True, exact=True))
        time.sleep(0.7)
        note("  %s visible: %s" % (marker, marker in dump_texts().upper()))
        note("%s shot: %s" % (name, shot(str(OUT / ("audit_%s.png" % name)))))

    # close overlay (X in the overlay header) - exact match so "Explore" etc.
    # can never shadow it
    note(click_text("X", "close overlay", button_only=True, exact=True))
    time.sleep(1)

    # --- Gather herbs twice so refine has materials ---
    note(click_text("Gather Herbs", "action grid"))
    time.sleep(2.2)
    note(click_text("Gather Herbs", "action grid again"))
    time.sleep(2.2)
    s = backend_state()
    note("inventory after gather: %s" % json.dumps(s.get("player", {}).get("inventory", {}))[:220])

    # --- Refine popup (the redesign) ---
    note(click_text("Refine Pills", "action grid"))
    time.sleep(1.5)
    note("refine shot: " + shot(str(OUT / "audit_f_refine.png")))
    joined = dump_texts()
    note("brewable section present: %s" % ("BREWABLE NOW" in joined))
    note("locked section present: %s" % ("OUT OF REACH" in joined))
    note("have/need counts shown: %s" % ("(have " in joined))

    # --- Brew the first truly brewable recipe; verify through the backend ---
    s0 = backend_state()
    inv0 = s0.get("player", {}).get("inventory", {})
    target = None
    for r in s0.get("refining_recipes", []):
        if r.get("available") and all(inv0.get(k, 0) >= v for k, v in r.get("inputs", {}).items()):
            target = r
            break
    if target is None:
        note("MISS: no recipe is brewable with the gathered materials")
    else:
        title = str(target.get("display_name", "")).lower()
        # The brewable card's title Label (recipe.display_name) sits between the
        # two section captions; match by text AND that vertical band.
        nodes = flat_nodes(ui_dump())

        def ypos(n):
            r = n.get("global_rect", n.get("rect", {}))
            p = r.get("position", {})
            return float(p.get("y", 0)) if isinstance(p, dict) else 0.0

        top_y = bot_y = None
        for n in nodes:
            t = str(n.get("text", ""))
            if t.startswith("BREWABLE NOW"):
                top_y = ypos(n)
            elif t.startswith("STILL OUT OF REACH"):
                bot_y = ypos(n)
        row = None
        for n in nodes:
            t = str(n.get("text", "")).lower()
            if title and title in t and top_y is not None and bot_y is not None and top_y < ypos(n) < bot_y:
                row = n
        if row is None:
            note("MISS: %r row not rendered in the brewable band" % title)
        else:
            note("row node: type=%s text=%r rect=%s" % (
                row.get("type"), str(row.get("text", ""))[:40],
                json.dumps(row.get("global_rect", row.get("rect", {})))))
            cx, cy = click_node(row)
            note("clicked window px (%d, %d) * factor" % (cx, cy))
            time.sleep(3)
            after = backend_state().get("player", {}).get("inventory", {})
            still_open = find_node(ui_dump(), "Refine Pills", exact=True) is not None
            note("refine dialog still open after pick: %s" % still_open)
            if still_open:
                note("post-click shot: " + shot(str(OUT / "audit_g2_postclick.png")))
            deltas = []
            for k, v in target.get("inputs", {}).items():
                deltas.append("%s %d->%d (expect -%d)" % (k, int(inv0.get(k, 0)), int(after.get(k, 0)), v))
            out_id = str(target.get("output", {}).get("item_id", ""))
            out_n = int(target.get("output", {}).get("count", 1))
            deltas.append("%s %d->%d (expect +%d)" % (out_id, int(inv0.get(out_id, 0)), int(after.get(out_id, 0)), out_n))
            note("BREW [%s]: %s" % (target.get("id"), ", ".join(deltas)))
            note("refine result shot: " + shot(str(OUT / "audit_g_refine_result.png")))

    # picking a recipe closes the dialog itself; only clean up if it remains
    if find_node(ui_dump(), "Refine Pills", exact=True) is not None:
        note(click_text("X", "close refine", button_only=True, exact=True))
    time.sleep(1)

    # --- Remaining popups ---
    for label, name in [("Travel", "h_travel"), ("World Map", "i_worldmap"),
                        ("Talents", "j_talents"), ("Dao", "k_dao")]:
        note(click_text(label, "action grid"))
        time.sleep(1.5)
        note("%s shot: %s" % (name, shot(str(OUT / ("audit_%s.png" % name)))))
        note(click_text("X", "close %s" % name, button_only=True, exact=True))
        time.sleep(0.8)

    note(click_text("Settings", "top bar", button_only=True, exact=True))
    time.sleep(1.5)
    note("settings shot: " + shot(str(OUT / "audit_l_settings.png")))
    note(click_text("X", "close settings", button_only=True, exact=True))

    note("AUDIT COMPLETE")
finally:
    tmp = OUT / "_probe.png"
    if tmp.exists():
        tmp.unlink()
    try:
        tool("project_manage", {"op": "stop"})
        note("game stopped")
    except Exception:
        pass
    try:
        proc.stdin.close()
        proc.wait(timeout=10)
    except Exception:
        proc.kill()
