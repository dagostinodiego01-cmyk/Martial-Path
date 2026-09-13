extends SceneTree
## Headless smoke check for the Godot panels.
##
## The Python suite owns the engine, and `--check-only` only parses GDScript -- so
## nothing caught a panel that built or rendered wrong until a player opened the
## tab. This builds every panel from a synthetic state payload, renders it, and
## asserts the text a player would read actually reached the tree.
##
## Run:  godot --headless --path frontend-godot -s res://tests/check_panels.gd
## Exit: 0 when every panel renders its expectations, 1 otherwise.

var _failures := 0
var _ran := false


func _process(_delta: float) -> bool:
	if not _ran:
		_ran = true
		_run()
	return true


func _run() -> void:
	var payload := _state_payload()
	var player: Dictionary = payload["player"]

	_check("InventoryPanel", InventoryPanel.new(), func(p): p.render(payload), [
		"STORAGE RING", "Healing Pill", "Iron Sword", "x2", "2 / 50", "Gold 25",
	])
	_check("EquipmentPanel", EquipmentPanel.new(), func(p): p.render(player), [
		"WORN ARTIFACTS", "WEAPON", "Iron Sword", "1 / 11 worn", "TOTAL BONUSES", "Max HP",
	])
	_check("JournalPanel", JournalPanel.new(), func(p): p.render(payload["quests"]), [
		"ACTIVE ENDEAVORS", "First Steps", "Train once", "0 / 1",
	])
	# The journal is a to-do list: locked and hidden endeavors must stay out of it.
	_check("JournalPanel hides locked quests", JournalPanel.new(), func(p): p.render(payload["quests"]), [], ["Spoiler"])
	_check("StatusPanel", StatusPanel.new(), func(p): p.render(player), [
		"CHARACTER SHEET", "THE ASCENT", "Strength Training", "you stand here",
		"Cultivation Strain", "Breakthrough Safety",
	])
	_check("TechniquesPanel", TechniquesPanel.new(), func(p): p.render(player, payload["cooldowns"]), [
		"KNOWN ARTS", "ACTIVE", "Iron Fist", "recovering - 1 turn(s)",
	])

	print("check_panels: %d panel check(s) failed" % _failures)
	quit(1 if _failures > 0 else 0)


## Render a panel and assert which needles must (and must not) show up in the text
## it produced.
func _check(name: String, panel: Control, do_render: Callable, expect: Array, forbidden: Array = []) -> void:
	root.add_child(panel)
	do_render.call(panel)
	var text := _text_of(panel)
	root.remove_child(panel)
	panel.free()

	var problems: Array[String] = []
	for needle in expect:
		if not text.contains(str(needle)):
			problems.append("missing %s" % str(needle))
	for needle in forbidden:
		if text.contains(str(needle)):
			problems.append("unexpectedly present: %s" % str(needle))
	if text.strip_edges().length() < 40:
		problems.append("rendered almost nothing (%d chars)" % text.strip_edges().length())

	if problems.is_empty():
		print("OK   %s" % name)
		return
	_failures += 1
	print("FAIL %s: %s" % [name, "; ".join(problems)])


## Every player-visible string in a panel subtree.
func _text_of(node: Node) -> String:
	var out := ""
	if node is Label:
		out += (node as Label).text + "\n"
	elif node is RichTextLabel:
		out += (node as RichTextLabel).get_parsed_text() + "\n"
	elif node is Button:
		out += (node as Button).text + "\n"
	for child in node.get_children():
		out += _text_of(child)
	return out


## A payload shaped like the engine's /state response, covering every field the
## panels read. Synthetic so the check never depends on a running backend.
func _state_payload() -> Dictionary:
	var body := {
		"display_name": "Mortal",
		"realm_id": "mortal",
		"progress": 10.0,
		"required_progress": 100.0,
		"progress_percent": 10.0,
		"cultivation_strain": 3,
		"foundation_stability": 90,
		"foundation": 1,
	}
	var essence := {
		"display_name": "Early Houtian",
		"progress": 0.0,
		"required_progress": 100.0,
		"progress_percent": 0.0,
		"cultivation_strain": 0,
	}
	var player := {
		"name": "Daoist",
		"hp": 100, "max_hp": 100, "qi": 50, "max_qi": 50,
		"attack": 15, "defense": 5, "gold": 25,
		"comprehension": 3, "insight": 1, "reputation": 0, "morality": 0, "exp": 12,
		"soul_strength": 1, "foundation_quality": 2, "current_location": "outer_forest",
		"max_story_tier": 1, "essence_unlocked": true,
		"cultivation_state": {
			"body_transformation": body,
			"essence_gathering": essence,
			"balance": {"status": "Balanced"},
			"breakthrough_safety": {"level": "Safe", "score": 70},
		},
		"martial_talent": {"display_name": "Average"},
		"body_talent": {"display_name": "Sturdy"},
		"lifespan": {
			"display": "12 / 100", "age_years": 12.0, "remaining_years": 88.0,
			"year": 1, "immortal": false,
		},
		"equipment": {"weapon": "iron_sword"},
		"equipment_details": {
			"weapon": {
				"display_name": "Iron Sword", "rarity": "uncommon",
				"durability": 9, "max_durability": 10, "broken": false,
			},
		},
		"equipment_modifiers": {"stat_modifiers": {"max_hp": 10.0, "attack": 3.0}},
		"skills": [{
			"id": "basic_punch", "name": "Iron Fist", "category": "Active",
			"type": "active", "qi_cost": 5, "cooldown": 2,
			"description": "A straight punch.", "effect_label": "Impact",
		}],
	}
	var inventory := [
		{
			"item_id": "healing_pill", "name": "Healing Pill", "rarity": "common",
			"count": 2, "type": "consumable", "usable": true,
			"description": "Mends flesh.",
		},
		{
			"item_id": "iron_sword", "name": "Iron Sword", "rarity": "uncommon",
			"count": 1, "type": "equipment", "valid_slots": ["weapon"],
			"stat_modifiers": {"attack": 3.0},
		},
	]
	var quests := [
		{
			"title": "First Steps", "status": "active", "description": "Begin your path.",
			"objectives": [{"text": "Train once", "current": 0, "required": 1}],
		},
		{"title": "Spoiler", "status": "locked", "description": "Not yet.", "objectives": []},
	]
	return {
		"player": player,
		"inventory_items": inventory,
		"quests": quests,
		"cooldowns": {"basic_punch": 1},
	}
