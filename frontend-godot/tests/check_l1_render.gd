extends SceneTree

## Headless C.6/C.7 render check: drive the real controller's Talents dialog and
## character-sheet rendering with genuine engine payloads. Run via
##   godot --headless --path frontend-godot -s tests/check_l1_render.gd
## Prints "PASS" only if every assertion holds; exits non-zero otherwise.

var _failures: Array[String] = []


func _check(condition: bool, what: String) -> void:
	if not condition:
		_failures.append(what)
		print("  FAIL: %s" % what)


func _initialize() -> void:
	print("=== L1 render check (C.6 economy + C.7 talent sources) ===")
	var script := load("res://scripts/MainController.gd")
	_check(script != null, "MainController.gd loads")
	if script == null:
		_finish()
		return

	# A real TALENTS payload with a real item_sources block, as the engine now emits.
	var talents := {
		"event": "TALENTS",
		"martial_talent": {"display_name": "No Talent"},
		"body_talent": {"display_name": "Iron Skin Grade"},
		"martial_upgrades": [
			{"target_id": "common_grade_1", "target_name": "Common Grade (1)",
			 "cost": {"talent_refining_elixir": 1}, "affordable": false}
		],
		"body_upgrades": [
			{"target_id": "forged_body_grade", "target_name": "Forged Body Grade",
			 "cost": {"talent_refining_elixir": 1}, "affordable": true}
		],
		"item_sources": {
			"talent_refining_elixir": [
				"Asura Divine Kingdom Black Market (36 spirit stone)",
				"Sky Fortune Cultivator Market (36 spirit stone)"
			]
		},
	}

	var controller: Node = script.new()
	get_root().add_child(controller)
	# Script mode (-s) does not instantiate autoloads, but MainController renders
	# identity art through the ``Profile`` autoload. Provide the real script as a
	# stand-in so ``Profile.current_texture()`` resolves; the compile gate's
	# "Identifier not found: Profile" is the same -s limitation.
	var profile: Node = load("res://scripts/PlayerProfile.gd").new()
	profile.name = "Profile"
	get_root().add_child(profile)
	# add_child(controller) already fired _ready(); a second manual call would
	# rebuild the UI and race the ApiClient, so don't.

	controller._render_event(talents)
	var dialog_text := _subtree_text(controller._dialog.get("content", null))
	# Captions are upper-cased by the dialog builder; compare case-insensitively.
	_check(_has_ci(dialog_text, "can be bought at"), "the sources header is rendered")
	_check(_has_ci(dialog_text, "Asura Divine Kingdom Black Market (36 spirit stone)"),
		"shop names and live prices are rendered (dialog: %s)" % dialog_text.left(260))

	# C.6: the character sheet shows strain against the real cap, plus the trade.
	var player := {
		"name": "Tester",
		"essence_unlocked": true,
		"lifespan": {"display": "88 years"},
		"martial_talent": {"display_name": "No Talent"},
		"body_talent": {"display_name": "Iron Skin Grade"},
		"cultivation_state": {
			"body_transformation": {
				"display_name": "Mortal", "progress": 30.0, "required_progress": 70.0,
				"progress_percent": 43.0, "cultivation_strain": 40.0, "foundation_stability": 100.0,
				"breakthrough": {"gates": {"strain": 40.0, "max_allowed_strain": 45.0,
					"foundation_stability": 100.0, "required_foundation_stability": 70.0}},
				"economy": {
					"strain": 40.0, "strain_cap": 45.0,
					"train": {"strain_gain": 8.0, "strain_after": 48.0,
						"leaves_gate_open": false, "years": 0.05},
					"stabilise": {"strain_reduction": 25.0, "strain_after": 15.0,
						"foundation_stability_gain": 4.0, "years": 0.04}
				}
			},
			"essence_gathering": {
				"display_name": "Houtian", "progress": 0.0, "required_progress": 100.0,
				"progress_percent": 0.0, "cultivation_strain": 0.0,
				"breakthrough": {"gates": {"strain": 0.0, "max_allowed_strain": 45.0}},
				"economy": {"strain": 0.0, "strain_cap": 45.0,
					"train": {"strain_gain": 7.0, "strain_after": 7.0,
						"leaves_gate_open": true, "years": 0.05},
					"stabilise": {"strain_reduction": 25.0, "strain_after": 0.0,
						"foundation_stability_gain": 4.0, "years": 0.04}}
			}
		}
	}
	controller._render_character(player)
	await process_frame
	# RichTextLabel only parses its buffer when drawn, and headless -s never draws,
	# so ``get_parsed_text()`` is always empty here. The sheet line is composed by
	# the pure static UIKit.economy_line (which _render_character delegates to),
	# so assert on it directly; calling _render_character still proves it runs.
	var body_line := UIKit.economy_line(player.cultivation_state.body_transformation.economy)
	var essence_line := UIKit.economy_line(player.cultivation_state.essence_gathering.economy)
	_check(_has_ci(body_line, "40.0 -> 48.0"), "the train trade is rendered with real numbers (line: %s)" % body_line)
	_check(_has_ci(body_line, "closes the gate"), "a gate-closing session is flagged")
	_check(_has_ci(body_line, "Stabilise -25.0 -> 15.0 strain"), "the stabilise trade is rendered")
	_check(_has_ci(essence_line, "gate stays open"), "an open gate is flagged on the essence track")
	_check(controller._character_text != null, "the character sheet RichTextLabel exists after render")

	# TM.2: the top bar's time readout must be the engine's lifespan view, verbatim.
	# (The save-agreement half is tests/test_time_model.py; this is the render half.)
	var lifespan := {
		"age_years": 23.5, "year": 11, "season": "Summer",
		"max_lifespan_years": 120, "remaining_years": 96.5,
		"immortal": false, "display": "Age 23 / 120 years",
	}
	controller._last_world_view = {"season": "Summer"}
	controller._render_top_bar({"name": "Tester", "hp": 10, "max_hp": 10, "qi": 5, "max_qi": 5, "lifespan": lifespan})
	_check(controller._year_label.text == "11", "YEAR shows the engine's elapsed year (got %s)" % controller._year_label.text)
	_check(controller._season_label.text == "Summer", "SEASON shows the engine's season")
	_check(controller._age_label.text == "23 / 120", "AGE shows age / expected death (got %s)" % controller._age_label.text)
	lifespan.immortal = true
	controller._render_top_bar({"name": "Tester", "hp": 10, "max_hp": 10, "qi": 5, "max_qi": 5, "lifespan": lifespan})
	_check(controller._age_label.text == "Immortal", "an immortal reads Immortal, not a number")

	_finish()


func _has_ci(haystack: String, needle: String) -> bool:
	return needle.to_lower() in haystack.to_lower()


func _subtree_text(node: Node) -> String:
	if node == null:
		return ""
	var parts: Array[String] = []
	var stack: Array[Node] = [node]
	while not stack.is_empty():
		var current: Node = stack.pop_back()
		if current is Label or current is RichTextLabel or current is Button:
			var text = current.get("text")
			if text != null and str(text) != "":
				parts.append(str(text))
		for child in current.get_children():
			stack.append(child)
	return " | ".join(parts)


func _finish() -> void:
	if _failures.is_empty():
		print("PASS: L1 render check")
	else:
		print("FAIL: %d check(s)" % _failures.size())
		quit(1)
		return
	quit(0)
