---
description: 'Godot export rules: standalone Windows .exe, keep game rules out of Godot nodes/scenes. Use when working in the Godot frontend or on export.'
applyTo: 'frontend-godot/**'
---

# 04 — Godot Export Rules

The project may use Godot for interface, rendering, input handling, and Windows export.

However, Godot must not be treated as the owner of the entire game design.

## Export Requirements

1. The final game should be exportable as a Windows `.exe`.
2. Player-facing builds should not require the Godot editor.
3. The export target should usually be Windows x86_64.
4. Builds should be named clearly using semantic versioning.

Example:

```text
CultivationRPG_v0.1.0_windows_x64.exe
```

## Desktop Game Flow

The game should support a normal desktop game flow:

1. Launch executable.
2. Main menu.
3. Continue game.
4. New game.
5. Load game.
6. Settings.
7. Credits.
8. Exit.

## Godot Boundary Rules

1. Avoid relying on editor-only functionality.
2. Avoid placing critical game configuration only in scene files.
3. Keep core game rules separate from Godot nodes.
4. Isolate Godot-specific file access, input handling, and scene transitions.
5. If using Godot Resources, ensure the data model can still be understood and migrated later.
6. Do not bury game rules inside scene signal callbacks.
7. Keep exported builds reproducible.
8. Document export settings in `docs/EXPORT_GUIDE.md`.
