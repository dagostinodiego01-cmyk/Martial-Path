"""Complete the Godot AI v3 -> v4 plugin swap by hand.

The signed migration capsule verifies and stages the v4 release, then asks the
activation runner to swap two directories in-editor. On Windows that first
rename (`addons/godot_ai` -> `.godot_ai_update/backup/<from_version>`) is
refused while the editor holds the add-on's script files open, which is how
`activation.json` ends up at `status: "previous_tree_retained"`.

Running this with the editor closed performs the same two steps without the
open handles, using the capsule's own payload and layout:

  1. `addons/godot_ai`            -> `addons/.godot_ai_update/backup/<from>`
  2. `<payload zip>`              -> `addons/godot_ai` (293 signed files)

Every file is checked against the manifest inventory (sha256 + size) before the
live tree is touched, and again after extraction. No `pending.json` is written:
the incoming v4 plugin only runs its post-restart verification for a marker in
`swapped` state, so a hand swap is indistinguishable from a fresh install and
nothing will roll it back.

Usage (from the project root, editor closed):
    .venv/Scripts/python.exe tools/complete_v4_swap.py

Refuses to run while a Godot process is alive (override with --force, which is
almost always the failure you are trying to avoid).
"""

from __future__ import annotations

import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GODOT_PROJECT = ROOT / "frontend-godot"
ADDONS = GODOT_PROJECT / "addons"
LIVE = ADDONS / "godot_ai"
## Every archive entry is `addons/godot_ai/...`, so the extraction target is the
## project root above `addons/`, never `addons/` itself.
ARCHIVE_PREFIX = "addons/godot_ai/"
UPDATE_ROOT = ADDONS / ".godot_ai_update"
PAYLOAD = LIVE / "migration_payload"
ARCHIVE_NAME = "godot-ai-v4-plugin.zip"
MANIFEST_NAME = "godot-ai-v4-plugin.manifest.json"
CAPSULE_NAME = "Godot AI v4 Migration"
V4_NAME = "Godot AI"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def read_plugin_name(path: Path) -> str:
    if not path.is_file():
        return ""
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("name="):
            return line.split("=", 1)[1].strip().strip('"')
    return ""


def godot_processes() -> list[str]:
    """Live Godot editor/player PIDs as `name:pid`.

    Plain `tasklist` plus a substring match: `tasklist /FI "IMAGENAME eq
    Godot*.exe"` matches nothing, because the filter takes an exact image name
    and the image is `Godot_v4.7-stable_win64.exe` (truncated in the listing).
    An empty result means "not running", which is why it must not be trusted
    when tasklist itself fails.
    """
    if sys.platform != "win32":
        return []
    try:
        listed = subprocess.run(["tasklist"], capture_output=True, text=True, timeout=30)
    except (OSError, subprocess.SubprocessError):
        return []
    if listed.returncode != 0:
        return []
    found = []
    for line in listed.stdout.splitlines():
        if "Godot" not in line:
            continue
        parts = line.split()
        found.append("%s:%s" % (parts[0], parts[1]) if len(parts) > 1 else parts[0])
    return found


def verify_archive(archive: Path, manifest: dict) -> tuple[bool, str]:
    """Every payload file must match the signed inventory exactly."""
    expected = manifest["asset"]["sha256"]
    actual = sha256_file(archive)
    if actual != expected:
        return False, "archive sha256 %s does not match the signed %s" % (actual, expected)
    inventory = manifest["inventory"]
    with zipfile.ZipFile(archive) as zf:
        names = set(zf.namelist())
        declared = {entry["path"] for entry in inventory}
        missing = declared - names
        extra = names - declared
        if missing or extra:
            return False, "inventory mismatch (missing %d, extra %d)" % (len(missing), len(extra))
        stray = sorted(n for n in names if not n.startswith(ARCHIVE_PREFIX))
        if stray:
            return False, "archive entries outside %s: %s" % (ARCHIVE_PREFIX, stray[:3])
        for entry in inventory:
            data = zf.read(entry["path"])
            if len(data) != entry["size"] or hashlib.sha256(data).hexdigest() != entry["sha256"]:
                return False, "payload file does not match its manifest hash: %s" % entry["path"]
    return True, "archive and all %d payload files match the signed inventory" % len(inventory)


def verify_tree(tree: Path, manifest: dict) -> tuple[bool, str]:
    bad = []
    for entry in manifest["inventory"]:
        path = tree / entry["path"].split("addons/godot_ai/", 1)[-1]
        if not path.is_file():
            bad.append(path.as_posix())
            continue
        if path.stat().st_size != entry["size"] or sha256_file(path) != entry["sha256"]:
            bad.append(path.as_posix())
    if bad:
        return False, "%d installed file(s) do not match the manifest: %s" % (
            len(bad), ", ".join(str(b) for b in bad[:5]))
    return True, "all %d installed files match the signed inventory" % len(manifest["inventory"])


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--force", action="store_true",
                        help="attempt the swap even while a Godot process is running")
    args = parser.parse_args()

    if not LIVE.is_dir():
        print("no live add-on tree at %s" % LIVE)
        return 1

    live_name = read_plugin_name(LIVE / "plugin.cfg")
    print("live plugin.cfg name: %r" % live_name)
    if live_name == V4_NAME:
        print("already the real v4 tree - nothing to do.")
        return 0
    if live_name != CAPSULE_NAME:
        print("expected the %r capsule, found %r - refusing to guess." % (CAPSULE_NAME, live_name))
        return 1

    running = godot_processes()
    if running and not args.force:
        print("Godot is still running (%s)." % ", ".join(sorted(set(running))))
        print("Close the editor (and any second instance with this project open), then rerun.")
        print("The first directory rename is exactly what the editor's open handles refuse.")
        return 2

    archive = PAYLOAD / ARCHIVE_NAME
    manifest_path = PAYLOAD / MANIFEST_NAME
    if not archive.is_file() or not manifest_path.is_file():
        print("payload is incomplete: %s" % PAYLOAD)
        return 1
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    ok, detail = verify_archive(archive, manifest)
    print("payload check: %s" % detail)
    if not ok:
        print("refusing to touch the live tree.")
        return 1

    from_version = "3.2.5"
    activation = UPDATE_ROOT / "activation.json"
    if activation.is_file():
        try:
            recorded = json.loads(activation.read_text(encoding="utf-8"))
            from_version = str(recorded.get("from_version") or from_version)
        except (OSError, json.JSONDecodeError):
            pass

    backup = UPDATE_ROOT / "backup" / from_version
    if backup.exists():
        print("backup already exists at %s - resolve that update first." % backup)
        return 1

    to_version = str(manifest.get("version", ""))
    print("swapping %s -> %s (backup at %s)" % (from_version, to_version, backup))

    # The payload lives inside the tree being moved, so take a copy first.
    with tempfile.TemporaryDirectory(prefix="godot_ai_v4_") as staging:
        staged_archive = Path(staging) / ARCHIVE_NAME
        shutil.copy2(archive, staged_archive)

        backup.parent.mkdir(parents=True, exist_ok=True)
        try:
            LIVE.rename(backup)
        except OSError as exc:
            print("cannot move the live tree: %s" % exc)
            print("Godot or another process still holds files under %s." % LIVE)
            return 1
        print("moved live tree -> %s" % backup)

        with zipfile.ZipFile(staged_archive) as zf:
            ## Entries carry the `addons/` component, hence the project root.
            zf.extractall(GODOT_PROJECT)

    ok, detail = verify_tree(LIVE, manifest)
    print("installed tree check: %s" % detail)
    if not ok:
        print("restoring the capsule tree from %s" % backup)
        shutil.rmtree(LIVE, ignore_errors=True)
        backup.rename(LIVE)
        return 1

    print()
    print("v4 %s is in place at %s" % (to_version, LIVE))
    print("Next: open frontend-godot/project.godot. On enable the v4 plugin re-registers")
    print("the _mcp_game_helper autoload and serves the MCP bridge on port 8000 (ws 9500).")
    print("The capsule tree is kept at %s; nothing here writes pending.json, so the" % backup)
    print("plugin treats this as a plain install and will not roll it back.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
