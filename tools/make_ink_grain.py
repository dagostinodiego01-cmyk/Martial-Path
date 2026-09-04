"""Generate a subtle tileable ink-grain texture for the UI background (pure stdlib)."""
import struct
import zlib
from pathlib import Path

W = H = 256
rows = []
# Deterministic warm grain: base 0 with faint luminous specks, low alpha so it
# reads as paper tooth over the ground color, never as noise.
seed = 20260904
for y in range(H):
    row = bytearray([0])  # filter type 0
    for x in range(W):
        seed = (1103515245 * seed + 12345) & 0x7FFFFFFF
        v = (seed >> 16) & 0xFF
        # Sparse faint fibers: most pixels fully transparent, a few carry a
        # whisper of warm light (255, 244, 214) at 4-10 alpha.
        if v > 246:
            a = 10 if v > 252 else 5
            row += bytes((255, 244, 214, a))
        else:
            row += bytes((0, 0, 0, 0))
    rows.append(bytes(row))

raw = b"".join(rows)


def chunk(tag, data):
    c = struct.pack(">I", len(data)) + tag + data
    return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


png = b"\x89PNG\r\n\x1a\n"
png += chunk(b"IHDR", struct.pack(">IIBBBBB", W, H, 8, 6, 0, 0, 0))
png += chunk(b"IDAT", zlib.compress(raw, 9))
png += chunk(b"IEND", b"")

out = Path("frontend-godot/assets/ink_grain.png")
out.write_bytes(png)
print("wrote", out, len(png), "bytes")
