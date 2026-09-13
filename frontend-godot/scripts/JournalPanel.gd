extends MarginContainer
class_name JournalPanel
## The Journal tab: the cards for endeavors the player is actually on.
##
## Locked and hidden quests are deliberately not shown -- the journal is a
## to-do list, not a spoiler reel.

var _quests: VBoxContainer


func _ready() -> void:
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_theme_constant_override("margin_top", 4)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 10)
	add_child(box)

	box.add_child(UIKit.section_header("ACTIVE ENDEAVORS"))

	var scroll := UIKit.scroll_box()
	box.add_child(scroll)

	_quests = VBoxContainer.new()
	_quests.add_theme_constant_override("separation", 10)
	_quests.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_quests)


func render(quests: Array) -> void:
	UIKit.clear(_quests)
	var has_active := false
	for quest in quests:
		if typeof(quest) != TYPE_DICTIONARY:
			continue
		var status := str(quest.get("status", "locked"))
		if status == "locked" or status == "hidden":
			continue
		has_active = true
		_quests.add_child(_make_quest_card(quest))
	if not has_active:
		_quests.add_child(UIKit.empty_note("No active quests yet. Explore to uncover your path."))


func _make_quest_card(quest: Dictionary) -> PanelContainer:
	var card := PanelContainer.new()
	var status := str(quest.get("status", "active"))
	var done := status == "completed"
	var accent := UIKit.COLOR_SUCCESS if done else UIKit.COLOR_ANTIQUE_GOLD
	card.add_theme_stylebox_override("panel", UIKit.accent_card_style(accent))

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 5)
	card.add_child(box)

	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 10)
	box.add_child(head)
	head.add_child(UIKit.label(str(quest.get("title", "Quest")), 16, UIKit.COLOR_PRIMARY_TEXT))
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(spacer)
	head.add_child(UIKit.label(
		("COMPLETED" if done else status.capitalize()).to_upper(),
		11,
		UIKit.COLOR_SUCCESS if done else UIKit.COLOR_MUTED
	))

	var desc := str(quest.get("description", ""))
	if desc != "":
		box.add_child(UIKit.word_wrap(UIKit.label(desc, 12, UIKit.COLOR_SECONDARY_TEXT)))

	for objective in quest.get("objectives", []):
		var cur := int(objective.get("current", 0))
		var req := int(max(1, int(objective.get("required", 1))))
		var complete := cur >= req
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 8)
		box.add_child(row)
		row.add_child(UIKit.label("x" if complete else ">", 11, UIKit.COLOR_SUCCESS if complete else UIKit.COLOR_MUTED))
		var obj_label := UIKit.label(
			str(objective.get("text", "Objective")),
			12,
			UIKit.COLOR_MUTED if complete else UIKit.COLOR_PRIMARY_TEXT
		)
		obj_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(obj_label)
		row.add_child(UIKit.label(
			"%d / %d" % [cur, req],
			12,
			UIKit.COLOR_SUCCESS if complete else UIKit.COLOR_SECONDARY_TEXT
		))
		if not complete:
			var bar := UIKit.progress_bar(UIKit.COLOR_BODY, UIKit.COLOR_BODY_DARK)
			bar.min_value = 0
			bar.max_value = req
			bar.value = cur
			row.add_child(bar)
	return card
