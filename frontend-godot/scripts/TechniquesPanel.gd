extends MarginContainer
class_name TechniquesPanel
## The Techniques tab: known arts grouped by category (Active / Stats / Growth /
## Passive), each card carrying its cost and whether it is still recovering.
##
## Cooldowns are handed in per render rather than cached, so a card can never
## claim a skill is ready when the engine says it is not.

const CATEGORY_ORDER := ["Active", "Stats", "Growth", "Passive"]

var _list: VBoxContainer


func _ready() -> void:
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_theme_constant_override("margin_top", 4)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 10)
	add_child(box)

	box.add_child(UIKit.section_header("KNOWN ARTS"))

	var scroll := UIKit.scroll_box()
	box.add_child(scroll)

	_list = VBoxContainer.new()
	_list.add_theme_constant_override("separation", 10)
	_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_list)


func render(player: Dictionary, cooldowns: Dictionary) -> void:
	var skills = player.get("skills", [])
	UIKit.clear(_list)
	if skills.is_empty():
		_list.add_child(UIKit.empty_note("No techniques known yet. Seek a master or join a sect."))
		return
	var groups := {"Active": [], "Stats": [], "Growth": [], "Passive": []}
	for skill in skills:
		if typeof(skill) == TYPE_DICTIONARY:
			var category := str(skill.get("category", ""))
			if category == "" or category == "unknown":
				category = "Active" if str(skill.get("type", "")) == "active" else "Passive"
			if not groups.has(category):
				groups[category] = []
			groups[category].append(skill)
		else:
			groups["Passive"].append(str(skill))
	for category in CATEGORY_ORDER:
		if groups[category].is_empty():
			continue
		_list.add_child(UIKit.label(category.to_upper(), 12, UIKit.COLOR_MUTED))
		for skill in groups[category]:
			if typeof(skill) == TYPE_DICTIONARY:
				_list.add_child(_make_technique_card(skill, category, cooldowns))
			else:
				_list.add_child(UIKit.label(UIKit.title_from_id(str(skill)), 14, UIKit.COLOR_PRIMARY_TEXT))


func _make_technique_card(skill: Dictionary, category: String, cooldowns: Dictionary) -> PanelContainer:
	var card := PanelContainer.new()
	var accent := UIKit.COLOR_ANTIQUE_GOLD
	match category:
		"Stats":
			accent = UIKit.COLOR_BODY
		"Growth":
			accent = UIKit.COLOR_QI
		"Passive":
			accent = UIKit.COLOR_ESSENCE
	card.add_theme_stylebox_override("panel", UIKit.accent_card_style(accent))

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	card.add_child(box)

	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 10)
	box.add_child(head)
	head.add_child(UIKit.label(str(skill.get("name", skill.get("id", "Technique"))), 15, UIKit.COLOR_PRIMARY_TEXT))
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(spacer)

	var meta_bits: Array[String] = []
	var recovering := false
	if category == "Active":
		meta_bits.append("Qi %s" % skill.get("qi_cost", 0))
		meta_bits.append("Cooldown %s" % skill.get("cooldown", 0))
		var cd_left := int(cooldowns.get(str(skill.get("id", "")), 0))
		if cd_left > 0:
			meta_bits.append("recovering - %d turn(s)" % cd_left)
			recovering = true
		if int(skill.get("insight_required", 0)) > 0:
			meta_bits.append("Insight %s" % skill.get("insight_required", 0))
	if str(skill.get("effect_label", "")) != "":
		meta_bits.append(str(skill.get("effect_label", "")))
	if not meta_bits.is_empty():
		head.add_child(UIKit.label(
			"  -  ".join(meta_bits),
			12,
			UIKit.COLOR_WARNING if recovering else UIKit.COLOR_MUTED
		))

	var desc := str(skill.get("description", ""))
	if desc != "":
		box.add_child(UIKit.word_wrap(UIKit.label(desc, 12, UIKit.COLOR_SECONDARY_TEXT)))
	return card
