---
name: gui-updates
description: 'Routing + procedure for ALL visual/UI/frontend changes in the Martial Path RPG. Use whenever the user asks to change, style, restyle, lay out, add, fix, or tweak the GUI/UI/interface/screen/panel/theme/colours/widget/HUD/menu, or reports a visual bug. Enforces the rule that GUI work targets ONLY the Godot frontend (frontend-godot/), never the PySide6 desktop GUI, unless the user explicitly names PySide6/Qt/desktop. Covers the Godot files to edit, allowed backend view-model support, Godot-specific gotchas, and verification.'
argument-hint: 'the UI/visual change to make'
---

# GUI Updates -> Godot Only

**Golden rule:** every visual / UI / frontend change goes to the **Godot
frontend** (`frontend-godot/`). Do **not** touch the PySide6 desktop GUI.

## When to Use
Any request about the interface: layout, panels, tabs, colours/theme, fonts,
buttons/cards, spacing, HUD, menus, "make the UI look like X", or a visual bug
report (misaligned, vertical text, wrong colour, overlap, etc.).

## Edit these (Godot)
- `frontend-godot/scripts/MainController.gd` - the whole UI is built in code here (top bar, Character panel, Location + Actions, right tabs, Event Log). This is almost always the file to change.
- `frontend-godot/scripts/ApiClient.gd` - only for how the client talks to the API (endpoints, request handling), not gameplay.
- `frontend-godot/scenes/*.tscn`, `frontend-godot/ui/themes/martial_path_theme.tres` - scene tree / shared theme resource.

## Routing decision (applies to every GUI request)
Route **ALL** GUI/visual/frontend requests to the Godot frontend
(`frontend-godot/`) unless the user **explicitly** uses one of these terms:
"PySide6", "Qt", "desktop GUI", or `gui_main.py`. If the request is ambiguous,
default to Godot and state that assumption. Keep this routing logic here only -
do not restate or split it across other sections.

Only when the user explicitly names PySide6/Qt/desktop, edit the desktop GUI
instead; otherwise leave these untouched:
- `game/ui/gui_interface.py`
- `game/ui/ui_theme.py`
- `game/gui_main.py`, root `gui_main.py`

Also leave the CLI (`game/ui/cli_interface.py`) alone unless asked.

## Allowed backend support (not the PySide6 GUI)
The Godot client only receives what the API sends. If the UI needs a value it
does not have, add a **UI-safe, read-only view-model field** to
`GameEngine.get_game_state()` (served by `game/api/server.py`). That is backend
plumbing, not the PySide6 GUI, and it is allowed. Only add a new view-model
field if the required value is entirely absent from the existing `/state`
response; if it can be derived or composed from existing fields in
`MainController.gd`, do that instead. Never compute gameplay in the frontend -
the UI renders `state` / result dicts and sends `{"action": ...}`.

When a GUI change does require a new state field, sequence the work: (1) add and
verify the backend field first, (2) confirm `pytest -q` passes, then (3) update
`MainController.gd` to consume it. Do not deliver the frontend change without the
backend change in the same response.

## Godot procedure & gotchas (learned)
1. **UI is code, not scenes.** Build/adjust widgets in `MainController.gd` (`_build_*`, `_render_*`). Keep the dashboard structure and the charcoal/gold palette constants at the top of the file.
2. **Short `Label`s must not wrap.** Use `AUTOWRAP_OFF` for single-line labels (headings, captions, footer values). `AUTOWRAP_WORD_SMART` lets a label collapse to one-character-per-line (vertical text) when a sibling spacer squeezes it. Long copy uses `RichTextLabel`, which wraps by words.
3. **No multi-line lambdas for signals.** Connect signals to named methods (e.g. `_on_settings_selected`); inline multi-statement lambdas with a trailing `)` are fragile in GDScript.
4. **Anti-duplication (same as the brief):** Gold only in Inventory; Body/Essence only in the Character panel; HP/Qi only in the top bar; full location text only in the Location panel. Locked states come from `state.player.essence_unlocked`; the unlock hint from `cultivation_state.essence_gathering.unlock_requirement`.
5. Keep `func` names unique; verify with a search for `^func ` after large edits.

## Assets (images)
- Godot can only load assets under its **project root**: put images in `frontend-godot/assets/...` and reference them as `res://assets/...`. Files in the repo-root `Images/` folder are OUTSIDE the Godot project (staging only) and cannot be loaded via `res://`.
- **Location art** lives at `frontend-godot/assets/locations/<location_id>.png` (ids from `game/data/locations.json`). `_render_location` loads it by id via `ResourceLoader.exists()` + `load()`, with the location name label as the fallback. The app icon is `frontend-godot/icon.png`; the world map is staged at `frontend-godot/assets/world_map.jpg`.
- To add art for a location: copy `Images/<Name>.png` to `frontend-godot/assets/locations/<id>.png`. After adding files, the user must open the project in the Godot editor once so it imports them (generates `.import`); until then, `load()` falls back gracefully.

## Verify
- Godot is **not installed** in this workspace, so you cannot headless-parse or screenshot GDScript. Review manually: unique `^func `, no references to removed vars, valid Godot 4 API.
- To sanity-check the data the UI will show, start the backend and read state: `uvicorn game.api.server:app` then `GET /state` (or call `game.api.server.get_state()` in Python).
- If you added a state field, run `pytest -q` (the state shape is covered by `tests/test_api_server.py`).
- Ask the user to open the project in the Godot editor once to confirm it launches.
