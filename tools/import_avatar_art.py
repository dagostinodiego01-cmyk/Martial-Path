"""Import painted player portraits as game avatars (the drop-in path).

The twenty roster slots are playable with generated placeholders
(``tools/gen_avatar_art.py``). Real art replaces a slot file-for-file; this tool
does the conversion and leaves a provenance record, so a painting never lands in
the repo as an anonymous binary:

    python tools/import_avatar_art.py sword_maiden=C:/art/wi5UL.jpg
    python tools/import_avatar_art.py sect_patriarch=C:/art/elder.png:0.9:0.02
    python tools/import_avatar_art.py --dry-run wi5UL=... # validate only

Each item is ``<avatar_id>=<source image>[:zoom[:top]]`` where ``zoom`` is the
fraction of the source's short side kept (1.0 keeps the full width) and ``top``
nudges the crop window down as a fraction of the source height. Sources may be
any format the Godot runtime reads (JPEG, PNG, WebP); the shipped asset is
always a square, sRGB PNG, at most ``--size`` (default 512) on a side.

That size is a cap, not a target. The client's largest portrait is 76px, so a
crop smaller than the cap ships at its own resolution rather than upscaled -- a
small source stays sharp instead of being stretched into a soft 512. The
manifest records the size each portrait actually shipped at.

The default ``--anchor face`` frames a head-and-shoulders bust: the importer
measures the subject's skin tones, sizes the window so the face fills a set
fraction of the square, and reports where that face ended up. ``--anchor top``
and ``--anchor center`` fall back to plain geometric squares, and any source
where the detector finds no skin still ships as a top crop rather than failing.

The pixels are converted by the engine, not by Python: ``Image.load`` reads
every codec a painter hands over, and ``Image.resize`` resamples with Lanczos.
This project has no imaging library, and adding one just for an asset step is a
poor trade (``frontend-godot/tools/`` holds the engine-side half of this tool
and is ``.gdignore``'d, so it is never scanned by the editor nor exported).

Provenance lands in ``frontend-godot/assets/avatars/art_manifest.json``: art
that is absent from that manifest is a generated placeholder, which is what lets
``tests/test_player_identity.py`` pin the placeholder pixels without ever
pinning a painting, and ``tools/gen_avatar_art.py`` refuse to overwrite art.
Each entry keeps both halves of the crop: ``spec`` is what was asked for
(anchor/zoom/top, the replayable recipe) and ``crop``/``face`` are what the
engine actually did, so a re-import can be diffed instead of trusted.

Finally the tool refreshes Godot's texture cache (``--import``), because the
running game draws the *imported* ctex rather than the PNG on disk and would
otherwise keep showing the previous portrait until the editor re-imported it.
"""
from __future__ import annotations

import argparse
import glob
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from tools.gen_avatar_art import BY_ID, OUT_DIR, Res, _write_import  # noqa: E402

#: Painted portraits import with mipmaps: the picker draws them at ~15% of the
#: shipped 512px, where unmipmapped line work speckles.
MIPMAPS = True

MANIFEST_PATH = OUT_DIR / "art_manifest.json"
GODOT_SCRIPT = "res://tools/import_avatar_art.gd"
RESULT_PREFIX = "AVATAR_IMPORT "

#: Places a Godot binary is likely to be on this project's machines. ``--godot``
#: and ``$GODOT_BIN`` always win; the search is only a convenience.
_GODOT_HINTS = (
    "~/Downloads/Godot_v*/Godot_*console*.exe",
    "~/Downloads/Godot_v*/*.exe",
    "~/Downloads/Godot*.exe",
    "~/.local/bin/godot",
    "/usr/local/bin/godot",
    "C:/Program Files/Godot/*.exe",
)


def find_godot(explicit: str = "") -> Path:
    if explicit:
        return Path(explicit)
    env = os.environ.get("GODOT_BIN", "")
    if env:
        return Path(env)
    which = shutil.which("godot")
    if which:
        return Path(which)
    for hint in _GODOT_HINTS:
        matches = [Path(match) for match in glob.glob(os.path.expanduser(hint)) if Path(match).is_file()]
        if not matches:
            continue
        # Prefer the console build, which keeps stdout attached on Windows.
        consoles = [path for path in matches if "console" in path.name]
        return sorted(consoles or matches)[-1]
    raise SystemExit("could not find a Godot binary; pass --godot <path> or set GODOT_BIN")


def read_manifest(path: Path = MANIFEST_PATH) -> dict:
    if not path.is_file():
        return {"version": 1, "avatars": {}}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or "avatars" not in data:
        raise SystemExit(f"{path} is not an avatar manifest")
    return data


def write_manifest(manifest: dict, path: Path = MANIFEST_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = {"version": manifest.get("version", 1),
               "note": ("Provenance for shipped avatar art. An id absent here is a generated "
                        "placeholder (tools/gen_avatar_art.py); 'art' is 'painted' when it came "
                        "from a file through tools/import_avatar_art.py."),
               "avatars": {key: manifest["avatars"][key] for key in sorted(manifest["avatars"])}}
    path.write_text(json.dumps(ordered, indent=2) + "\n", encoding="utf-8")


def painted_ids(manifest: dict) -> set:
    return {key for key, entry in manifest.get("avatars", {}).items() if entry.get("art") == "painted"}


def parse_item(spec: str) -> dict:
    """``<id>=<path>[:zoom[:top]]`` -> a job item (with the id validated)."""
    if "=" not in spec:
        raise SystemExit(f"expected <avatar_id>=<image path>, got {spec!r}")
    avatar_id, _, rest = spec.partition("=")
    avatar_id = avatar_id.strip()
    if avatar_id not in BY_ID:
        raise SystemExit(f"unknown avatar id {avatar_id!r}; the roster lives in tools/gen_avatar_art.py")
    # A drive letter colon (C:/...) is part of the path, so peel numeric
    # modifiers off the right-hand end only.
    parts = rest.split(":")
    mods: list = []
    while len(parts) > 1 and len(mods) < 2 and _is_float(parts[-1]):
        mods.insert(0, float(parts.pop()))
    zoom = mods[0] if len(mods) >= 1 else 1.0
    top = mods[1] if len(mods) >= 2 else 0.0
    if not 0.15 <= zoom <= 1.0:
        raise SystemExit(f"zoom must be between 0.15 and 1.0, got {zoom} in {spec!r}")
    source = ":".join(parts)
    if source == "":
        raise SystemExit(f"missing source image in {spec!r}")
    path = Path(os.path.expanduser(source))
    if not path.is_file():
        raise SystemExit(f"source image not found: {path}")
    return {"id": avatar_id, "source": str(path), "zoom": zoom, "top": top}


def _is_float(text: str) -> bool:
    try:
        float(text)
    except ValueError:
        return False
    return True


def import_avatars(items: list, size: int = 512, anchor: str = "top", godot: Path = None,
                   force: bool = False, dry_run: bool = False,
                   skip_reimport: bool = False) -> dict:
    manifest = read_manifest()
    already = painted_ids(manifest)
    job_items = []
    skipped = []
    for item in items:
        if item["id"] in already and not force:
            skipped.append(item["id"])
            continue
        job_items.append({
            "id": item["id"],
            "source": item["source"],
            "dest": str((OUT_DIR / f"{item['id']}.png").resolve()),
            "zoom": item["zoom"],
            "top": item["top"],
            "anchor": anchor,
        })

    requested = {item["id"]: item for item in job_items}
    print(f"{len(job_items)} to import, {len(skipped)} already painted "
          f"({', '.join(skipped) if skipped else 'none'})")
    for entry in job_items:
        print(f"  {entry['id']:<24} <- {Path(entry['source']).name}")
    if dry_run or not job_items:
        return {"imported": [], "skipped": skipped, "dry_run": True}

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    job_path = Path(tempfile.gettempdir()) / "martial_path_avatar_job.json"
    job_path.write_text(json.dumps({"size": size, "items": job_items}), encoding="utf-8")

    binary = find_godot(str(godot) if godot else "")
    command = [str(binary), "--headless", "--path", str(ROOT / "frontend-godot"),
               "-s", GODOT_SCRIPT, "--", str(job_path)]
    print(f"running {binary.name} headless")
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    result_line = next((line for line in completed.stdout.splitlines() if line.startswith(RESULT_PREFIX)), "")
    if not result_line:
        sys.stdout.write(completed.stdout[-4000:])
        sys.stderr.write(completed.stderr[-2000:])
        raise SystemExit("the engine produced no import result (see output above)")

    payload = json.loads(result_line[len(RESULT_PREFIX):])
    for entry in payload.get("imported", []):
        avatar_id = str(entry["id"])
        shipped = OUT_DIR / f"{avatar_id}.png"
        if not shipped.is_file():
            raise SystemExit(f"engine reported {avatar_id} but {shipped} does not exist")
        source = Path(str(entry["source"]))
        asked = requested.get(avatar_id, {})
        manifest["avatars"][avatar_id] = {
            "art": "painted",
            "source": source.name,
            "imported": date.today().isoformat(),
            "source_sha256": _sha256(source),
            "shipped_sha256": _sha256(shipped),
            "crop": entry.get("crop", {}),
            "source_size": [int(entry.get("source_width", 0)), int(entry.get("source_height", 0))],
            # The request, kept beside the geometry it produced: replaying the
            # manifest's own recipe has to reproduce the shipped pixels.
            "spec": {"anchor": asked.get("anchor", anchor),
                     "zoom": asked.get("zoom", 1.0),
                     "top": asked.get("top", 0.0)},
            "size": int(entry.get("size", size)),
            # The cap the import was run with, beside the size it produced: the
            # two differ whenever the crop was smaller than the cap, which is
            # the whole point (a small source is never stretched).
            "size_cap": int(entry.get("requested_size", size)),
        }
        # Only recorded when the detector chose the crop: on an explicit
        # zoom/top crop it would report a face that scenery put there.
        if entry.get("face"):
            manifest["avatars"][avatar_id]["face"] = entry["face"]
        _write_import(shipped, Res % avatar_id, mipmaps=MIPMAPS)

    write_manifest(manifest)
    print(f"manifest: {MANIFEST_PATH.relative_to(ROOT)}")
    if not skip_reimport:
        refresh_import_cache(binary)
    return {"imported": payload.get("imported", []), "failed": payload.get("failed", []), "skipped": skipped}


def refresh_import_cache(godot: Path) -> bool:
    """Make the new art visible to the running game.

    A shipped PNG is drawn from Godot's imported texture cache
    (``.godot/imported/*.ctex``), and the runtime loads that cache as-is: writing
    a PNG and its ``.import`` sidecar is not enough, because the editor is what
    re-imports, and the game will happily draw the *previous* portrait from a
    stale ctex until it does. So the importer runs the same import pass the
    editor would -- cheap, and it turns a baffling "my new art did not show up"
    into a non-event.
    """
    command = [str(godot), "--headless", "--path", str(ROOT / "frontend-godot"), "--import"]
    completed = subprocess.run(command, capture_output=True, text=True, encoding="utf-8", errors="replace")
    if completed.returncode != 0:
        print(f"WARNING: the texture cache refresh failed (exit {completed.returncode}); "
              "reopen the project in the Godot editor before running the game")
        return False
    print("texture cache refreshed (--skip-reimport to skip)")
    return True


def _sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1 << 16), b""):
            digest.update(chunk)
    return digest.hexdigest()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Import painted portraits as avatar assets.")
    parser.add_argument("items", nargs="*", metavar="id=image[:zoom[:top]]")
    parser.add_argument("--size", type=int, default=512,
                        help="shipped square size cap in px (default 512; never upscales a crop)")
    parser.add_argument("--anchor", choices=("face", "top", "center"), default="face",
                        help="crop anchor: 'face' frames a bust around the subject's face (default), "
                             "'top'/'center' take a plain square")
    parser.add_argument("--godot", default="", help="path to the Godot binary")
    parser.add_argument("--force", action="store_true", help="replace art that was already imported")
    parser.add_argument("--dry-run", action="store_true", help="validate the job and print it, then stop")
    parser.add_argument("--skip-reimport", action="store_true",
                        help="do not refresh Godot's texture cache (the game would draw the old art)")
    args = parser.parse_args(argv)

    if not args.items:
        parser.error("give at least one <avatar_id>=<image> item")
    items = [parse_item(spec) for spec in args.items]
    outcome = import_avatars(items, size=args.size, anchor=args.anchor,
                             godot=Path(args.godot) if args.godot else None,
                             force=args.force, dry_run=args.dry_run,
                             skip_reimport=args.skip_reimport)
    for entry in outcome.get("imported", []):
        crop = entry.get("crop", {})
        face = entry.get("face", {})
        print(f"  imported {entry['id']:<24} {entry.get('source_width')}x{entry.get('source_height')} "
              f"-> {entry.get('size')}px {crop.get('anchor')} crop={crop.get('side')}@{crop.get('top')}")
        if face:
            print(f"             face: {face.get('width', 0):.0%} of the square wide, "
                  f"centre {face.get('centre', 0):.0%}, brow {face.get('brow', 0):.0%}"
                  f"{' (too small: check the crop)' if not face.get('prominent') else ''}")
    if outcome.get("failed"):
        print(f"  FAILED: {outcome['failed']}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
