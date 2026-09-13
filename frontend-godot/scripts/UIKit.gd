extends RefCounted
class_name UIKit
## The shared presentation kit: the lacquer-and-gold palette the whole client is
## carved from, plus the stateless widget/stylebox/formatting factories every
## panel needs.
##
## Static and dependency-free on purpose. Any Control can dress itself with it
## without inheriting a controller, so each panel script stays a single writer's
## file: panels own their layout and their own widget refs, this owns only how a
## panel, label, button, bar or chip looks.
##
## The palette is the committed world (DESIGN.md): warm ink ground, gold hairline
## frames, parchment text, cinnabar seals, qi cyan.


# --- Palette -----------------------------------------------------------------

const COLOR_BACKGROUND := Color("12100B")
const COLOR_SECONDARY_BACKGROUND := Color("171410")
const COLOR_PANEL := Color("1C1813")
const COLOR_PANEL_SOFT := Color("242019")
const COLOR_PANEL_RAISED := Color("2A241B")
const COLOR_BORDER := Color("4B3E22")
const COLOR_BORDER_STRONG := Color("C9A24D")
const COLOR_PRIMARY_TEXT := Color("E7DDC6")
const COLOR_SECONDARY_TEXT := Color("BFB298")
const COLOR_MUTED := Color("8E8471")
const COLOR_TITLE_GOLD := Color("E4C87F")
const COLOR_ANTIQUE_GOLD := Color("C9A24D")
const COLOR_SEAL_RED := Color("B03A2E")
const COLOR_QI := Color("4FA8D8")
const COLOR_QI_DARK := Color("12222C")
const COLOR_HP := Color("C4443C")
const COLOR_HP_DARK := Color("2B1210")
const COLOR_BODY := Color("7CA558")
const COLOR_BODY_DARK := Color("1A2314")
const COLOR_ESSENCE := Color("A87ED8")
const COLOR_INVENTORY_BLUE := Color("4FA8D8")
const COLOR_WARNING := Color("D9A441")
const COLOR_DANGER := Color("C4443C")
const COLOR_SUCCESS := Color("7CA558")
## The "nothing worn here" frame: a shade quieter than an empty slot normally is.
const COLOR_SLOT_EMPTY_BORDER := Color("3A3225")

const DISPLAY_FONT := preload("res://ui/fonts/Cinzel.ttf")

## Display-only cap, mirroring the engine's storage ring size.
const INVENTORY_CAPACITY := 50

## Every equipment slot, in paper-doll order, paired with its player-facing name.
const EQUIPMENT_SLOT_ORDER := [
	["weapon", "Weapon"],
	["armor", "Armor"],
	["boots", "Boots"],
	["cloak", "Cloak"],
	["ring_1", "Ring I"],
	["ring_2", "Ring II"],
	["amulet", "Amulet"],
	["talisman", "Talisman"],
	["artifact_1", "Artifact I"],
	["artifact_2", "Artifact II"],
	["flying_sword", "Flying Sword"],
]


# --- Styleboxes --------------------------------------------------------------

static func panel_style(fill: Color, border: Color = COLOR_BORDER, border_width: int = 1) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = fill
	style.border_color = border
	style.set_border_width_all(border_width)
	style.set_corner_radius_all(0)
	style.content_margin_left = 16
	style.content_margin_right = 16
	style.content_margin_top = 14
	style.content_margin_bottom = 14
	return style


static func popup_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = Color("171310")
	style.border_color = COLOR_BORDER_STRONG
	style.set_border_width_all(1)
	style.set_corner_radius_all(0)
	style.content_margin_left = 18
	style.content_margin_right = 18
	style.content_margin_top = 16
	style.content_margin_bottom = 16
	style.shadow_color = Color(0, 0, 0, 0.55)
	style.shadow_size = 28
	style.shadow_offset = Vector2(0, 8)
	return style


static func button_style(fill: Color, border: Color) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = fill
	style.border_color = border
	style.set_border_width_all(1)
	style.set_corner_radius_all(0)
	style.content_margin_left = 12
	style.content_margin_right = 12
	style.content_margin_top = 7
	style.content_margin_bottom = 7
	return style


static func bar_background_style(fill: Color) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = fill
	style.border_color = COLOR_BORDER
	style.set_border_width_all(1)
	style.set_corner_radius_all(0)
	return style


static func chip_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = COLOR_PANEL_RAISED
	style.border_color = COLOR_BORDER
	style.set_border_width_all(1)
	style.set_corner_radius_all(0)
	style.content_margin_left = 10
	style.content_margin_right = 10
	style.content_margin_top = 4
	style.content_margin_bottom = 4
	return style


static func portrait_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = COLOR_PANEL_SOFT
	style.border_color = COLOR_BORDER_STRONG
	style.set_border_width_all(1)
	style.set_corner_radius_all(0)
	return style


## A card whose rarity rides its top edge (the inventory item card).
static func item_card_style(accent: Color) -> StyleBoxFlat:
	var style := panel_style(COLOR_PANEL_SOFT, accent, 1)
	style.border_width_top = 2
	return style


## A card whose category rides its left edge (quest and technique cards).
static func accent_card_style(accent: Color) -> StyleBoxFlat:
	var style := panel_style(COLOR_PANEL_SOFT, accent, 1)
	style.border_width_left = 3
	return style


# --- Widgets -----------------------------------------------------------------

static func label(text: String, size: int, color: Color, display: bool = false) -> Label:
	var out := Label.new()
	out.text = text
	out.add_theme_font_size_override("font_size", size)
	out.add_theme_color_override("font_color", color)
	if display:
		out.add_theme_font_override("font", DISPLAY_FONT)
	# Keep single-line labels from collapsing to one-character-per-line when a
	# sibling (e.g. an expanding spacer in a header row) squeezes their width.
	# Long-form copy uses RichTextLabel, so plain labels never need wrapping.
	out.autowrap_mode = TextServer.AUTOWRAP_OFF
	return out


static func button(text: String, cb: Callable, tooltip: String = "") -> Button:
	var out := Button.new()
	out.text = text
	out.tooltip_text = tooltip
	out.pressed.connect(cb)
	out.add_theme_color_override("font_color", COLOR_PRIMARY_TEXT)
	out.add_theme_color_override("font_hover_color", COLOR_TITLE_GOLD)
	out.add_theme_stylebox_override("normal", button_style(COLOR_PANEL_SOFT, COLOR_BORDER))
	out.add_theme_stylebox_override("hover", button_style(Color("332A1A"), COLOR_ANTIQUE_GOLD))
	out.add_theme_stylebox_override("pressed", button_style(COLOR_SECONDARY_BACKGROUND, COLOR_ANTIQUE_GOLD))
	return out


static func panel(fill: Color = COLOR_PANEL, border: Color = COLOR_BORDER, border_width: int = 1) -> PanelContainer:
	var out := PanelContainer.new()
	out.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	out.add_theme_stylebox_override("panel", panel_style(fill, border, border_width))
	return out


static func apply_bar_style(bar: ProgressBar, color: Color, background_color: Color) -> void:
	bar.add_theme_stylebox_override("background", bar_background_style(background_color))
	var fill := StyleBoxFlat.new()
	fill.bg_color = color
	fill.set_corner_radius_all(0)
	bar.add_theme_stylebox_override("fill", fill)


static func bar_group(caption: String, color: Color, background_color: Color) -> Dictionary:
	var box := VBoxContainer.new()
	box.custom_minimum_size = Vector2(150, 0)
	var cap := label(caption, 12, COLOR_MUTED)
	box.add_child(cap)
	var bar := ProgressBar.new()
	bar.min_value = 0
	bar.max_value = 100
	bar.value = 0
	bar.show_percentage = false
	bar.custom_minimum_size = Vector2(150, 16)
	apply_bar_style(bar, color, background_color)
	box.add_child(bar)
	return {"box": box, "bar": bar, "cap": cap}


static func progress_bar(color: Color, background_color: Color, height: float = 8.0, width: float = 90.0) -> ProgressBar:
	var bar := ProgressBar.new()
	bar.show_percentage = false
	bar.custom_minimum_size = Vector2(width, height)
	apply_bar_style(bar, color, background_color)
	return bar


static func chip(caption: String, value: String, color: Color) -> PanelContainer:
	var out := PanelContainer.new()
	out.add_theme_stylebox_override("panel", chip_style())
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 6)
	out.add_child(row)
	row.add_child(label(caption, 11, COLOR_MUTED))
	row.add_child(label(value, 12, color))
	return out


## The "caption ..... trailing" row every tab page opens with.
static func section_header(caption: String, trailing: Label = null) -> HBoxContainer:
	var header := HBoxContainer.new()
	header.add_child(label(caption, 13, COLOR_MUTED))
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(spacer)
	if trailing != null:
		header.add_child(trailing)
	return header


static func scroll_box() -> ScrollContainer:
	var scroll := ScrollContainer.new()
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	return scroll


static func empty_note(text: String) -> Label:
	return label(text, 14, COLOR_MUTED)


static func word_wrap(target: Label) -> Label:
	target.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return target


static func set_rich_text(control: RichTextLabel, text: String) -> void:
	control.clear()
	control.append_text(text)


static func clear(container: Container) -> void:
	if container == null:
		return
	for child in container.get_children():
		child.queue_free()


# --- Formatting --------------------------------------------------------------

static func rarity_color(rarity: String) -> Color:
	match rarity.to_lower():
		"common", "":
			return COLOR_SECONDARY_TEXT
		"uncommon":
			return COLOR_BODY
		"rare":
			return COLOR_QI
		"epic", "exceptional":
			return COLOR_ESSENCE
		"legendary", "immortal":
			return COLOR_TITLE_GOLD
		_:
			return COLOR_SECONDARY_TEXT


## ``ring_1`` -> ``Ring 1``, ``sword_dao`` -> ``Sword Dao``.
static func title_from_id(value: String) -> String:
	return value.replace("_", " ").capitalize()


static func format_quantity(value) -> String:
	if typeof(value) == TYPE_INT:
		return str(value)
	if typeof(value) == TYPE_FLOAT:
		var number := float(value)
		if is_equal_approx(number, round(number)):
			return str(int(round(number)))
		return "%.1f" % number
	return str(value)


static func format_modifier_value(key: String, value: Variant) -> String:
	var n := float(value)
	if n == 0.0:
		return ""
	if key.ends_with("_multiplier"):
		return "x%.2f" % n
	if n != floor(n):
		# Fractional values are percentage-style (e.g. +8% breakthrough chance).
		return "%+.0f%%" % (n * 100.0)
	return "%+.0f" % n


static func format_modifier_group(group: Dictionary) -> String:
	if typeof(group) != TYPE_DICTIONARY or group.is_empty():
		return ""
	var parts := PackedStringArray()
	for key in group.keys():
		var val_str := format_modifier_value(str(key), group[key])
		if val_str == "":
			continue
		parts.append("%s %s" % [humanize_key(str(key)), val_str])
	if parts.size() == 0:
		return ""
	return "  ".join(parts)


static func format_item_modifiers(item: Dictionary) -> String:
	var parts := PackedStringArray()
	for group in [item.get("stat_modifiers", {}), item.get("cultivation_modifiers", {}), item.get("utility_modifiers", {})]:
		var line := format_modifier_group(group)
		if line != "":
			parts.append(line)
	return "  ".join(parts)


## Modifier keys the players read often get a proper name; everything else falls
## back to title case.
static func humanize_key(key: String) -> String:
	match key:
		"max_hp":
			return "Max HP"
		"max_qi":
			return "Max Qi"
		"body_strength":
			return "Body Strength"
		"foundation_quality":
			return "Foundation Quality"
		"body_cultivation_flat_bonus":
			return "Body Cultivation"
		"essence_cultivation_flat_bonus":
			return "Essence Cultivation"
		"foundation_stability_bonus":
			return "Foundation Stability"
		"breakthrough_chance_modifier":
			return "Breakthrough Chance"
		"body_breakthrough_modifier":
			return "Body Breakthrough"
		"essence_breakthrough_modifier":
			return "Essence Breakthrough"
		"comprehension_bonus":
			return "Comprehension"
		"body_strain_gain_multiplier":
			return "Body Strain Gain"
		"qi_strain_gain_multiplier":
			return "Qi Strain Gain"
		"travel_safety_bonus":
			return "Travel Safety"
		"stealth_bonus":
			return "Stealth"
		"ambush_avoidance_bonus":
			return "Ambush Avoidance"
		"spirit_stone_find_bonus":
			return "Spirit Stone Find"
		"corpse_qi_resistance":
			return "Corpse Qi Resist"
		"rare_event_chance_bonus":
			return "Rare Event Chance"
		"herb_gathering_bonus":
			return "Herb Gathering"
		"shop_discount_modifier":
			return "Shop Discount"
	var words := key.replace("_", " ").split(" ")
	var out := PackedStringArray()
	for word in words:
		if word.length() > 0:
			out.append(word.substr(0, 1).to_upper() + word.substr(1))
	return " ".join(out)
