"""Generate placeholder art for ``divine_phoenix_mystic_realm``.

The handover noted this is the one location still missing artwork. This writes a
deterministic, atmospheric gradient placeholder (a dark indigo-to-crimson wash)
plus the Godot ``.import`` sidecar so the editor picks it up without rescanning.
Replace the PNG with real art later; the filename and import metadata won't
change.

Usage:
    python tools/gen_missing_location_art.py
"""
from __future__ import annotations

import hashlib
import struct
import zlib
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "frontend-godot" / "assets" / "locations"
TARGET = ASSETS / "divine_phoenix_mystic_realm.png"
RES_PATH = "res://assets/locations/divine_phoenix_mystic_realm.png"

WIDTH, HEIGHT = 960, 640


def _pixel(x: int, y: int) -> tuple[int, int, int]:
    # Vertical wash: deep indigo (top) -> dark crimson (bottom), with a faint
    # warm glow near the centre to suggest a phoenix realm's heat.
    t = y / (HEIGHT - 1)
    r = int(24 + (86 - 24) * t)
    g = int(16 + (22 - 16) * t)
    b = int(52 + (34 - 52) * t)
    dx = (x - WIDTH / 2) / (WIDTH / 2)
    dy = (y - HEIGHT / 2) / (HEIGHT / 2)
    glow = max(0.0, 1.0 - (dx * dx + dy * dy) * 2.2)
    r = min(255, r + int(glow * 46))
    g = min(255, g + int(glow * 18))
    return r, g, b


def _write_png(path: Path) -> None:
    raw = bytearray()
    for y in range(HEIGHT):
        raw.append(0)
        for x in range(WIDTH):
            raw.extend(_pixel(x, y))

    def chunk(tag: bytes, data: bytes) -> bytes:
        payload = struct.pack(">I", len(data)) + tag + data
        return payload + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    ihdr = struct.pack(">IIBBBBB", WIDTH, HEIGHT, 8, 2, 0, 0, 0)
    png = b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", ihdr) + chunk(b"IDAT", zlib.compress(bytes(raw))) + chunk(b"IEND", b"")
    path.write_bytes(png)


def _write_import(path: Path) -> None:
    digest = hashlib.md5(RES_PATH.encode("utf-8")).hexdigest()
    content = f"""[remap]

importer="texture"
type="CompressedTexture2D"
uid="uid://bdivinemystic01"
path="res://.godot/imported/divine_phoenix_mystic_realm.png-{digest}.ctex"
metadata={{
"vram_texture": false
}}

[deps]

source_file="{RES_PATH}"
dest_files=["res://.godot/imported/divine_phoenix_mystic_realm.png-{digest}.ctex"]

[params]

compress/mode=0
compress/high_quality=false
compress/lossy_quality=0.7
compress/uastc_level=0
compress/rdo_quality_loss=0.0
compress/hdr_compression=1
compress/normal_map=0
compress/channel_pack=0
mipmaps/generate=false
mipmaps/limit=-1
roughness/mode=0
roughness/src_normal=""
process/channel_remap/red=0
process/channel_remap/green=1
process/channel_remap/blue=2
process/channel_remap/alpha=3
process/fix_alpha_border=true
process/premult_alpha=false
process/normal_map_invert_y=false
process/hdr_as_srgb=false
process/hdr_clamp_exposure=false
process/size_limit=0
detect_3d/compress_to=1
"""
    path.write_text(content, encoding="utf-8")


def main() -> None:
    _write_png(TARGET)
    _write_import(Path(str(TARGET) + ".import"))
    print(f"wrote {TARGET.name} (+ .import)")


if __name__ == "__main__":
    main()
