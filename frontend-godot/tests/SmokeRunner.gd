extends Node
## Headless smoke check for the Godot client shell (T.5).
##
## `check_panels.gd` covers the five overlay panels in isolation. This covers the
## controller that hosts them, driven with payloads captured from a real run:
##
##   * a state refresh with `enemy: null` AND `encounter: null` -- the exact pair
##     whose chained `.get()` broke the running game the first time NEW GAME was
##     clicked (see tests/test_godot_state_contract.py);
##   * the same refresh twice, because a refresh must be repeatable;
##   * a combat state (enemy set) and a pending-encounter state (encounter set);
##   * every tab opened and closed, with the overlay title matching the tab;
##   * one render of every result payload the run produced, so the event table is
##     exercised with engine output rather than hand-written fixtures.
##
## The payload is written by `tests/test_godot_smoke.py` from an actual seeded
## playthrough; the static half of the contract -- every `EventType` having a
## render arm at all -- is pinned by `tests/test_godot_event_coverage.py`.
##
## WHY A SCENE, NOT `-s`: a script run with `-s` has no autoload context, so
## `MainController.gd` (which reads the `Profile` autoload) fails to compile --
## "Identifier not found: Profile" -- and the check would test nothing. Running
## this scene as the main scene gives the real autoloads and the real controller.
##
## Run:  godot --headless --path frontend-godot res://tests/SmokeRunner.tscn -- <payload.json>
## Exit: 0 when every check passes, 1 otherwise.

var _failures: int = 0
var _rendered: int = 0
var _tabs: int = 0


func _ready() -> void:
	var payload: Dictionary = _load_payload()
	if payload.is_empty():
		_fail("no payload: pass the JSON file written by tests/test_godot_smoke.py after --")
		_report()
		return

	var controller: Control = preload("res://scenes/Main.tscn").instantiate() as Control
	if controller == null:
		_fail("res://scenes/Main.tscn did not instantiate a Control")
		_report()
		return
	add_child(controller)

	var states: Dictionary = payload.get("states", {})
	_refresh(controller, states.get("explore", {}), "explore (enemy null, encounter null)")
	_refresh(controller, states.get("explore", {}), "explore again (refresh is repeatable)")
	_refresh(controller, states.get("combat", {}), "combat (enemy set, encounter null)")
	_refresh(controller, states.get("encounter", {}), "encounter (encounter set, enemy null)")
	_tabs_open_and_close(controller)

	var events: Array = payload.get("events", [])
	for result in events:
		if typeof(result) != TYPE_DICTIONARY:
			continue
		# A crash here is the failure: the run dies before the summary line and the
		# Python wrapper sees a non-zero exit with no proof of coverage.
		controller.call("_render_event", result)
		_rendered += 1
	if _rendered != events.size():
		_fail("rendered %d of %d event payload(s)" % [_rendered, events.size()])
	else:
		_ok("rendered %d event payload(s) from a real run" % _rendered)

	_report()


## Refresh the client with one state payload and prove it rendered something.
func _refresh(controller: Control, state: Dictionary, label: String) -> void:
	if state.is_empty():
		_fail("%s: no such state in the payload" % label)
		return
	if label.begins_with("explore"):
		# The whole point of this case: the keys are present and null.
		if not state.has("enemy") or not state.has("encounter"):
			_fail("%s: the payload must carry enemy and encounter" % label)
			return
		if typeof(state.get("enemy")) != TYPE_NIL or typeof(state.get("encounter")) != TYPE_NIL:
			_fail("%s: expected both keys to be null" % label)
			return

	controller.call("_refresh_state", state)

	var title: Label = controller.get("_location_title") as Label
	if title == null:
		_fail("%s: the location title was never built" % label)
		return
	if title.text.strip_edges() == "":
		_fail("%s: the location title stayed empty" % label)
		return
	_ok("%s -> %s" % [label, title.text])


## Open and close every tab, in both directions.
func _tabs_open_and_close(controller: Control) -> void:
	var script: GDScript = controller.get_script() as GDScript
	if script == null:
		_fail("the controller has no script attached")
		return
	var titles: Array = script.get_script_constant_map().get("TAB_TITLES", []) as Array
	if titles.is_empty():
		_fail("TAB_TITLES is empty")
		return

	var overlay: Control = controller.get("_overlay") as Control
	var overlay_title: Label = controller.get("_overlay_title") as Label
	if overlay == null or overlay_title == null:
		_fail("the overlay was never built")
		return

	for index in titles.size():
		var name := str(titles[index])
		controller.call("_open_overlay", index)
		if not overlay.visible:
			_fail("tab %d (%s): the overlay stayed hidden" % [index, name])
			continue
		var expected := name.to_upper()
		if overlay_title.text != expected:
			_fail("tab %d: title %s, expected %s" % [index, overlay_title.text, expected])
			continue
		controller.call("_close_overlay")
		if overlay.visible:
			_fail("tab %d (%s): the overlay stayed open after closing" % [index, name])
			continue
		_tabs += 1
		_ok("tab %d (%s) opened and closed" % [index, name])


func _load_payload() -> Dictionary:
	var arguments: PackedStringArray = OS.get_cmdline_user_args()
	if arguments.is_empty():
		return {}
	var path := str(arguments[0])
	if not FileAccess.file_exists(path):
		return {}
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return {}
	var parsed: Variant = JSON.parse_string(file.get_as_text())
	file.close()
	if typeof(parsed) != TYPE_DICTIONARY:
		return {}
	return parsed


func _ok(text: String) -> void:
	print("OK   %s" % text)


func _fail(text: String) -> void:
	_failures += 1
	print("FAIL %s" % text)


func _report() -> void:
	print("check_smoke: %d tab(s), %d event payload(s), %d failure(s)" % [_tabs, _rendered, _failures])
	get_tree().quit(1 if _failures > 0 else 0)
