# -*- mode: python ; coding: utf-8 -*-
"""PyInstaller build spec for the Martial Path backend.

Produces a single-file ``MartialPathBackend.exe`` that serves the FastAPI engine
API on http://127.0.0.1:8000. The exported Godot game launches this executable,
so the packaged build needs no Python install.

Build (from the repository root, using the project venv):

    .venv\\Scripts\\python.exe -m PyInstaller backend.spec --noconfirm

Output: ``dist/MartialPathBackend.exe``.
"""
from PyInstaller.utils.hooks import collect_all

# Bundle the JSON game data alongside the ``game`` package so that
# ``data_loader.DATA_DIR`` (``game/data`` resolved relative to the module) points
# at the extracted copy inside the frozen bundle.
datas = [("game/data", "game/data")]
binaries = []

# uvicorn resolves its ASGI loop/protocol implementations dynamically; pin the
# ones ``run_backend`` actually selects (asyncio + h11) so they are always bundled.
hiddenimports = [
    "uvicorn.loops.asyncio",
    "uvicorn.protocols.http.h11_impl",
    "uvicorn.lifespan.on",
]

# Pull in the full dependency trees that use dynamic imports / compiled cores.
for _pkg in ("uvicorn", "anyio", "pydantic", "pydantic_core"):
    _d, _b, _h = collect_all(_pkg)
    datas += _d
    binaries += _b
    hiddenimports += _h


a = Analysis(
    ["run_backend.py"],
    pathex=[],
    binaries=binaries,
    datas=datas,
    hiddenimports=hiddenimports,
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    # The API server never touches the desktop UI or test tooling; excluding them
    # keeps the executable small and avoids accidental heavy dependencies.
    excludes=["tkinter", "PySide6", "PyQt5", "PyQt6", "matplotlib", "pytest", "IPython"],
    noarchive=False,
)

pyz = PYZ(a.pure)

# One-DIRECTORY build (not one-file): a single MartialPathBackend.exe plus an
# ``_internal`` folder. The game auto-launches and later terminates this process,
# so one clean PID (no one-file bootloader child) and no per-launch extraction
# matter more than shipping a single loose file.
exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="MartialPathBackend",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    # Windowed (no console) so launching the backend never flashes a terminal.
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=False,
    upx_exclude=[],
    name="MartialPathBackend",
)
