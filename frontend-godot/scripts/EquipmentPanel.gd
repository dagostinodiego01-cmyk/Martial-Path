extends MarginContainer
class_name EquipmentPanel
## The Equipment tab: the paper-doll grid of worn artifacts plus the aggregated
## bonus tally. Read-only -- the engine owns what is worn; the player changes it
## from an inventory card or the UNEQUIP action.

var _slots: GridContainer
var _count: Label
var _bonus: RichTextLabel


func _ready() -> void:
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_theme_constant_override("margin_top", 4)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 10)
	add_child(box)

	_count = UIKit.label("0 / %d worn" % UIKit.EQUIPMENT_SLOT_ORDER.size(), 13, UIKit.COLOR_MUTED)
	box.add_child(UIKit.section_header("WORN ARTIFACTS", _count))

	# Aggregated bonus tally: everything worn gear currently contributes.
	_bonus = RichTextLabel.new()
	_bonus.bbcode_enabled = true
	_bonus.fit_content = true
	_bonus.add_theme_color_override("default_color", UIKit.COLOR_SECONDARY_TEXT)
	box.add_child(_bonus)

	var scroll := UIKit.scroll_box()
	box.add_child(scroll)

	_slots = GridContainer.new()
	_slots.columns = 3
	_slots.add_theme_constant_override("h_separation", 10)
	_slots.add_theme_constant_override("v_separation", 10)
	_slots.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_slots)


func render(player: Dictionary) -> void:
	var slots: Dictionary = player.get("equipment", {})
	var details: Dictionary = player.get("equipment_details", {})
	var modifiers: Dictionary = player.get("equipment_modifiers", {})
	UIKit.clear(_slots)
	var worn := 0
	for pair in UIKit.EQUIPMENT_SLOT_ORDER:
		var slot_id := str(pair[0])
		var slot_label := str(pair[1])
		var item_id = slots.get(slot_id, null)
		var info: Dictionary = details.get(slot_id, {})
		if item_id == null or str(item_id) == "":
			_slots.add_child(_make_slot_card(slot_label, "(empty)", "", UIKit.COLOR_MUTED, -1, -1, "", slot_id))
			continue
		worn += 1
		var durability: Variant = info.get("durability", null)
		var max_durability: Variant = info.get("max_durability", null)
		var name_color := UIKit.COLOR_PRIMARY_TEXT if not bool(info.get("broken", false)) else UIKit.COLOR_DANGER
		_slots.add_child(_make_slot_card(
			slot_label,
			str(info.get("display_name", item_id)),
			str(info.get("rarity", "")),
			name_color,
			durability,
			max_durability,
			UIKit.format_item_modifiers(info),
			slot_id
		))
	_count.text = "%d / %d worn" % [worn, UIKit.EQUIPMENT_SLOT_ORDER.size()]
	_render_tally(modifiers)


func _make_slot_card(
	slot_label: String,
	item_name: String,
	rarity: String,
	name_color: Color,
	durability: Variant,
	max_durability: Variant,
	modifiers: String = "",
	slot_id: String = ""
) -> PanelContainer:
	var card := PanelContainer.new()
	var is_empty := item_name == "(empty)"
	card.add_theme_stylebox_override(
		"panel",
		UIKit.panel_style(
			UIKit.COLOR_SECONDARY_BACKGROUND if is_empty else UIKit.COLOR_PANEL_SOFT,
			UIKit.COLOR_SLOT_EMPTY_BORDER if is_empty else UIKit.COLOR_BORDER,
			1
		)
	)
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 3)
	card.add_child(box)
	box.add_child(UIKit.label(slot_label.to_upper(), 10, UIKit.COLOR_ANTIQUE_GOLD))
	box.add_child(UIKit.word_wrap(UIKit.label(item_name, 14, name_color)))
	if rarity != "":
		box.add_child(UIKit.label(rarity.replace("_", " ").capitalize(), 10, UIKit.rarity_color(rarity)))
	if modifiers != "":
		box.add_child(UIKit.word_wrap(UIKit.label(modifiers, 10, UIKit.COLOR_BODY)))
	if typeof(durability) == TYPE_INT and typeof(max_durability) == TYPE_INT and int(max_durability) > 0:
		box.add_child(UIKit.label(
			"Durability %s / %s" % [durability, max_durability],
			10,
			UIKit.COLOR_WARNING if int(durability) <= 0 else UIKit.COLOR_MUTED
		))
	if is_empty and slot_id != "":
		box.add_child(UIKit.word_wrap(UIKit.label("Nothing worn here.", 10, UIKit.COLOR_MUTED)))
	return card


func _render_tally(modifiers: Dictionary) -> void:
	var lines := "[color=#C9A24D]TOTAL BONUSES[/color]   "
	var parts: Array[String] = []
	var stat_line := UIKit.format_modifier_group(modifiers.get("stat_modifiers", {}))
	if stat_line != "":
		parts.append("[color=#E7DDC6]Stats:[/color] %s" % stat_line)
	var cult_line := UIKit.format_modifier_group(modifiers.get("cultivation_modifiers", {}))
	if cult_line != "":
		parts.append("[color=#4FA8D8]Cultivation:[/color] %s" % cult_line)
	var util_line := UIKit.format_modifier_group(modifiers.get("utility_modifiers", {}))
	if util_line != "":
		parts.append("[color=#7CA558]Utility:[/color] %s" % util_line)
	if parts.is_empty():
		lines += "[color=#8E8471]Nothing worn grants a bonus yet.[/color]"
	else:
		lines += "   ".join(parts)
	UIKit.set_rich_text(_bonus, lines)
