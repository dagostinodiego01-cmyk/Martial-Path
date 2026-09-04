extends Control
## Martial Path - main menu (canon "Standing Door" visual world).
##
## Owns desktop flow only: it never mutates gameplay state directly; it calls
## the Python backend through ApiClient and switches scenes after the backend
## confirms the requested action. All gameplay rules remain in the engine.

const MARTIAL_THEME := preload("res://ui/themes/martial_path_theme.tres")
const INK_GROUND := Color("14100b")
const COLOR_TEXT := Color("e7ddc9")
const COLOR_MUTED := Color("a08f74")
const COLOR_GOLD := Color("c9a35c")
const COLOR_GOLD_BRIGHT := Color("e9c87f")
const COLOR_PANEL := Color("1c1712")
const COLOR_PANEL_LINE := Color("4b3d24")

var api: ApiClient
var _status_label: Label
var _gated_buttons: Array[Button] = []
var _meta_label: Label
var _origin_select: OptionButton
var _origin_ids: Array[String] = []
var _origin_hooks: Array[String] = []
var _chronicle_list: VBoxContainer
var _chronicle_count: Label
var _retained_meta: Dictionary = {}
var _legacy_dialog: PopupPanel


func _unhandled_input(event: InputEvent) -> void:
	# F11 toggles fullscreen; the stretch mode (canvas_items + expand) keeps the
	# UI filling any window shape. Leaving fullscreen restores the maximized
	# window (the boot mode), never a small floating one.
	if event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_F11:
		var mode := DisplayServer.window_get_mode()
		DisplayServer.window_set_mode(
			DisplayServer.WINDOW_MODE_MAXIMIZED if mode == DisplayServer.WINDOW_MODE_FULLSCREEN
			else DisplayServer.WINDOW_MODE_FULLSCREEN
		)


func _ready() -> void:
	theme = MARTIAL_THEME
	_build_ui()
	_apply_app_icon()
	api = ApiClient.new()
	add_child(api)
	api.state_loaded.connect(_on_state_loaded)
	api.meta_loaded.connect(_on_meta_loaded)
	api.action_completed.connect(_on_action_completed)
	api.request_failed.connect(_on_request_failed)
	_wire_backend_gate()


func _apply_app_icon() -> void:
	var image := Image.new()
	if image.load("res://icon.png") != OK:
		return
	DisplayServer.set_icon(image)


# --- Construction -----------------------------------------------------------


func _build_ui() -> void:
	var ground := ColorRect.new()
	ground.color = INK_GROUND
	ground.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(ground)

	var grain := TextureRect.new()
	grain.texture = load("res://assets/ink_grain.png")
	grain.stretch_mode = TextureRect.STRETCH_TILE
	grain.modulate = Color(1, 1, 1, 0.55)
	grain.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(grain)

	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	for side in ["left", "top", "right", "bottom"]:
		margin.add_theme_constant_override("margin_%s" % side, 40)
	add_child(margin)

	var center := CenterContainer.new()
	center.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	margin.add_child(center)

	# The standing door: a single tall lacquer panel framed by a double gold rule.
	var door := PanelContainer.new()
	door.custom_minimum_size = Vector2(520, 0)
	var door_style := StyleBoxFlat.new()
	door_style.bg_color = COLOR_PANEL
	door_style.border_width_left = 3
	door_style.border_width_top = 3
	door_style.border_width_right = 3
	door_style.border_width_bottom = 3
	door_style.border_color = COLOR_GOLD
	door_style.content_margin_left = 8
	door_style.content_margin_top = 8
	door_style.content_margin_right = 8
	door_style.content_margin_bottom = 8
	door_style.shadow_color = Color(0, 0, 0, 0.6)
	door_style.shadow_size = 36
	door_style.shadow_offset = Vector2(0, 12)
	door.add_theme_stylebox_override("panel", door_style)
	center.add_child(door)

	var inner_rule := PanelContainer.new()
	var rule_style := StyleBoxFlat.new()
	rule_style.bg_color = Color(0.11, 0.09, 0.066, 1)
	rule_style.border_width_left = 1
	rule_style.border_width_top = 1
	rule_style.border_width_right = 1
	rule_style.border_width_bottom = 1
	rule_style.border_color = COLOR_PANEL_LINE
	rule_style.content_margin_left = 36
	rule_style.content_margin_top = 26
	rule_style.content_margin_right = 36
	rule_style.content_margin_bottom = 24
	inner_rule.add_theme_stylebox_override("panel", rule_style)
	door.add_child(inner_rule)

	var column := VBoxContainer.new()
	column.add_theme_constant_override("separation", 10)
	inner_rule.add_child(column)

	# --- Brand block -------------------------------------------------------
	column.add_child(_make_ornament())

	var title := Label.new()
	title.text = "MARTIAL PATH"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_override("font", _cinzel())
	title.add_theme_font_size_override("font_size", 44)
	title.add_theme_color_override("font_color", COLOR_GOLD_BRIGHT)
	column.add_child(title)

	var subtitle := Label.new()
	subtitle.text = "A CULTIVATION PATH THROUGH BODY, ESSENCE, AND CONSEQUENCE"
	subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	subtitle.add_theme_font_size_override("font_size", 12)
	subtitle.add_theme_color_override("font_color", COLOR_MUTED)
	column.add_child(subtitle)

	column.add_child(_make_spacer(14))

	_meta_label = Label.new()
	_meta_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_meta_label.add_theme_font_size_override("font_size", 15)
	_meta_label.add_theme_color_override("font_color", COLOR_GOLD)
	column.add_child(_meta_label)

	# --- Origins -----------------------------------------------------------
	column.add_child(_make_spacer(16))
	column.add_child(_make_section_rule("CHOOSE YOUR ORIGIN"))

	_origin_select = OptionButton.new()
	_origin_select.custom_minimum_size = Vector2(0, 40)
	_origin_select.item_selected.connect(_on_origin_selected)
	column.add_child(_origin_select)

	# --- Chronicle ---------------------------------------------------------
	column.add_child(_make_spacer(14))
	var chronicle_head := HBoxContainer.new()
	chronicle_head.add_child(_make_section_rule("CHRONICLE OF PAST LIVES"))
	_chronicle_count = Label.new()
	_chronicle_count.add_theme_font_size_override("font_size", 12)
	_chronicle_count.add_theme_color_override("font_color", COLOR_MUTED)
	chronicle_head.add_child(_chronicle_count)
	column.add_child(chronicle_head)

	var chronicle_scroll := ScrollContainer.new()
	chronicle_scroll.custom_minimum_size = Vector2(0, 132)
	chronicle_scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	chronicle_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	column.add_child(chronicle_scroll)

	_chronicle_list = VBoxContainer.new()
	_chronicle_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_chronicle_list.add_theme_constant_override("separation", 2)
	chronicle_scroll.add_child(_chronicle_list)

	# --- Legacy + play -----------------------------------------------------
	column.add_child(_make_spacer(14))

	var legacy_button := _make_button("LEGACY TREE", _open_legacy_dialog)
	column.add_child(legacy_button)

	column.add_child(_make_spacer(4))

	var new_game_button := _make_primary_button("NEW GAME", _new_game)
	var continue_button := _make_button("CONTINUE", func(): _load_slot("default"))
	var load_button := _make_button("LOAD GAME", func(): _load_slot("default"))
	_gated_buttons = [new_game_button, continue_button, load_button]
	column.add_child(new_game_button)
	var play_row := HBoxContainer.new()
	play_row.add_theme_constant_override("separation", 8)
	continue_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	load_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	play_row.add_child(continue_button)
	play_row.add_child(load_button)
	column.add_child(play_row)

	# --- Footer ------------------------------------------------------------
	column.add_child(_make_spacer(16))

	var footer := HBoxContainer.new()
	footer.alignment = BoxContainer.ALIGNMENT_CENTER
	footer.add_theme_constant_override("separation", 4)
	footer.add_child(_make_text_link("SETTINGS", func(): _set_status("Settings arrive with the next meditation.")))
	footer.add_child(_make_dot())
	footer.add_child(_make_text_link("CREDITS", func(): _set_status("Martial Path - an original cultivation RPG.")))
	footer.add_child(_make_dot())
	footer.add_child(_make_text_link("QUIT", func(): get_tree().quit()))
	column.add_child(footer)

	column.add_child(_make_spacer(6))

	_status_label = Label.new()
	_status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_status_label.custom_minimum_size = Vector2(0, 34)
	_status_label.add_theme_font_size_override("font_size", 13)
	_status_label.add_theme_color_override("font_color", COLOR_GOLD)
	column.add_child(_status_label)


func _cinzel() -> Font:
	var variation := FontVariation.new()
	variation.base_font = load("res://ui/fonts/Cinzel.ttf")
	variation.spacing_space = 4
	return variation


func _make_ornament() -> Control:
	# A centered diamond between two hairlines: the gate sigil.
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 10)
	var left := ColorRect.new()
	left.color = COLOR_GOLD
	left.custom_minimum_size = Vector2(120, 1)
	left.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(left)
	var diamond := Label.new()
	diamond.text = "◆"
	diamond.add_theme_font_size_override("font_size", 12)
	diamond.add_theme_color_override("font_color", COLOR_GOLD_BRIGHT)
	row.add_child(diamond)
	var right := ColorRect.new()
	right.color = COLOR_GOLD
	right.custom_minimum_size = Vector2(120, 1)
	right.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(right)
	return row


func _make_spacer(height: int) -> Control:
	var spacer := Control.new()
	spacer.custom_minimum_size = Vector2(0, height)
	return spacer


func _make_section_rule(title_text: String) -> Control:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	var line_a := ColorRect.new()
	line_a.color = COLOR_PANEL_LINE
	line_a.custom_minimum_size = Vector2(18, 1)
	line_a.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	row.add_child(line_a)
	var label := Label.new()
	label.text = title_text
	label.add_theme_font_size_override("font_size", 13)
	label.add_theme_color_override("font_color", COLOR_GOLD)
	row.add_child(label)
	var line_b := ColorRect.new()
	line_b.color = COLOR_PANEL_LINE
	line_b.custom_minimum_size = Vector2(18, 1)
	line_b.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	line_b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(line_b)
	return row


func _make_button(text: String, callback: Callable) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(0, 40)
	button.pressed.connect(callback)
	return button


func _make_primary_button(text: String, callback: Callable) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(0, 48)
	var normal := StyleBoxFlat.new()
	normal.bg_color = COLOR_GOLD
	normal.border_width_left = 1
	normal.border_width_top = 1
	normal.border_width_right = 1
	normal.border_width_bottom = 1
	normal.border_color = COLOR_GOLD_BRIGHT
	normal.content_margin_left = 14
	normal.content_margin_top = 10
	normal.content_margin_right = 14
	normal.content_margin_bottom = 10
	var hover := normal.duplicate()
	hover.bg_color = COLOR_GOLD_BRIGHT
	var pressed := normal.duplicate()
	pressed.bg_color = Color(0.71, 0.57, 0.32, 1)
	var disabled := normal.duplicate()
	disabled.bg_color = Color(0.24, 0.2, 0.14, 1)
	disabled.border_color = Color(0.29, 0.24, 0.14, 1)
	button.add_theme_stylebox_override("normal", normal)
	button.add_theme_stylebox_override("hover", hover)
	button.add_theme_stylebox_override("pressed", pressed)
	button.add_theme_stylebox_override("disabled", disabled)
	button.add_theme_color_override("font_color", Color("241b0d"))
	button.add_theme_color_override("font_hover_color", Color("241b0d"))
	button.add_theme_color_override("font_pressed_color", Color("241b0d"))
	button.add_theme_color_override("font_disabled_color", Color(0.45, 0.4, 0.3, 1))
	button.add_theme_font_size_override("font_size", 16)
	button.pressed.connect(callback)
	return button


func _make_text_link(text: String, callback: Callable) -> Button:
	var button := Button.new()
	button.text = text
	button.flat = true
	button.add_theme_font_size_override("font_size", 12)
	button.add_theme_color_override("font_color", COLOR_MUTED)
	button.add_theme_color_override("font_hover_color", COLOR_GOLD_BRIGHT)
	button.pressed.connect(callback)
	return button


func _make_dot() -> Label:
	var dot := Label.new()
	dot.text = "·"
	dot.add_theme_color_override("font_color", COLOR_PANEL_LINE)
	return dot


# --- Backend flow -----------------------------------------------------------


func _new_game() -> void:
	_set_status("The wheel turns... a new life begins.")
	var origin_id = null
	if _origin_ids.size() > 0 and _origin_select.selected >= 0 and _origin_select.selected < _origin_ids.size():
		origin_id = _origin_ids[_origin_select.selected]
	api.new_game("Daoist", null, origin_id, true)


func _load_slot(slot: String) -> void:
	_set_status("Opening the record of a past life...")
	api.load_game(slot)


func _on_state_loaded(_state: Dictionary) -> void:
	_open_gameplay()


func _on_meta_loaded(meta: Dictionary) -> void:
	_retained_meta = meta
	var memory := int(meta.get("ancestral_memory", 0))
	_meta_label.text = "ANCESTRAL MEMORY · %d" % memory

	_origin_select.clear()
	_origin_ids.clear()
	_origin_hooks.clear()
	var origins = meta.get("origins", [])
	for origin in origins:
		var oid := str(origin.get("id", ""))
		var label := str(origin.get("display_name", oid)).to_upper()
		var cost := int(origin.get("cost", 0))
		if cost > 0:
			label += "   (%d)" % cost
		var idx := _origin_select.item_count
		_origin_select.add_item(label, idx)
		_origin_select.set_item_disabled(idx, not bool(origin.get("affordable", true)))
		_origin_ids.append(oid)
		_origin_hooks.append(str(origin.get("story_hook", "")))

	for child in _chronicle_list.get_children():
		child.queue_free()
	var chronicle = meta.get("chronicle", [])
	_chronicle_count.text = "· %d" % chronicle.size() if not chronicle.is_empty() else ""
	if chronicle.is_empty():
		var empty := Label.new()
		empty.text = "No lives recorded. The ledger awaits its first entry."
		empty.add_theme_font_size_override("font_size", 13)
		empty.add_theme_color_override("font_color", COLOR_MUTED)
		_chronicle_list.add_child(empty)
	else:
		for i in chronicle.size():
			var entry: Dictionary = chronicle[i]
			var row := HBoxContainer.new()
			row.add_theme_constant_override("separation", 8)
			var index := Label.new()
			index.text = "%02d" % (i + 1)
			index.add_theme_font_size_override("font_size", 12)
			index.add_theme_color_override("font_color", COLOR_PANEL_LINE)
			index.custom_minimum_size = Vector2(24, 0)
			row.add_child(index)
			var line := Label.new()
			line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
			line.size_flags_horizontal = Control.SIZE_EXPAND_FILL
			line.text = _chronicle_line(entry)
			line.add_theme_font_size_override("font_size", 13)
			line.add_theme_color_override("font_color", COLOR_TEXT)
			row.add_child(line)
			_chronicle_list.add_child(row)

	_refresh_legacy_dialog()


func _on_origin_selected(index: int) -> void:
	if index >= 0 and index < _origin_hooks.size():
		_set_status(_origin_hooks[index])


# --- Legacy dialog ----------------------------------------------------------


func _open_legacy_dialog() -> void:
	if _legacy_dialog != null and is_instance_valid(_legacy_dialog):
		_legacy_dialog.queue_free()
	_legacy_dialog = PopupPanel.new()
	var style := StyleBoxFlat.new()
	style.bg_color = COLOR_PANEL
	style.border_width_left = 2
	style.border_width_top = 2
	style.border_width_right = 2
	style.border_width_bottom = 2
	style.border_color = COLOR_GOLD
	style.content_margin_left = 22
	style.content_margin_top = 18
	style.content_margin_right = 22
	style.content_margin_bottom = 18
	style.shadow_color = Color(0, 0, 0, 0.6)
	style.shadow_size = 30
	_legacy_dialog.add_theme_stylebox_override("panel", style)

	var column := VBoxContainer.new()
	column.custom_minimum_size = Vector2(560, 420)
	column.add_theme_constant_override("separation", 10)
	_legacy_dialog.add_child(column)

	var title := Label.new()
	title.text = "LEGACY OF ANCESTORS"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_override("font", _cinzel())
	title.add_theme_font_size_override("font_size", 22)
	title.add_theme_color_override("font_color", COLOR_GOLD_BRIGHT)
	column.add_child(title)

	var memory := int(_retained_meta.get("ancestral_memory", 0))
	var balance := Label.new()
	balance.text = "Ancestral Memory available: %d" % memory
	balance.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	balance.add_theme_font_size_override("font_size", 13)
	balance.add_theme_color_override("font_color", COLOR_GOLD)
	column.add_child(balance)

	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	column.add_child(scroll)

	var tiers_box := VBoxContainer.new()
	tiers_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	tiers_box.add_theme_constant_override("separation", 12)
	scroll.add_child(tiers_box)

	var tiers = _retained_meta.get("unlock_tree", [])
	if tiers.is_empty():
		var empty := Label.new()
		empty.text = "The legacy sleeps - no tiers are known to this world yet."
		empty.add_theme_font_size_override("font_size", 13)
		empty.add_theme_color_override("font_color", COLOR_MUTED)
		tiers_box.add_child(empty)
	for tier in tiers:
		if typeof(tier) != TYPE_DICTIONARY:
			continue
		var tier_name := str(tier.get("display_name", tier.get("id", "Tier")))
		var header := Label.new()
		header.text = tier_name.to_upper()
		header.add_theme_font_size_override("font_size", 14)
		header.add_theme_color_override("font_color", COLOR_GOLD)
		tiers_box.add_child(header)
		for node in tier.get("unlocks", []):
			if typeof(node) != TYPE_DICTIONARY:
				continue
			tiers_box.add_child(_make_legacy_row(node))

	var close := Button.new()
	close.text = "RETURN"
	close.custom_minimum_size = Vector2(0, 38)
	close.pressed.connect(func(): _legacy_dialog.hide())
	column.add_child(close)

	add_child(_legacy_dialog)
	_legacy_dialog.popup_centered(Vector2i(620, 520))


func _make_legacy_row(node: Dictionary) -> Control:
	var row := PanelContainer.new()
	var style := StyleBoxFlat.new()
	style.bg_color = Color(0.09, 0.075, 0.055, 1)
	style.border_width_left = 1
	style.border_width_top = 1
	style.border_width_right = 1
	style.border_width_bottom = 1
	style.border_color = COLOR_PANEL_LINE
	style.content_margin_left = 12
	style.content_margin_top = 8
	style.content_margin_right = 12
	style.content_margin_bottom = 8
	row.add_theme_stylebox_override("panel", style)

	var grid := HBoxContainer.new()
	grid.add_theme_constant_override("separation", 10)
	row.add_child(grid)

	var name_box := VBoxContainer.new()
	name_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var node_id := str(node.get("id", ""))
	var name_label := Label.new()
	name_label.text = _humanize_key(node_id)
	name_label.add_theme_font_size_override("font_size", 14)
	name_label.add_theme_color_override("font_color", COLOR_TEXT if not bool(node.get("purchased", false)) else COLOR_MUTED)
	name_box.add_child(name_label)
	var desc := str(node.get("description", ""))
	if desc != "":
		var desc_label := Label.new()
		desc_label.text = desc
		desc_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		desc_label.add_theme_font_size_override("font_size", 12)
		desc_label.add_theme_color_override("font_color", COLOR_MUTED)
		name_box.add_child(desc_label)
	grid.add_child(name_box)

	var cost := int(node.get("cost", 0))
	var cost_label := Label.new()
	cost_label.text = "%d AM" % cost
	cost_label.add_theme_font_size_override("font_size", 13)
	cost_label.add_theme_color_override("font_color", COLOR_GOLD)
	cost_label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	grid.add_child(cost_label)

	var purchased := bool(node.get("purchased", false))
	var available := bool(node.get("available", false))
	var state := Button.new()
	state.custom_minimum_size = Vector2(96, 32)
	state.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	if purchased:
		state.text = "OWNED"
		state.disabled = true
	elif available:
		state.text = "AWAKEN"
		state.pressed.connect(_on_unlock_pressed.bind(node_id))
	else:
		state.text = "SEALED"
		state.disabled = true
	grid.add_child(state)
	return row


func _refresh_legacy_dialog() -> void:
	# Rebuild in place if the dialog is open so a purchase reflects instantly.
	if _legacy_dialog != null and is_instance_valid(_legacy_dialog) and _legacy_dialog.visible:
		_open_legacy_dialog()


func _on_unlock_pressed(node_id: String) -> void:
	api.send_action({"action": "UNLOCK", "unlock_id": node_id})


func _humanize_key(value: String) -> String:
	return value.replace("_", " ").capitalize()


func _chronicle_line(entry: Dictionary) -> String:
	var origin := str(entry.get("origin", "?"))
	var dao := str(entry.get("dao", "?"))
	var body := str(entry.get("peak_body_realm", "?"))
	var age := int(entry.get("age_years", 0))
	var cause := _humanize_cause(str(entry.get("cause", "?")))
	return "%s · %s · %s at %d yrs (%s)" % [origin, dao, cause, age, body]


func _humanize_cause(cause: String) -> String:
	match cause:
		"old_age":
			return "died of old age"
		"combat":
			return "fell in battle"
		"ascended":
			return "ascended beyond the world"
		_:
			return "met their end"


func _on_action_completed(result: Dictionary) -> void:
	var event := str(result.get("event", ""))
	if event == "LOAD_RESULT" and bool(result.get("success", false)):
		_open_gameplay()
		return
	if event == "UNLOCK_PURCHASED":
		_set_status("Legacy awakened. Ancestral Memory: %s" % str(result.get("ancestral_memory", 0)))
		api.fetch_meta()
		return
	if event == "ERROR":
		_set_status("That legacy cannot be claimed right now (%s)." % str(result.get("reason", "unknown")))
		api.fetch_meta()
		return
	_set_status(_translate_reason(str(result.get("reason", "SAVE_NOT_FOUND"))))


func _on_request_failed(_message: String) -> void:
	_set_status("The game engine is not responding. Start the local Martial Path backend and try again.")


func _open_gameplay() -> void:
	get_tree().change_scene_to_file("res://scenes/Main.tscn")


func _wire_backend_gate() -> void:
	# Until the local engine answers, keep the play options disabled so a click
	# never races the backend start-up. BackendLauncher owns the process + probe.
	if Backend.is_ready:
		api.fetch_meta()
		return
	_set_gated(false)
	_set_status("Awakening the world...")
	Backend.backend_ready.connect(_on_backend_ready)
	Backend.backend_failed.connect(_on_backend_failed)


func _on_backend_ready() -> void:
	_set_gated(true)
	_set_status("")
	api.fetch_meta()


func _on_backend_failed(message: String) -> void:
	_set_status(message)


func _set_gated(enabled: bool) -> void:
	for button in _gated_buttons:
		button.disabled = not enabled


func _set_status(text: String) -> void:
	_status_label.text = text


func _translate_reason(reason: String) -> String:
	match reason:
		"SAVE_NOT_FOUND":
			return "No default save exists yet. Start a new game first."
		"SAVE_VERSION_MISMATCH":
			return "That save was created with an incompatible version."
		"SAVE_CORRUPT":
			return "That save file could not be read."
		_:
			return "That action cannot be completed right now."
