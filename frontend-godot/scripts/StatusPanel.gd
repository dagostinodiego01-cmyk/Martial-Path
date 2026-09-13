extends MarginContainer
class_name StatusPanel
## The Status tab: the structured character sheet beside the realm ladder.
##
## The ladder is the lifetime spine -- body realms walked so far stay lit, the
## current rung is gold, and the rungs ahead are dim. Essence is one rung that is
## either open or locked with its unlock requirement stated.

var _sheet: GridContainer
var _ladder: VBoxContainer


func _ready() -> void:
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_theme_constant_override("margin_top", 4)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 10)
	add_child(box)

	var columns := HBoxContainer.new()
	columns.add_theme_constant_override("separation", 18)
	columns.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	columns.size_flags_vertical = Control.SIZE_EXPAND_FILL
	box.add_child(columns)

	# Left: the structured character sheet.
	var sheet_box := VBoxContainer.new()
	sheet_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sheet_box.size_flags_stretch_ratio = 1.4
	columns.add_child(sheet_box)
	sheet_box.add_child(UIKit.section_header("CHARACTER SHEET"))
	var sheet_scroll := UIKit.scroll_box()
	sheet_box.add_child(sheet_scroll)
	_sheet = GridContainer.new()
	_sheet.columns = 2
	_sheet.add_theme_constant_override("h_separation", 26)
	_sheet.add_theme_constant_override("v_separation", 8)
	_sheet.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	sheet_scroll.add_child(_sheet)

	# Right: the realm ladder -- the lifetime spine.
	var ladder_box := VBoxContainer.new()
	ladder_box.custom_minimum_size = Vector2(280, 0)
	columns.add_child(ladder_box)
	ladder_box.add_child(UIKit.section_header("THE ASCENT"))
	var ladder_scroll := UIKit.scroll_box()
	ladder_box.add_child(ladder_scroll)
	_ladder = VBoxContainer.new()
	_ladder.add_theme_constant_override("separation", 6)
	_ladder.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	ladder_scroll.add_child(_ladder)


func render(player: Dictionary) -> void:
	var cultivation: Dictionary = player.get("cultivation_state", {})
	var body: Dictionary = cultivation.get("body_transformation", {})
	var essence: Dictionary = cultivation.get("essence_gathering", {})
	var martial_talent: Dictionary = player.get("martial_talent", {})
	var body_talent: Dictionary = player.get("body_talent", {})
	var lifespan: Dictionary = player.get("lifespan", {})
	var balance: Dictionary = cultivation.get("balance", {})
	var safety: Dictionary = cultivation.get("breakthrough_safety", {})
	var effective: Dictionary = player.get("effective_stats", {})

	UIKit.clear(_sheet)
	_add_row("HP", "%s / %s" % [player.get("hp", 0), player.get("max_hp", 0)], UIKit.COLOR_HP)
	_add_row("Qi", "%s / %s" % [player.get("qi", 0), player.get("max_qi", 0)], UIKit.COLOR_QI)
	_add_row("Attack", str(player.get("attack", 0)))
	_add_row("Defense", str(player.get("defense", 0)))
	if not effective.is_empty():
		_add_row("Effective ATK / DEF", "%s / %s" % [effective.get("attack", player.get("attack", 0)), effective.get("defense", player.get("defense", 0))], UIKit.COLOR_ANTIQUE_GOLD)
	_add_row("Comprehension", str(player.get("comprehension", 0)))
	_add_row("Insight", str(player.get("insight", 0)))
	_add_row("Reputation", str(player.get("reputation", 0)))
	_add_row("Morality", str(player.get("morality", 0)))
	_add_row("EXP", str(player.get("exp", 0)))
	_add_row("Martial Talent", str(martial_talent.get("display_name", "Unknown")), UIKit.COLOR_ESSENCE)
	_add_row("Body Talent", str(body_talent.get("display_name", "Unknown")), UIKit.COLOR_BODY)
	_add_row("Lifespan", str(lifespan.get("display", "Unknown")), UIKit.COLOR_TITLE_GOLD)
	_add_row("Body Foundation", str(body.get("foundation", 0)), UIKit.COLOR_BODY)
	_add_row("Cultivation Strain", "%s / 100" % body.get("cultivation_strain", 0), UIKit.COLOR_WARNING)
	_add_row("Foundation Stability", "%s / 100" % body.get("foundation_stability", 100), UIKit.COLOR_SUCCESS)
	_add_row("Soul Strength", str(player.get("soul_strength", 0)), UIKit.COLOR_ESSENCE)
	_add_row("Foundation Quality", str(player.get("foundation_quality", 0)))
	_add_row("Balance", str(balance.get("status", "-")))
	_add_row("Breakthrough Safety", "%s (%s)" % [safety.get("level", "-"), safety.get("score", 0)])
	_add_row("Location", str(player.get("current_location", "unknown")), UIKit.COLOR_QI)
	_add_row("Ancestral Memory", str(player.get("max_story_tier", "-")), UIKit.COLOR_ANTIQUE_GOLD)

	# The realm ladder: the lifetime spine. Body realms walked so far are lit.
	UIKit.clear(_ladder)
	var body_realm := str(body.get("realm_id", "mortal"))
	var ladder := [
		["mortal", "Mortal"], ["strength_training", "Strength Training"],
		["body_tempering", "Body Tempering"], ["pulse_condensation", "Pulse Condensation"],
		["marrow_cleansing", "Marrow Cleansing"],
	]
	var reached_current := true
	for step in ladder:
		var step_id := str(step[0])
		var is_current := step_id == body_realm
		if is_current:
			reached_current = true
		_add_ladder_step(str(step[1]), reached_current or is_current, is_current, "you stand here" if is_current else "")
	# Essence: one rung that is either open or locked.
	if bool(player.get("essence_unlocked", true)):
		_add_ladder_step("Essence: %s" % essence.get("display_name", "-"), true, false, "")
	else:
		_add_ladder_step("Essence: locked", false, false, str(essence.get("unlock_requirement", "")))


func _add_row(label_text: String, value: String, color: Color = UIKit.COLOR_PRIMARY_TEXT) -> void:
	_sheet.add_child(UIKit.label(label_text, 13, UIKit.COLOR_MUTED))
	_sheet.add_child(UIKit.label(value, 13, color))


func _add_ladder_step(step_name: String, reached: bool, current: bool, note: String) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	_ladder.add_child(row)
	row.add_child(UIKit.label(
		"=" if reached else "-",
		13,
		UIKit.COLOR_ANTIQUE_GOLD if reached else UIKit.COLOR_SLOT_EMPTY_BORDER
	))
	var name_col := UIKit.COLOR_TITLE_GOLD if current else (UIKit.COLOR_PRIMARY_TEXT if reached else UIKit.COLOR_MUTED)
	var step_label := UIKit.label(step_name, 13, name_col)
	step_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(step_label)
	if note != "":
		row.add_child(UIKit.label(note, 11, UIKit.COLOR_MUTED))
