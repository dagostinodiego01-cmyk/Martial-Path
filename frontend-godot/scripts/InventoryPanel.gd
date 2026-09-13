extends MarginContainer
class_name InventoryPanel
## The Inventory tab: the storage-ring grid of item cards.
##
## Owns its own widgets and asks the host to act (``use_requested`` /
## ``equip_requested``) instead of reaching into the controller, so this file has
## exactly one writer. Dressing comes from UIKit; the engine owns every number.

signal use_requested(item_id: String)
signal equip_requested(item_id: String)

var _grid: GridContainer
var _count: Label
var _gold: Label
var _stones: Label


func _ready() -> void:
	size_flags_horizontal = Control.SIZE_EXPAND_FILL
	size_flags_vertical = Control.SIZE_EXPAND_FILL
	add_theme_constant_override("margin_top", 4)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 10)
	add_child(box)

	box.add_child(UIKit.section_header("STORAGE RING"))

	var scroll := UIKit.scroll_box()
	box.add_child(scroll)

	_grid = GridContainer.new()
	_grid.columns = 3
	_grid.add_theme_constant_override("h_separation", 10)
	_grid.add_theme_constant_override("v_separation", 10)
	_grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.add_child(_grid)

	var footer := HBoxContainer.new()
	footer.add_theme_constant_override("separation", 18)
	box.add_child(footer)
	_gold = UIKit.label("Gold 0", 15, UIKit.COLOR_ANTIQUE_GOLD)
	footer.add_child(_gold)
	_stones = UIKit.label("Spirit Stones 0", 15, UIKit.COLOR_INVENTORY_BLUE)
	footer.add_child(_stones)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	footer.add_child(spacer)
	_count = UIKit.label("0 / %d" % UIKit.INVENTORY_CAPACITY, 13, UIKit.COLOR_MUTED)
	footer.add_child(_count)


func render(state: Dictionary) -> void:
	var items: Array = state.get("inventory_items", [])
	var player: Dictionary = state.get("player", {})
	_count.text = "%d / %d" % [items.size(), UIKit.INVENTORY_CAPACITY]
	UIKit.clear(_grid)
	var stones := 0
	for item in items:
		if typeof(item) != TYPE_DICTIONARY:
			continue
		if str(item.get("item_id", "")) == "spirit_stone":
			stones = int(item.get("count", 0))
		_grid.add_child(_make_item_card(item))
	if items.is_empty():
		_grid.add_child(UIKit.empty_note("Your storage ring is empty."))
	_gold.text = "Gold %s" % player.get("gold", 0)
	_stones.text = "Spirit Stones %s" % stones


func _make_item_card(item: Dictionary) -> PanelContainer:
	var card := PanelContainer.new()
	var rarity := str(item.get("rarity", ""))
	var rarity_col := UIKit.rarity_color(rarity)
	card.add_theme_stylebox_override("panel", UIKit.item_card_style(rarity_col))
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 4)
	card.add_child(box)

	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 8)
	box.add_child(head)
	var name_label := UIKit.word_wrap(UIKit.label(str(item.get("name", "Item")), 15, UIKit.COLOR_PRIMARY_TEXT))
	name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head.add_child(name_label)
	var count := UIKit.format_quantity(item.get("count", 1))
	if count != "1":
		head.add_child(UIKit.label("x%s" % count, 14, UIKit.COLOR_ANTIQUE_GOLD))

	var meta_bits: Array[String] = []
	var type := str(item.get("type", ""))
	if rarity != "":
		meta_bits.append(rarity.replace("_", " ").capitalize())
	if type == "equipment":
		var slots: Array = item.get("valid_slots", [])
		if not slots.is_empty():
			var slot_names: Array[String] = []
			for slot in slots:
				slot_names.append(UIKit.title_from_id(str(slot)))
			meta_bits.append(", ".join(slot_names))
	if bool(item.get("usable", false)):
		meta_bits.append("usable")
	if not meta_bits.is_empty():
		box.add_child(UIKit.label(" - ".join(meta_bits), 11, rarity_col))

	var desc := str(item.get("description", ""))
	if desc != "":
		box.add_child(UIKit.word_wrap(UIKit.label(desc, 12, UIKit.COLOR_SECONDARY_TEXT)))

	var mods := UIKit.format_item_modifiers(item)
	if mods != "":
		box.add_child(UIKit.word_wrap(UIKit.label(mods, 12, UIKit.COLOR_BODY)))

	# Direct item actions on the card.
	var item_id := str(item.get("item_id", ""))
	if item_id == "":
		return card
	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 6)
	box.add_child(actions)
	if bool(item.get("usable", false)):
		actions.add_child(UIKit.button(
			"Use",
			func(): use_requested.emit(item_id),
			"Use %s." % str(item.get("name", item_id))
		))
	if type == "equipment" and not item.get("valid_slots", []).is_empty():
		actions.add_child(UIKit.button(
			"Equip",
			func(): equip_requested.emit(item_id),
			"Choose a slot for %s." % str(item.get("name", item_id))
		))
	return card
