extends Control
## Martial Path - Godot frontend controller.
##
## Builds the current UI in code, forwards commands to the Python backend
## through ApiClient, and renders returned state/result dictionaries. It owns
## presentation only: all gameplay rules remain in the Python engine.

const PANEL_MIN_WIDTH := 220
const CENTER_MIN_WIDTH := 420
const MARTIAL_THEME := preload("res://ui/themes/martial_path_theme.tres")
const WORLD_MAP_PATH := "res://assets/sky_spill_continent_map.png"
const WORLD_MAP_SIZE := Vector2(960, 640)
const WORLD_MAP_ASPECT := 1.5

const COLOR_BACKGROUND := Color("#05080B")
const COLOR_SECONDARY_BACKGROUND := Color("#0B1118")
const COLOR_PANEL := Color("#0B1118")
const COLOR_PANEL_SOFT := Color("#111820")
const COLOR_PANEL_RAISED := Color("#101923")
const COLOR_BORDER := Color("#4B3820")
const COLOR_BORDER_STRONG := Color("#A9792B")
const COLOR_PRIMARY_TEXT := Color("#F2E8D5")
const COLOR_SECONDARY_TEXT := Color("#C7BCA8")
const COLOR_MUTED := Color("#8F8A81")
const COLOR_TITLE_GOLD := Color("#F0C76A")
const COLOR_ANTIQUE_GOLD := Color("#D6A64A")
const COLOR_QI := Color("#3B9FE8")
const COLOR_QI_DARK := Color("#123143")
const COLOR_SPIRITUAL_CYAN := Color("#51BDED")
const COLOR_HP := Color("#D94B4B")
const COLOR_HP_DARK := Color("#3A1516")
const COLOR_BODY := Color("#79C85A")
const COLOR_BODY_DARK := Color("#22331A")
const COLOR_ESSENCE := Color("#C77DFF")
const COLOR_INVENTORY_BLUE := Color("#51BDED")
const COLOR_WARNING := Color("#E6B24A")
const COLOR_DANGER := Color("#E05A5A")
const COLOR_SUCCESS := Color("#70D36B")
const INVENTORY_CAPACITY := 50
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

# Floating tab panels opened from the top bar (index -> title).
const TAB_TITLES := ["Inventory", "Equipment", "Journal", "Status", "Techniques"]

var api: ApiClient
var _connected := false
var _showing_event_result := false

## When false (player mode), backend/connection diagnostics are hidden from the
## player. Enable in the Inspector to surface URLs, connection status, and raw
## error/reason codes for debugging.
@export var debug_mode := false

# Top bar refs.
var _name_label: Label
var _hp_bar: ProgressBar
var _qi_bar: ProgressBar
var _hp_text: Label
var _qi_text: Label
var _year_label: Label

# Character panel refs (left).
var _portrait_initial: Label
var _char_name_label: Label
var _char_path_label: Label
var _char_realm_label: Label
var _character_text: RichTextLabel
var _body_progress_bar: ProgressBar
var _body_progress_text: Label

# Location panel refs (centre).
var _location_title: Label
var _artwork_label: Label
var _artwork_texture: TextureRect
var _location_texture_cache := {}
var _location_text: RichTextLabel
var _chips_row: HBoxContainer
var _exits_row: HBoxContainer
var _combat_panel: PanelContainer
var _enemy_name: Label
var _enemy_hp_bar: ProgressBar
var _enemy_details: RichTextLabel

# Floating overlay (tab panels) refs.
var _overlay: Control
var _overlay_dim: ColorRect
var _overlay_panel: PanelContainer
var _overlay_title: Label
var _overlay_content: VBoxContainer
var _tab_pages: Array = []
var _tab_buttons: Array = []
var _active_tab := -1

# Tab content refs (inside the floating overlay).
var _inventory_text: RichTextLabel
var _inventory_count: Label
var _equipment_text: RichTextLabel
var _equipment_count: Label
var _gold_label: Label
var _stones_label: Label
var _quest_text: RichTextLabel
var _status_text: RichTextLabel
var _techniques_text: RichTextLabel

# Action refs.
var _action_box: VBoxContainer
var _cultivation_grid: GridContainer
var _exploration_grid: GridContainer
var _support_grid: GridContainer
var _combat_actions: HBoxContainer
var _log: RichTextLabel

# Cached destinations for the Travel popup (from the last state snapshot).
var _destinations: Array = []
var _travel_ids: Array = []
var _last_state: Dictionary = {}
var _equip_choices: Array = []
var _unequip_choices: Array = []
var _shop_choices: Array = []
var _trainer_choices: Array = []
var _use_choices: Array = []

# Cosmetic display state (the engine tracks years via lifespan).
var _year := 0


func _ready() -> void:
	theme = MARTIAL_THEME
	_build_ui()
	_apply_window_icon()
	api = ApiClient.new()
	add_child(api)
	api.state_loaded.connect(_on_state_loaded)
	api.action_completed.connect(_on_action_completed)
	api.request_failed.connect(_on_request_failed)
	if debug_mode:
		_append("Connecting to backend at %s ..." % ApiClient.BASE_URL)
	api.get_state()


func _apply_window_icon() -> void:
	var image := Image.new()
	if image.load("res://icon.png") == OK:
		DisplayServer.set_icon(image)


# --- UI construction -------------------------------------------------------

func _build_ui() -> void:
	var background := ColorRect.new()
	background.color = COLOR_BACKGROUND
	background.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(background)

	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 36)
	margin.add_theme_constant_override("margin_top", 28)
	margin.add_theme_constant_override("margin_right", 36)
	margin.add_theme_constant_override("margin_bottom", 28)
	add_child(margin)

	var root := VBoxContainer.new()
	root.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	root.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_theme_constant_override("separation", 12)
	margin.add_child(root)

	_build_top_bar(root)
	_build_body(root)
	_build_overlay()


func _build_top_bar(root: VBoxContainer) -> void:
	var top := _make_panel()
	top.custom_minimum_size = Vector2(0, 88)
	root.add_child(top)

	var row := HBoxContainer.new()
	row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_theme_constant_override("separation", 18)
	top.add_child(row)

	var emblem := TextureRect.new()
	emblem.custom_minimum_size = Vector2(52, 52)
	emblem.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	emblem.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	emblem.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var emblem_tex := _load_texture("res://icon.png")
	if emblem_tex != null:
		emblem.texture = emblem_tex
	row.add_child(emblem)

	var title_box := VBoxContainer.new()
	title_box.custom_minimum_size = Vector2(260, 0)
	row.add_child(title_box)
	var title := _make_label("MARTIAL PATH", 32, COLOR_TITLE_GOLD)
	title.autowrap_mode = TextServer.AUTOWRAP_OFF
	title_box.add_child(title)
	_name_label = _make_label("Daoist", 16, COLOR_SECONDARY_TEXT)
	title_box.add_child(_name_label)

	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(spacer)

	var hp_group := _make_bar_group("HP", COLOR_HP, COLOR_HP_DARK)
	_hp_bar = hp_group["bar"]
	_hp_text = hp_group["cap"]
	row.add_child(hp_group["box"])

	var qi_group := _make_bar_group("Qi", COLOR_QI, COLOR_QI_DARK)
	_qi_bar = qi_group["bar"]
	_qi_text = qi_group["cap"]
	row.add_child(qi_group["box"])

	var year_box := VBoxContainer.new()
	year_box.custom_minimum_size = Vector2(72, 0)
	row.add_child(year_box)
	year_box.add_child(_make_label("YEAR", 12, COLOR_MUTED))
	_year_label = _make_label("0", 16, COLOR_PRIMARY_TEXT)
	year_box.add_child(_year_label)

	for i in TAB_TITLES.size():
		row.add_child(_make_tab_button(TAB_TITLES[i], i))

	var settings_btn := _make_button("Settings", func(): _open_settings(), "Save, load, or start a new game.")
	settings_btn.custom_minimum_size = Vector2(96, 0)
	row.add_child(settings_btn)


func _build_body(root: VBoxContainer) -> void:
	var body := HBoxContainer.new()
	body.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	body.size_flags_vertical = Control.SIZE_EXPAND_FILL
	body.add_theme_constant_override("separation", 12)
	root.add_child(body)

	# Left column: Character only (identity / cultivation / combat).
	var left := VBoxContainer.new()
	left.custom_minimum_size = Vector2(PANEL_MIN_WIDTH, 0)
	left.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	left.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.size_flags_stretch_ratio = 22.0
	left.add_theme_constant_override("separation", 12)
	body.add_child(left)
	_build_character_panel(left)

	# Centre column: Location (with artwork) then Actions.
	var center := VBoxContainer.new()
	center.custom_minimum_size = Vector2(CENTER_MIN_WIDTH, 0)
	center.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	center.size_flags_vertical = Control.SIZE_EXPAND_FILL
	center.size_flags_stretch_ratio = 52.0
	center.add_theme_constant_override("separation", 12)
	body.add_child(center)
	_build_location_panel(center)
	_build_action_panel(center)

	# Right column: permanent event log.
	var right := VBoxContainer.new()
	right.custom_minimum_size = Vector2(PANEL_MIN_WIDTH, 0)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right.size_flags_stretch_ratio = 26.0
	right.add_theme_constant_override("separation", 12)
	body.add_child(right)
	_build_event_log(right)


func _build_character_panel(left: VBoxContainer) -> void:
	var panel := _make_panel()
	panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.add_child(panel)

	var box := VBoxContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.size_flags_vertical = Control.SIZE_EXPAND_FILL
	box.add_theme_constant_override("separation", 8)
	panel.add_child(box)

	box.add_child(_make_label("CHARACTER", 14, COLOR_ANTIQUE_GOLD))

	# Portrait (monogram) + identity summary.
	var header := HBoxContainer.new()
	header.add_theme_constant_override("separation", 10)
	box.add_child(header)

	var portrait_panel := PanelContainer.new()
	portrait_panel.custom_minimum_size = Vector2(64, 64)
	portrait_panel.add_theme_stylebox_override("panel", _make_portrait_style())
	header.add_child(portrait_panel)
	_portrait_initial = _make_label("?", 30, COLOR_TITLE_GOLD)
	_portrait_initial.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_portrait_initial.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	portrait_panel.add_child(_portrait_initial)

	var identity := VBoxContainer.new()
	identity.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	identity.add_theme_constant_override("separation", 2)
	header.add_child(identity)
	_char_name_label = _make_label("Daoist", 17, COLOR_PRIMARY_TEXT)
	identity.add_child(_char_name_label)
	_char_path_label = _make_label("Path: Unassigned", 12, COLOR_QI)
	identity.add_child(_char_path_label)
	_char_realm_label = _make_label("Realm: -", 12, COLOR_MUTED)
	identity.add_child(_char_realm_label)

	_character_text = RichTextLabel.new()
	_character_text.bbcode_enabled = true
	_character_text.fit_content = true
	_character_text.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_character_text.add_theme_color_override("default_color", COLOR_PRIMARY_TEXT)
	box.add_child(_character_text)

	_body_progress_text = _make_label("Body Progress 0%", 12, COLOR_MUTED)
	box.add_child(_body_progress_text)
	_body_progress_bar = ProgressBar.new()
	_body_progress_bar.min_value = 0
	_body_progress_bar.max_value = 100
	_body_progress_bar.show_percentage = false
	_body_progress_bar.custom_minimum_size = Vector2(0, 14)
	_apply_bar_style(_body_progress_bar, COLOR_BODY, COLOR_BODY_DARK)
	box.add_child(_body_progress_bar)

	box.add_child(_make_button("View Detailed Status", func(): _focus_tab(3), "Open the Status panel."))


func _build_location_panel(center: VBoxContainer) -> void:
	var panel := _make_panel(COLOR_PANEL, COLOR_BORDER, 1)
	panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	center.add_child(panel)

	var box := VBoxContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.size_flags_vertical = Control.SIZE_EXPAND_FILL
	box.add_theme_constant_override("separation", 10)
	panel.add_child(box)

	_location_title = _make_label("OUTER FOREST", 22, COLOR_TITLE_GOLD)
	box.add_child(_location_title)

	# Location artwork: a TextureRect (from res://assets/locations/<id>.png) with
	# a centred name label as the fallback when a location has no image yet.
	var art := PanelContainer.new()
	art.custom_minimum_size = Vector2(0, 200)
	art.size_flags_vertical = Control.SIZE_EXPAND_FILL
	art.clip_contents = true
	var art_style := _make_panel_style(COLOR_PANEL_SOFT, COLOR_BORDER, 1)
	art_style.bg_color = Color("#0C1512")
	art_style.content_margin_left = 0
	art_style.content_margin_right = 0
	art_style.content_margin_top = 0
	art_style.content_margin_bottom = 0
	art.add_theme_stylebox_override("panel", art_style)
	box.add_child(art)

	var art_holder := Control.new()
	art_holder.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	art_holder.size_flags_vertical = Control.SIZE_EXPAND_FILL
	art.add_child(art_holder)

	_artwork_texture = TextureRect.new()
	_artwork_texture.set_anchors_preset(Control.PRESET_FULL_RECT)
	_artwork_texture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_artwork_texture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	_artwork_texture.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_artwork_texture.visible = false
	art_holder.add_child(_artwork_texture)

	_artwork_label = _make_label("", 26, Color(0.95, 0.90, 0.83, 0.4))
	_artwork_label.set_anchors_preset(Control.PRESET_FULL_RECT)
	_artwork_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_artwork_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_artwork_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	art_holder.add_child(_artwork_label)

	# Enemy strip (visible only during combat).
	_combat_panel = _make_panel(COLOR_PANEL_SOFT, COLOR_DANGER, 1)
	_combat_panel.visible = false
	box.add_child(_combat_panel)
	var combat_box := VBoxContainer.new()
	combat_box.add_theme_constant_override("separation", 6)
	_combat_panel.add_child(combat_box)
	_enemy_name = _make_label("Enemy", 16, COLOR_DANGER)
	combat_box.add_child(_enemy_name)
	_enemy_hp_bar = ProgressBar.new()
	_enemy_hp_bar.min_value = 0
	_enemy_hp_bar.max_value = 100
	_enemy_hp_bar.show_percentage = false
	_enemy_hp_bar.custom_minimum_size = Vector2(0, 16)
	_apply_bar_style(_enemy_hp_bar, COLOR_HP, COLOR_HP_DARK)
	combat_box.add_child(_enemy_hp_bar)
	_enemy_details = RichTextLabel.new()
	_enemy_details.bbcode_enabled = true
	_enemy_details.fit_content = true
	_enemy_details.custom_minimum_size = Vector2(0, 70)
	_enemy_details.add_theme_color_override("default_color", COLOR_PRIMARY_TEXT)
	combat_box.add_child(_enemy_details)

	# Description, metadata, and exits.
	_location_text = RichTextLabel.new()
	_location_text.bbcode_enabled = true
	_location_text.fit_content = true
	_location_text.add_theme_color_override("default_color", COLOR_PRIMARY_TEXT)
	box.add_child(_location_text)

	# Icon + value chips for Danger / Qi Density / Resources.
	_chips_row = HBoxContainer.new()
	_chips_row.add_theme_constant_override("separation", 8)
	box.add_child(_chips_row)

	# Interactive exits (click to travel).
	_exits_row = HBoxContainer.new()
	_exits_row.add_theme_constant_override("separation", 8)
	box.add_child(_exits_row)


func _build_action_panel(center: VBoxContainer) -> void:
	var panel := _make_panel()
	center.add_child(panel)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 8)
	panel.add_child(box)
	box.add_child(_make_label("ACTIONS", 14, COLOR_ANTIQUE_GOLD))

	_action_box = VBoxContainer.new()
	_action_box.add_theme_constant_override("separation", 6)
	_action_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.add_child(_action_box)

	_action_box.add_child(_make_label("Cultivation", 12, COLOR_ANTIQUE_GOLD))
	_cultivation_grid = _make_action_grid(4)
	_action_box.add_child(_cultivation_grid)

	_action_box.add_child(_make_label("Exploration", 12, COLOR_ANTIQUE_GOLD))
	_exploration_grid = _make_action_grid(4)
	_action_box.add_child(_exploration_grid)

	_action_box.add_child(_make_label("Commerce & Support", 12, COLOR_ANTIQUE_GOLD))
	_support_grid = _make_action_grid(4)
	_action_box.add_child(_support_grid)

	_combat_actions = _make_action_row()
	_combat_actions.visible = false
	box.add_child(_combat_actions)
	_combat_actions.add_child(_make_button("Attack", func(): _send("ATTACK"), "Strike with a basic attack."))
	_combat_actions.add_child(_make_button("Iron Fist", func(): api.send_action({"action": "USE_SKILL", "skill_id": "iron_fist"}), "Spend Qi to use Iron Fist."))
	_combat_actions.add_child(_make_button("Healing Pill", func(): api.send_action({"action": "USE_ITEM", "item_id": "healing_pill"}), "Use a healing pill."))
	_combat_actions.add_child(_make_button("Flee", func(): _send("FLEE"), "Attempt to escape."))


func _render_actions(player: Dictionary) -> void:
	_clear_action_grids()
	var essence_unlocked := bool(player.get("essence_unlocked", true))
	var cultivation: Dictionary = player.get("cultivation_state", {})
	var essence: Dictionary = cultivation.get("essence_gathering", {})
	var req := str(essence.get("unlock_requirement", ""))
	var locked_reason := ""
	if not essence_unlocked:
		locked_reason = ("Locked - %s." % req) if req != "" else "Essence Gathering is still locked."

	_cultivation_grid.add_child(_make_action_card("Train Body", "Cultivate your body", func(): _send("TRAIN_BODY")))
	_cultivation_grid.add_child(_make_action_card("Gather Essence", ("Absorb spiritual energy" if essence_unlocked else "Locked"), func(): _send("TRAIN_ESSENCE"), essence_unlocked, locked_reason))
	_cultivation_grid.add_child(_make_action_card("Stabilise Foundation", "Settle strain", func(): _send("STABILISE_FOUNDATION")))
	_cultivation_grid.add_child(_make_action_card("Stabilise Essence", ("Settle essence strain" if essence_unlocked else "Locked"), func(): _send("STABILISE_ESSENCE"), essence_unlocked, locked_reason))
	_cultivation_grid.add_child(_make_action_card("Body Breakthrough", "Attempt advancement", func(): _send("BODY_BREAKTHROUGH")))
	_cultivation_grid.add_child(_make_action_card("Essence Breakthrough", ("Attempt advancement" if essence_unlocked else "Locked"), func(): _send("ESSENCE_BREAKTHROUGH"), essence_unlocked, locked_reason))

	_exploration_grid.add_child(_make_action_card("Explore", "Search the area", func(): _send("EXPLORE")))
	_exploration_grid.add_child(_make_action_card("Rest", "Recover HP & Qi", func(): _send("REST")))
	_exploration_grid.add_child(_make_action_card("Travel", "Move to another area", func(): _open_travel_popup()))
	_exploration_grid.add_child(_make_action_card("World Map", "Show your location", Callable(self, "_open_world_map_popup"), _has_map_position(), "This location has no map marker."))

	_support_grid.add_child(_make_action_card("Market", "Buy supplies and equipment", func(): _send("SHOP"), _has_available_shop(), "No market is available here."))
	_support_grid.add_child(_make_action_card("Masters", "Learn techniques", func(): _send("TRAINERS"), _has_available_trainer(), "No technique master is here."))
	_support_grid.add_child(_make_action_card("Inventory", "Manage your items", func(): _focus_tab(0)))
	_support_grid.add_child(_make_action_card("Use Item", "Use a pill or manual", Callable(self, "_open_use_popup"), _has_usable_item(), "No usable items in inventory."))
	_support_grid.add_child(_make_action_card("Equip Item", "Wear owned equipment", Callable(self, "_open_equip_popup"), _has_equipment_inventory(), "No equippable items in inventory."))
	_support_grid.add_child(_make_action_card("Unequip Item", "Clear an equipment slot", Callable(self, "_open_unequip_popup"), _has_equipped_items(), "No equipment is currently worn."))


func _make_action_card(title: String, subtitle: String, cb: Callable, enabled: bool = true, locked_reason: String = "") -> Button:
	var button := Button.new()
	button.disabled = not enabled
	button.tooltip_text = locked_reason if locked_reason != "" else subtitle
	button.custom_minimum_size = Vector2(0, 54)
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.focus_mode = Control.FOCUS_NONE
	button.add_theme_stylebox_override("normal", _make_button_style(COLOR_PANEL_RAISED, COLOR_BORDER))
	button.add_theme_stylebox_override("hover", _make_button_style(COLOR_PANEL_RAISED, COLOR_BORDER_STRONG))
	button.add_theme_stylebox_override("pressed", _make_button_style(COLOR_SECONDARY_BACKGROUND, COLOR_BORDER_STRONG))
	button.add_theme_stylebox_override("disabled", _make_button_style(COLOR_SECONDARY_BACKGROUND, COLOR_BORDER))
	if enabled:
		button.pressed.connect(cb)

	var margin := MarginContainer.new()
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 10)
	margin.add_theme_constant_override("margin_top", 6)
	margin.add_theme_constant_override("margin_right", 10)
	margin.add_theme_constant_override("margin_bottom", 6)
	button.add_child(margin)
	var v := VBoxContainer.new()
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_theme_constant_override("separation", 1)
	margin.add_child(v)
	var title_label := _make_label(title, 14, COLOR_ANTIQUE_GOLD if enabled else COLOR_MUTED)
	title_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(title_label)
	var sub_text := subtitle
	var sub_color := COLOR_MUTED
	if not enabled and locked_reason != "":
		sub_text = "🔒 " + locked_reason
		sub_color = COLOR_WARNING
	var sub_label := _make_label(sub_text, 11, sub_color)
	sub_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(sub_label)
	return button


func _focus_tab(index: int) -> void:
	_open_overlay(index)


func _open_settings() -> void:
	var popup := PopupMenu.new()
	popup.add_item("New Game", 0)
	popup.add_item("Save Game", 1)
	popup.add_item("Load Game", 2)
	popup.add_separator()
	popup.add_item("Quit", 3)
	add_child(popup)
	popup.id_pressed.connect(_on_settings_selected)
	popup.popup_hide.connect(popup.queue_free)
	popup.reset_size()
	var mouse := Vector2i(get_viewport().get_mouse_position())
	popup.popup(Rect2i(mouse.x, mouse.y, 0, 0))


func _on_settings_selected(id: int) -> void:
	match id:
		0:
			_start_new_game()
		1:
			api.save_game("default")
		2:
			api.load_game("default")
		3:
			get_tree().quit()


func _open_travel_popup() -> void:
	_travel_ids = []
	var popup := PopupMenu.new()
	for dest in _destinations:
		if typeof(dest) != TYPE_DICTIONARY:
			continue
		var reachable := bool(dest.get("reachable", true))
		popup.add_item("%s  (%s)" % [str(dest.get("display_name", dest.get("id", "?"))), str(dest.get("danger", "?"))], _travel_ids.size())
		popup.set_item_disabled(_travel_ids.size(), not reachable)
		if not reachable:
			popup.set_item_tooltip(_travel_ids.size(), str(dest.get("reason", "You cannot travel there yet.")))
		_travel_ids.append(str(dest.get("id", "")))
	if _travel_ids.is_empty():
		popup.add_item("Nowhere to travel from here", 0)
		popup.set_item_disabled(0, true)
	add_child(popup)
	popup.id_pressed.connect(_on_travel_selected)
	popup.popup_hide.connect(popup.queue_free)
	popup.reset_size()
	var mouse := Vector2i(get_viewport().get_mouse_position())
	popup.popup(Rect2i(mouse.x, mouse.y, 0, 0))


func _on_travel_selected(idx: int) -> void:
	if idx >= 0 and idx < _travel_ids.size() and str(_travel_ids[idx]) != "":
		api.travel(str(_travel_ids[idx]))


func _open_world_map_popup() -> void:
	var location: Dictionary = _last_state.get("location", {})
	var position: Dictionary = location.get("map_position", {})
	if position.is_empty():
		_set_situation("World Map", "No map marker is available for this location.")
		return

	var popup := PopupPanel.new()
	add_child(popup)
	popup.popup_hide.connect(popup.queue_free)

	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 12)
	margin.add_theme_constant_override("margin_top", 12)
	margin.add_theme_constant_override("margin_right", 12)
	margin.add_theme_constant_override("margin_bottom", 12)
	popup.add_child(margin)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 8)
	margin.add_child(box)
	box.add_child(_make_label(str(location.get("display_name", location.get("name", "World Map"))).to_upper(), 18, COLOR_TITLE_GOLD))

	var map_holder := Control.new()
	map_holder.custom_minimum_size = WORLD_MAP_SIZE
	map_holder.clip_contents = true
	box.add_child(map_holder)

	var map_texture := TextureRect.new()
	map_texture.set_anchors_preset(Control.PRESET_FULL_RECT)
	map_texture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	map_texture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	map_texture.texture = _load_texture(WORLD_MAP_PATH)
	map_texture.mouse_filter = Control.MOUSE_FILTER_IGNORE
	map_holder.add_child(map_texture)

	var marker := Label.new()
	marker.text = "X"
	marker.tooltip_text = "Current location: %s" % location.get("display_name", location.get("name", "Unknown"))
	marker.custom_minimum_size = Vector2(36, 36)
	marker.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	marker.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	marker.add_theme_font_size_override("font_size", 28)
	marker.add_theme_color_override("font_color", COLOR_DANGER)
	marker.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.9))
	marker.add_theme_constant_override("shadow_offset_x", 2)
	marker.add_theme_constant_override("shadow_offset_y", 2)
	map_holder.add_child(marker)

	popup.popup_centered()
	call_deferred("_position_world_map_marker", map_holder, marker, position)
	_set_situation("World Map", "Current location: %s" % location.get("display_name", location.get("name", "Unknown")))


func _position_world_map_marker(map_holder: Control, marker: Label, position: Dictionary) -> void:
	var map_rect := _world_map_content_rect(map_holder.size)
	var x := clampf(float(position.get("x", 0.5)), 0.0, 1.0)
	var y := clampf(float(position.get("y", 0.5)), 0.0, 1.0)
	var marker_size := marker.custom_minimum_size
	marker.position = Vector2(
		map_rect.position.x + (map_rect.size.x * x) - (marker_size.x * 0.5),
		map_rect.position.y + (map_rect.size.y * y) - (marker_size.y * 0.5)
	)


func _world_map_content_rect(holder_size: Vector2) -> Rect2:
	if holder_size.x <= 0 or holder_size.y <= 0:
		return Rect2(Vector2.ZERO, WORLD_MAP_SIZE)
	var holder_aspect := holder_size.x / holder_size.y
	if holder_aspect > WORLD_MAP_ASPECT:
		var image_width := holder_size.y * WORLD_MAP_ASPECT
		return Rect2(Vector2((holder_size.x - image_width) * 0.5, 0), Vector2(image_width, holder_size.y))
	var image_height := holder_size.x / WORLD_MAP_ASPECT
	return Rect2(Vector2(0, (holder_size.y - image_height) * 0.5), Vector2(holder_size.x, image_height))


func _open_equip_popup() -> void:
	_equip_choices = []
	var popup := PopupMenu.new()
	for item in _last_state.get("inventory_items", []):
		if typeof(item) != TYPE_DICTIONARY or str(item.get("type", "")) != "equipment":
			continue
		var item_id := str(item.get("item_id", ""))
		for slot in item.get("valid_slots", []):
			var target_slot := str(slot)
			if item_id == "" or target_slot == "":
				continue
			var label := "%s -> %s" % [item.get("name", item_id), _slot_label(target_slot)]
			popup.add_item(label, _equip_choices.size())
			popup.set_item_tooltip(_equip_choices.size(), str(item.get("description", "")))
			_equip_choices.append({"item_id": item_id, "slot": target_slot})
	if _equip_choices.is_empty():
		popup.add_item("No equippable items in inventory", 0)
		popup.set_item_disabled(0, true)
	add_child(popup)
	popup.id_pressed.connect(_on_equip_selected)
	popup.popup_hide.connect(popup.queue_free)
	popup.reset_size()
	var mouse := Vector2i(get_viewport().get_mouse_position())
	popup.popup(Rect2i(mouse.x, mouse.y, 0, 0))


func _on_equip_selected(idx: int) -> void:
	if idx < 0 or idx >= _equip_choices.size():
		return
	var choice: Dictionary = _equip_choices[idx]
	api.send_action({"action": "EQUIP_ITEM", "item_id": choice.get("item_id", ""), "slot": choice.get("slot", "")})


func _open_use_popup() -> void:
	_use_choices = []
	var popup := PopupMenu.new()
	for item in _last_state.get("inventory_items", []):
		if typeof(item) != TYPE_DICTIONARY or not bool(item.get("usable", false)):
			continue
		var item_id := str(item.get("item_id", ""))
		if item_id == "":
			continue
		var label := "%s x%s" % [str(item.get("name", item_id)), _format_quantity(item.get("count", 1))]
		var index := _use_choices.size()
		popup.add_item(label, index)
		popup.set_item_tooltip(index, str(item.get("description", "")))
		_use_choices.append({"item_id": item_id})
	if _use_choices.is_empty():
		popup.add_item("No usable items in inventory", 0)
		popup.set_item_disabled(0, true)
	add_child(popup)
	popup.id_pressed.connect(_on_use_selected)
	popup.popup_hide.connect(popup.queue_free)
	popup.reset_size()
	var mouse := Vector2i(get_viewport().get_mouse_position())
	popup.popup(Rect2i(mouse.x, mouse.y, 0, 0))


func _on_use_selected(idx: int) -> void:
	if idx < 0 or idx >= _use_choices.size():
		return
	var choice: Dictionary = _use_choices[idx]
	api.send_action({"action": "USE_ITEM", "item_id": choice.get("item_id", "")})


func _open_unequip_popup() -> void:
	_unequip_choices = []
	var popup := PopupMenu.new()
	var player: Dictionary = _last_state.get("player", {})
	var equipment: Dictionary = player.get("equipment", {})
	var details: Dictionary = player.get("equipment_details", {})
	for slot in equipment.keys():
		var raw_item_id = equipment.get(slot)
		if raw_item_id == null or str(raw_item_id) == "":
			continue
		var item_id := str(raw_item_id)
		var equipped: Dictionary = details.get(slot, {})
		var label := "%s: %s" % [_slot_label(str(slot)), equipped.get("display_name", item_id)]
		popup.add_item(label, _unequip_choices.size())
		popup.set_item_tooltip(_unequip_choices.size(), str(equipped.get("description", "")))
		_unequip_choices.append({"slot": str(slot)})
	if _unequip_choices.is_empty():
		popup.add_item("No equipment is currently worn", 0)
		popup.set_item_disabled(0, true)
	add_child(popup)
	popup.id_pressed.connect(_on_unequip_selected)
	popup.popup_hide.connect(popup.queue_free)
	popup.reset_size()
	var mouse := Vector2i(get_viewport().get_mouse_position())
	popup.popup(Rect2i(mouse.x, mouse.y, 0, 0))


func _on_unequip_selected(idx: int) -> void:
	if idx < 0 or idx >= _unequip_choices.size():
		return
	var choice: Dictionary = _unequip_choices[idx]
	api.send_action({"action": "UNEQUIP_ITEM", "slot": choice.get("slot", "")})


func _show_shop(result: Dictionary) -> void:
	_shop_choices = []
	var shop: Dictionary = result.get("shop", {})
	var shop_id := str(shop.get("id", ""))
	var popup := PopupMenu.new()
	for item in result.get("stock", []):
		if typeof(item) != TYPE_DICTIONARY:
			continue
		var item_id := str(item.get("item_id", ""))
		if item_id == "":
			continue
		var label := "%s - %s" % [str(item.get("name", item_id)), _format_price(item.get("price", {}))]
		popup.add_item(label, _shop_choices.size())
		popup.set_item_tooltip(_shop_choices.size(), str(item.get("description", "")))
		_shop_choices.append({"shop_id": shop_id, "item_id": item_id})
	if _shop_choices.is_empty():
		popup.add_item("No stock available", 0)
		popup.set_item_disabled(0, true)
	add_child(popup)
	popup.id_pressed.connect(_on_shop_selected)
	popup.popup_hide.connect(popup.queue_free)
	popup.reset_size()
	var mouse := Vector2i(get_viewport().get_mouse_position())
	popup.popup(Rect2i(mouse.x, mouse.y, 0, 0))
	_set_situation(str(shop.get("display_name", "Market")), str(shop.get("description", "Available wares are listed.")))


func _on_shop_selected(idx: int) -> void:
	if idx < 0 or idx >= _shop_choices.size():
		return
	var choice: Dictionary = _shop_choices[idx]
	api.send_action({"action": "BUY_ITEM", "shop_id": choice.get("shop_id", ""), "item_id": choice.get("item_id", "")})


func _has_equipment_inventory() -> bool:
	for item in _last_state.get("inventory_items", []):
		if typeof(item) != TYPE_DICTIONARY or str(item.get("type", "")) != "equipment":
			continue
		var slots: Array = item.get("valid_slots", [])
		if not slots.is_empty():
			return true
	return false


func _has_equipped_items() -> bool:
	var player: Dictionary = _last_state.get("player", {})
	for item_id in player.get("equipment", {}).values():
		if item_id != null and str(item_id) != "":
			return true
	return false


func _has_map_position() -> bool:
	var location: Dictionary = _last_state.get("location", {})
	var position = location.get("map_position", {})
	return typeof(position) == TYPE_DICTIONARY and position.has("x") and position.has("y")


func _has_available_shop() -> bool:
	return not _last_state.get("shops", []).is_empty()


func _has_available_trainer() -> bool:
	return not _last_state.get("trainers", []).is_empty()


func _has_usable_item() -> bool:
	for item in _last_state.get("inventory_items", []):
		if typeof(item) == TYPE_DICTIONARY and bool(item.get("usable", false)):
			return true
	return false


func _show_trainer(result: Dictionary) -> void:
	_trainer_choices = []
	var trainer: Dictionary = result.get("trainer", {})
	var trainer_id := str(trainer.get("id", ""))
	var popup := PopupMenu.new()
	for technique in result.get("techniques", []):
		if typeof(technique) != TYPE_DICTIONARY:
			continue
		var skill_id := str(technique.get("skill_id", ""))
		if skill_id == "":
			continue
		var known := bool(technique.get("already_known", false))
		var affordable := bool(technique.get("affordable", true))
		var suffix := ""
		if known:
			suffix = " (known)"
		elif not affordable:
			suffix = " (need funds)"
		var label := "%s - %s%s" % [str(technique.get("name", skill_id)), _format_price(technique.get("price", {})), suffix]
		var index := _trainer_choices.size()
		popup.add_item(label, index)
		popup.set_item_tooltip(index, str(technique.get("description", "")))
		popup.set_item_disabled(index, known or not affordable)
		_trainer_choices.append({"trainer_id": trainer_id, "skill_id": skill_id})
	if _trainer_choices.is_empty():
		popup.add_item("No techniques on offer", 0)
		popup.set_item_disabled(0, true)
	add_child(popup)
	popup.id_pressed.connect(_on_trainer_selected)
	popup.popup_hide.connect(popup.queue_free)
	popup.reset_size()
	var mouse := Vector2i(get_viewport().get_mouse_position())
	popup.popup(Rect2i(mouse.x, mouse.y, 0, 0))
	_set_situation(str(trainer.get("display_name", "Technique Master")), str(trainer.get("description", "Techniques available to learn are listed.")))


func _on_trainer_selected(idx: int) -> void:
	if idx < 0 or idx >= _trainer_choices.size():
		return
	var choice: Dictionary = _trainer_choices[idx]
	api.send_action({"action": "LEARN_SKILL", "trainer_id": choice.get("trainer_id", ""), "skill_id": choice.get("skill_id", "")})


func _slot_label(slot: String) -> String:
	return slot.replace("_", " ").capitalize()


func _build_overlay() -> void:
	_overlay = Control.new()
	_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_overlay.visible = false
	_overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_overlay)

	_overlay_dim = ColorRect.new()
	_overlay_dim.color = Color(0, 0, 0, 0.55)
	_overlay_dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	_overlay_dim.mouse_filter = Control.MOUSE_FILTER_STOP
	_overlay_dim.gui_input.connect(_on_overlay_dim_input)
	_overlay.add_child(_overlay_dim)

	_overlay_panel = _make_panel(COLOR_PANEL, COLOR_BORDER_STRONG, 1)
	_overlay_panel.anchor_left = 0.15
	_overlay_panel.anchor_right = 0.85
	_overlay_panel.anchor_top = 0.07
	_overlay_panel.anchor_bottom = 0.93
	_overlay.add_child(_overlay_panel)

	var root := VBoxContainer.new()
	root.add_theme_constant_override("separation", 10)
	_overlay_panel.add_child(root)

	var header := HBoxContainer.new()
	root.add_child(header)
	_overlay_title = _make_label("INVENTORY", 20, COLOR_TITLE_GOLD)
	header.add_child(_overlay_title)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(spacer)
	header.add_child(_make_button("✕", func(): _close_overlay(), "Close this panel."))

	_overlay_content = VBoxContainer.new()
	_overlay_content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_overlay_content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(_overlay_content)

	_build_inventory_page()
	_build_equipment_page()
	_quest_text = _add_text_page("Journal")
	_status_text = _add_text_page("Status")
	_techniques_text = _add_text_page("Techniques")

	for page in _tab_pages:
		page.visible = false


func _make_tab_button(title: String, index: int) -> Button:
	var button := _make_button(title, func(): _open_overlay(index), "Open the %s panel." % title)
	button.focus_mode = Control.FOCUS_NONE
	button.custom_minimum_size = Vector2(0, 36)
	_tab_buttons.append(button)
	return button


func _open_overlay(index: int) -> void:
	if index < 0 or index >= _tab_pages.size():
		return
	_active_tab = index
	_overlay_title.text = TAB_TITLES[index].to_upper()
	for i in _tab_pages.size():
		_tab_pages[i].visible = (i == index)
	_overlay.visible = true
	_update_tab_button_states()


func _close_overlay() -> void:
	_active_tab = -1
	_overlay.visible = false
	_update_tab_button_states()


func _update_tab_button_states() -> void:
	for i in _tab_buttons.size():
		var active := (i == _active_tab)
		var button: Button = _tab_buttons[i]
		if active:
			button.add_theme_stylebox_override("normal", _make_button_style(Color("#1A2A33"), COLOR_TITLE_GOLD))
			button.add_theme_color_override("font_color", COLOR_TITLE_GOLD)
		else:
			button.add_theme_stylebox_override("normal", _make_button_style(COLOR_PANEL_SOFT, COLOR_BORDER))
			button.add_theme_color_override("font_color", COLOR_PRIMARY_TEXT)


func _on_overlay_dim_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_close_overlay()


func _build_inventory_page() -> void:
	var page := MarginContainer.new()
	page.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	page.size_flags_vertical = Control.SIZE_EXPAND_FILL
	page.add_theme_constant_override("margin_top", 8)
	_overlay_content.add_child(page)
	_tab_pages.append(page)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 6)
	page.add_child(box)

	var header := HBoxContainer.new()
	header.add_child(_make_label("INVENTORY", 14, COLOR_ANTIQUE_GOLD))
	var head_space := Control.new()
	head_space.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(head_space)
	_inventory_count = _make_label("0 / %d" % INVENTORY_CAPACITY, 13, COLOR_MUTED)
	header.add_child(_inventory_count)
	box.add_child(header)

	_inventory_text = RichTextLabel.new()
	_inventory_text.bbcode_enabled = true
	_inventory_text.fit_content = true
	_inventory_text.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_inventory_text.add_theme_color_override("default_color", COLOR_PRIMARY_TEXT)
	box.add_child(_inventory_text)

	var footer := HBoxContainer.new()
	_gold_label = _make_label("Gold: 0", 14, COLOR_ANTIQUE_GOLD)
	footer.add_child(_gold_label)
	var foot_space := Control.new()
	foot_space.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	footer.add_child(foot_space)
	_stones_label = _make_label("Spirit Stones: 0", 14, COLOR_INVENTORY_BLUE)
	footer.add_child(_stones_label)
	box.add_child(footer)


func _build_equipment_page() -> void:
	var page := MarginContainer.new()
	page.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	page.size_flags_vertical = Control.SIZE_EXPAND_FILL
	page.add_theme_constant_override("margin_top", 8)
	_overlay_content.add_child(page)
	_tab_pages.append(page)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 6)
	page.add_child(box)

	var header := HBoxContainer.new()
	header.add_child(_make_label("EQUIPMENT", 14, COLOR_ANTIQUE_GOLD))
	var head_space := Control.new()
	head_space.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(head_space)
	_equipment_count = _make_label("0 / %d worn" % EQUIPMENT_SLOT_ORDER.size(), 13, COLOR_MUTED)
	header.add_child(_equipment_count)
	box.add_child(header)

	_equipment_text = RichTextLabel.new()
	_equipment_text.bbcode_enabled = true
	_equipment_text.fit_content = true
	_equipment_text.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_equipment_text.add_theme_color_override("default_color", COLOR_PRIMARY_TEXT)
	box.add_child(_equipment_text)


func _add_text_page(title: String) -> RichTextLabel:
	var page := MarginContainer.new()
	page.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	page.size_flags_vertical = Control.SIZE_EXPAND_FILL
	page.add_theme_constant_override("margin_top", 8)
	_overlay_content.add_child(page)
	_tab_pages.append(page)

	var text := RichTextLabel.new()
	text.bbcode_enabled = true
	text.fit_content = true
	text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	text.size_flags_vertical = Control.SIZE_EXPAND_FILL
	text.add_theme_color_override("default_color", COLOR_PRIMARY_TEXT)
	page.add_child(text)
	return text


func _build_event_log(root: VBoxContainer) -> void:
	var log_panel := _make_panel()
	log_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(log_panel)

	var box := VBoxContainer.new()
	box.size_flags_vertical = Control.SIZE_EXPAND_FILL
	box.add_theme_constant_override("separation", 6)
	log_panel.add_child(box)

	var header := HBoxContainer.new()
	header.add_child(_make_label("EVENT LOG", 14, COLOR_ANTIQUE_GOLD))
	var space := Control.new()
	space.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(space)
	header.add_child(_make_button("Clear Log", func(): _log.clear(), "Clear the event log."))
	box.add_child(header)

	_log = RichTextLabel.new()
	_log.bbcode_enabled = true
	_log.scroll_following = true
	_log.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_log.add_theme_color_override("default_color", COLOR_MUTED)
	box.add_child(_log)

	_append("[color=#5FAF72]Welcome to Martial Path. Your journey as a cultivator begins.[/color]")


func _make_action_row() -> HBoxContainer:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	return row


func _make_action_grid(columns: int) -> GridContainer:
	var grid := GridContainer.new()
	grid.columns = columns
	grid.add_theme_constant_override("h_separation", 8)
	grid.add_theme_constant_override("v_separation", 8)
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return grid


func _clear_action_grids() -> void:
	for grid in [_cultivation_grid, _exploration_grid, _support_grid]:
		if grid != null:
			_clear_row(grid)


func _clear_row(container: Container) -> void:
	if container == null:
		return
	for child in container.get_children():
		child.queue_free()


func _make_portrait_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = COLOR_PANEL_SOFT
	style.border_color = COLOR_BORDER_STRONG
	style.set_border_width_all(1)
	style.set_corner_radius_all(32)
	return style


func _make_chip(caption: String, value: String, color: Color) -> PanelContainer:
	var chip := PanelContainer.new()
	chip.add_theme_stylebox_override("panel", _make_chip_style())
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 6)
	chip.add_child(row)
	row.add_child(_make_label(caption, 11, COLOR_MUTED))
	row.add_child(_make_label(value, 12, color))
	return chip


func _make_chip_style() -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = COLOR_PANEL_RAISED
	style.border_color = COLOR_BORDER
	style.set_border_width_all(1)
	style.set_corner_radius_all(12)
	style.content_margin_left = 10
	style.content_margin_right = 10
	style.content_margin_top = 4
	style.content_margin_bottom = 4
	return style


func _render_chips(location: Dictionary) -> void:
	_clear_row(_chips_row)
	var danger := str(location.get("danger", "Unknown"))
	_chips_row.add_child(_make_chip("DANGER", danger, Color(_danger_color(danger))))
	var qi_label := str(location.get("qi_density_label", location.get("qi_density", "?")))
	_chips_row.add_child(_make_chip("QI", qi_label, COLOR_QI))
	var resources: Array = location.get("resources", [])
	_chips_row.add_child(_make_chip("RESOURCES", _join_array(resources) if not resources.is_empty() else "None", COLOR_ANTIQUE_GOLD))


func _render_exits(location: Dictionary) -> void:
	_clear_row(_exits_row)
	var connections: Array = location.get("connections", [])
	if connections.is_empty():
		return
	_exits_row.add_child(_make_label("Exits", 12, COLOR_MUTED))
	for conn in connections:
		if typeof(conn) != TYPE_DICTIONARY:
			continue
		var exit_id := str(conn.get("id", ""))
		var exit_name := str(conn.get("name", exit_id))
		if exit_id == "":
			continue
		_exits_row.add_child(_make_button(exit_name, func(): api.travel(exit_id), "Travel to %s." % exit_name))


func _make_bar_group(caption: String, color: Color, background_color: Color) -> Dictionary:
	var box := VBoxContainer.new()
	box.custom_minimum_size = Vector2(150, 0)
	var cap := _make_label(caption, 13, COLOR_MUTED)
	box.add_child(cap)
	var bar := ProgressBar.new()
	bar.min_value = 0
	bar.max_value = 100
	bar.value = 0
	bar.show_percentage = false
	bar.custom_minimum_size = Vector2(150, 18)
	_apply_bar_style(bar, color, background_color)
	box.add_child(bar)
	return {"box": box, "bar": bar, "cap": cap}


func _make_panel(fill: Color = COLOR_PANEL, border: Color = COLOR_BORDER, border_width: int = 1) -> PanelContainer:
	var panel := PanelContainer.new()
	panel.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	panel.add_theme_stylebox_override("panel", _make_panel_style(fill, border, border_width))
	return panel


func _make_panel_style(fill: Color, border: Color = COLOR_BORDER, border_width: int = 1) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = fill
	style.border_color = border
	style.set_border_width_all(border_width)
	style.set_corner_radius_all(6)
	style.content_margin_left = 14
	style.content_margin_right = 14
	style.content_margin_top = 12
	style.content_margin_bottom = 12
	return style


func _make_label(text: String, size: int, color: Color) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", size)
	label.add_theme_color_override("font_color", color)
	# Keep single-line labels from collapsing to one-character-per-line when a
	# sibling (e.g. an expanding spacer in a header row) squeezes their width.
	# Long-form copy uses RichTextLabel, so plain labels never need wrapping.
	label.autowrap_mode = TextServer.AUTOWRAP_OFF
	return label


func _make_button(text: String, cb: Callable, tooltip: String = "") -> Button:
	var button := Button.new()
	button.text = text
	button.tooltip_text = tooltip
	button.pressed.connect(cb)
	button.add_theme_color_override("font_color", COLOR_PRIMARY_TEXT)
	button.add_theme_color_override("font_hover_color", COLOR_TITLE_GOLD)
	button.add_theme_stylebox_override("normal", _make_button_style(COLOR_PANEL_SOFT, COLOR_BORDER))
	button.add_theme_stylebox_override("hover", _make_button_style(Color("#1A2A33"), COLOR_ANTIQUE_GOLD))
	button.add_theme_stylebox_override("pressed", _make_button_style(COLOR_SECONDARY_BACKGROUND, COLOR_ANTIQUE_GOLD))
	return button


func _make_button_style(fill: Color, border: Color) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = fill
	style.border_color = border
	style.set_border_width_all(1)
	style.set_corner_radius_all(5)
	style.content_margin_left = 10
	style.content_margin_right = 10
	style.content_margin_top = 6
	style.content_margin_bottom = 6
	return style


func _apply_bar_style(bar: ProgressBar, color: Color, background_color: Color) -> void:
	bar.add_theme_stylebox_override("background", _make_bar_background_style(background_color))
	var fill := StyleBoxFlat.new()
	fill.bg_color = color
	fill.set_corner_radius_all(4)
	bar.add_theme_stylebox_override("fill", fill)


func _make_bar_background_style(fill: Color) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = fill
	style.border_color = COLOR_BORDER
	style.set_border_width_all(1)
	style.set_corner_radius_all(4)
	return style


# --- Networking glue -------------------------------------------------------

func _send(action_name: String) -> void:
	api.send_action({"action": action_name})


func _start_new_game() -> void:
	_showing_event_result = false
	api.new_game("Daoist", null)


func _on_state_loaded(state: Dictionary) -> void:
	if not _connected:
		_connected = true
		if debug_mode:
			_append("[color=#5FAF72]Connected to backend.[/color]")
	_refresh_state(state)


func _on_action_completed(result: Dictionary) -> void:
	_render_event(result)
	# Re-sync the authoritative state after mutating actions. Viewing a shop only
	# opens a menu from the returned stock, so refreshing immediately would block
	# the follow-up purchase request until the state request completes.
	if str(result.get("event", "")) != "SHOP":
		api.get_state()


func _on_request_failed(message: String) -> void:
	if debug_mode:
		_append("[color=#C0393A]API ERROR:[/color] " + message)
	else:
		_set_situation("Connection Problem", "The game engine is not responding. Start the local Martial Path backend and try again.")


# --- Rendering -------------------------------------------------------------

func _refresh_state(state: Dictionary) -> void:
	_last_state = state
	var player: Dictionary = state.get("player", {})
	if player.is_empty():
		return
	_destinations = state.get("destinations", [])

	_render_top_bar(player)
	_render_character(player)
	_render_location(state.get("location", {}))
	_render_inventory(state)
	_render_equipment(player)
	_render_quests(state.get("quests", []))
	_render_status_summary(player)
	_render_techniques(player)
	_render_actions(player)

	var in_combat := bool(state.get("in_combat", false))
	_set_combat_mode(in_combat)
	var enemy = state.get("enemy", null)
	if in_combat and enemy != null:
		_update_enemy(enemy)


func _render_top_bar(player: Dictionary) -> void:
	_name_label.text = str(player.get("name", "Unknown"))
	var hp := int(player.get("hp", 0))
	var mhp := int(max(1, int(player.get("max_hp", 1))))
	var qi := int(player.get("qi", 0))
	var mqi := int(max(1, int(player.get("max_qi", 1))))
	_hp_bar.max_value = mhp
	_hp_bar.value = hp
	_hp_text.text = "HP %d/%d" % [hp, mhp]
	_qi_bar.max_value = mqi
	_qi_bar.value = qi
	_qi_text.text = "Qi %d/%d" % [qi, mqi]
	var lifespan: Dictionary = player.get("lifespan", {})
	_year = int(lifespan.get("year", 0))
	_year_label.text = str(_year)


func _render_character(player: Dictionary) -> void:
	var cultivation: Dictionary = player.get("cultivation_state", {})
	var body: Dictionary = cultivation.get("body_transformation", {})
	var essence: Dictionary = cultivation.get("essence_gathering", {})
	var martial_talent: Dictionary = player.get("martial_talent", {})
	var body_talent: Dictionary = player.get("body_talent", {})
	var lifespan: Dictionary = player.get("lifespan", {})
	var body_progress := float(body.get("progress", player.get("progress", 0.0)))
	var body_required := float(body.get("required_progress", 100.0))
	var body_percent := float(body.get("progress_percent", body_progress))
	var essence_progress := float(essence.get("progress", player.get("essence_progress", 0.0)))
	var essence_required := float(essence.get("required_progress", 100.0))
	var essence_percent := float(essence.get("progress_percent", essence_progress))
	var player_name := str(player.get("name", "Daoist"))
	_char_name_label.text = player_name
	_char_path_label.text = "Path: %s" % player.get("path", "Unassigned")
	_char_realm_label.text = "Realm: %s" % body.get("display_name", player.get("realm", "-"))
	if player_name.length() > 0:
		_portrait_initial.text = player_name.substr(0, 1).to_upper()
	else:
		_portrait_initial.text = "?"
	var lines := ""
	lines += "[color=#D6A64A]VITALS[/color]\n"
	lines += "[color=#C7BCA8]Martial Talent:[/color] [color=#C77DFF]%s[/color]\n" % martial_talent.get("display_name", "Unknown")
	lines += "[color=#C7BCA8]Body Talent:[/color] [color=#79C85A]%s[/color]\n" % body_talent.get("display_name", "Unknown")
	lines += "[color=#C7BCA8]Lifespan:[/color] [color=#D6A64A]%s[/color]\n\n" % lifespan.get("display", "Unknown")
	lines += "[color=#C7BCA8]Body:[/color] [color=#79C85A][b]%s[/b][/color]\n" % body.get("display_name", player.get("realm", "-"))
	lines += "[color=#C7BCA8]Progress:[/color] %.1f / %.1f ([color=#79C85A]%.1f%%[/color])\n" % [body_progress, body_required, body_percent]
	lines += "[color=#C7BCA8]Strain:[/color] [color=#D27A2C]%s / 100[/color]   [color=#C7BCA8]Stability:[/color] [color=#79C85A]%s / 100[/color]\n" % [body.get("cultivation_strain", 0), body.get("foundation_stability", 100)]
	lines += "[color=#C7BCA8]Foundation:[/color] [color=#79C85A]%s[/color]   [color=#C7BCA8]Strength:[/color] [color=#79C85A]%s[/color]\n\n" % [body.get("foundation", 0), body.get("body_strength", player.get("body_strength", 0))]
	if bool(player.get("essence_unlocked", true)):
		lines += "[color=#C7BCA8]Essence:[/color] [color=#C77DFF][b]%s[/b][/color] %.1f / %.1f (%.1f%%)\n" % [essence.get("display_name", player.get("essence_cultivation", "-")), essence_progress, essence_required, essence_percent]
		lines += "[color=#C7BCA8]Essence Strain:[/color] [color=#D27A2C]%s / 100[/color]   [color=#C7BCA8]Essence Stability:[/color] [color=#79C85A]%s / 100[/color]\n\n" % [essence.get("cultivation_strain", 0), essence.get("foundation_stability", 100)]
	else:
		lines += "[color=#C7BCA8]Essence:[/color] [color=#C77DFF][b]Locked[/b][/color]\n"
		var req := str(essence.get("unlock_requirement", ""))
		if req != "":
			lines += "[color=#8F8A81]Requirement: %s[/color]\n\n" % req
		else:
			lines += "\n"
	lines += "[color=#D6A64A]COMBAT[/color]\n"
	lines += "[color=#C7BCA8]ATK:[/color] %s   [color=#C7BCA8]DEF:[/color] %s\n" % [player.get("attack", 0), player.get("defense", 0)]
	lines += "[color=#C7BCA8]Comprehension:[/color] %s\n" % player.get("comprehension", 0)
	lines += "[color=#C7BCA8]Reputation:[/color] %s" % player.get("reputation", 0)
	_set_rich_text(_character_text, lines)
	_body_progress_bar.max_value = 100
	_body_progress_bar.value = body_percent
	_body_progress_text.text = "Body Progress %.1f / %.1f" % [body_progress, body_required]


func _render_location(location: Dictionary) -> void:
	if location.is_empty():
		_location_title.text = "Unknown"
		_artwork_texture.visible = false
		_artwork_label.text = ""
		_set_rich_text(_location_text, "")
		_clear_row(_chips_row)
		_clear_row(_exits_row)
		return
	var loc_name := str(location.get("name", location.get("display_name", "Unknown")))
	_location_title.text = loc_name.to_upper()
	var tex := _load_location_texture(str(location.get("id", "")))
	if tex != null:
		_artwork_texture.texture = tex
		_artwork_texture.visible = true
		_artwork_label.text = ""
	else:
		_artwork_texture.texture = null
		_artwork_texture.visible = false
		_artwork_label.text = loc_name
	_set_rich_text(_location_text, str(location.get("description", "")))
	_render_chips(location)
	_render_exits(location)


func _load_texture(path: String) -> Texture2D:
	# Prefer the imported resource (efficient, works in exports); fall back to
	# reading the raw PNG so art still shows before the Godot editor has imported
	# the files (ResourceLoader.exists stays false until the editor imports them).
	if ResourceLoader.exists(path):
		return load(path)
	if FileAccess.file_exists(path):
		var img := Image.new()
		if img.load(path) == OK:
			return ImageTexture.create_from_image(img)
	return null


func _load_location_texture(location_id: String) -> Texture2D:
	if location_id == "":
		return null
	if _location_texture_cache.has(location_id):
		return _location_texture_cache[location_id]
	var tex := _load_texture("res://assets/locations/%s.png" % location_id)
	_location_texture_cache[location_id] = tex
	return tex


func _render_inventory(state: Dictionary) -> void:
	var items: Array = state.get("inventory_items", [])
	var player: Dictionary = state.get("player", {})
	_inventory_count.text = "%d / %d" % [items.size(), INVENTORY_CAPACITY]
	var lines := "[color=#D6A64A]INVENTORY[/color]\n"
	var stones := 0
	for item in items:
		if typeof(item) != TYPE_DICTIONARY:
			continue
		if str(item.get("item_id", "")) == "spirit_stone":
			stones = int(item.get("count", 0))
		lines += "[color=#F2E8D5][b]%s[/b][/color]  [color=#D6A64A]x%s[/color]\n" % [item.get("name", "Item"), _format_quantity(item.get("count", 0))]
		lines += "[color=#8F8A81]%s[/color]\n\n" % item.get("description", "")
	if lines == "":
		lines = "[color=#8F8A81]Your storage ring is empty.[/color]"
	_set_rich_text(_inventory_text, lines.strip_edges())
	_gold_label.text = "Gold: %s" % player.get("gold", 0)
	_stones_label.text = "Spirit Stones: %s" % stones


func _render_equipment(player: Dictionary) -> void:
	var slots: Dictionary = player.get("equipment", {})
	var details: Dictionary = player.get("equipment_details", {})
	var lines := ""
	var worn := 0
	for pair in EQUIPMENT_SLOT_ORDER:
		var slot_id := str(pair[0])
		var slot_label := str(pair[1])
		var item_id = slots.get(slot_id, null)
		if item_id == null or str(item_id) == "":
			lines += "[color=#C7BCA8]%s[/color]  [color=#5A554C](empty)[/color]\n" % slot_label
		else:
			worn += 1
			var info: Dictionary = details.get(slot_id, {})
			var item_name := str(info.get("display_name", item_id))
			var rarity := str(info.get("rarity", "")).replace("_", " ").capitalize()
			lines += "[color=#C7BCA8]%s[/color]  [color=#F2E8D5][b]%s[/b][/color]" % [slot_label, item_name]
			if rarity != "":
				lines += "  [color=#D6A64A](%s)[/color]" % rarity
			lines += "\n"
	_set_rich_text(_equipment_text, lines.strip_edges())
	_equipment_count.text = "%d / %d worn" % [worn, EQUIPMENT_SLOT_ORDER.size()]


func _render_status_summary(player: Dictionary) -> void:
	var cultivation: Dictionary = player.get("cultivation_state", {})
	var body: Dictionary = cultivation.get("body_transformation", {})
	var martial_talent: Dictionary = player.get("martial_talent", {})
	var body_talent: Dictionary = player.get("body_talent", {})
	var lifespan: Dictionary = player.get("lifespan", {})
	var balance: Dictionary = cultivation.get("balance", {})
	var safety: Dictionary = cultivation.get("breakthrough_safety", {})
	var lines := "[color=#D6A64A]DETAILED STATUS[/color]\n\n"
	lines += "[color=#C7BCA8]HP:[/color] [color=#D94B4B]%s / %s[/color]\n" % [player.get("hp", 0), player.get("max_hp", 0)]
	lines += "[color=#C7BCA8]Qi:[/color] [color=#3B9FE8]%s / %s[/color]\n" % [player.get("qi", 0), player.get("max_qi", 0)]
	lines += "[color=#C7BCA8]Attack:[/color] %s   [color=#C7BCA8]Defense:[/color] %s\n" % [player.get("attack", 0), player.get("defense", 0)]
	var effective: Dictionary = player.get("effective_stats", {})
	if not effective.is_empty():
		lines += "[color=#C7BCA8]Effective ATK/DEF:[/color] %s / %s\n" % [effective.get("attack", player.get("attack", 0)), effective.get("defense", player.get("defense", 0))]
	lines += "[color=#C7BCA8]Comprehension:[/color] %s   [color=#C7BCA8]Reputation:[/color] %s\n" % [player.get("comprehension", 0), player.get("reputation", 0)]
	lines += "[color=#C7BCA8]Morality:[/color] %s   [color=#C7BCA8]EXP:[/color] %s\n\n" % [player.get("morality", 0), player.get("exp", 0)]
	lines += "[color=#C7BCA8]Martial Talent:[/color] [color=#C77DFF]%s[/color]\n" % martial_talent.get("display_name", "Unknown")
	lines += "[color=#C7BCA8]Body Talent:[/color] [color=#79C85A]%s[/color]\n" % body_talent.get("display_name", "Unknown")
	lines += "[color=#C7BCA8]Lifespan:[/color] [color=#D6A64A]%s[/color]\n" % lifespan.get("display", "Unknown")
	lines += "[color=#C7BCA8]Body Foundation:[/color] [color=#79C85A]%s[/color]\n" % body.get("foundation", 0)
	lines += "[color=#C7BCA8]Cultivation Strain:[/color] [color=#D27A2C]%s / 100[/color]\n" % body.get("cultivation_strain", 0)
	lines += "[color=#C7BCA8]Foundation Stability:[/color] [color=#79C85A]%s / 100[/color]\n" % body.get("foundation_stability", 100)
	lines += "[color=#C7BCA8]Soul Strength:[/color] [color=#C77DFF]%s[/color]\n" % player.get("soul_strength", 0)
	lines += "[color=#C7BCA8]Foundation Quality:[/color] %s\n" % player.get("foundation_quality", 0)
	lines += "[color=#C7BCA8]Balance:[/color] %s\n" % balance.get("status", "-")
	lines += "[color=#C7BCA8]Breakthrough Safety:[/color] %s (%s)\n" % [safety.get("level", "-"), safety.get("score", 0)]
	lines += "[color=#C7BCA8]Location:[/color] [color=#51BDED]%s[/color]" % player.get("current_location", "unknown")
	_set_rich_text(_status_text, lines)


func _render_quests(quests: Array) -> void:
	var lines := "[color=#D6A64A]JOURNAL[/color]\n\n"
	var has_active := false
	for quest in quests:
		if typeof(quest) != TYPE_DICTIONARY:
			continue
		var status := str(quest.get("status", "locked"))
		if status == "locked" or status == "hidden":
			continue
		has_active = true
		lines += "[color=#F0C76A][b]%s[/b][/color]  [color=#8F8A81]%s[/color]\n" % [quest.get("title", "Quest"), status.capitalize()]
		for objective in quest.get("objectives", []):
			var cur := int(objective.get("current", 0))
			var req := int(objective.get("required", 1))
			var col := "#70D36B" if cur >= req else "#C7BCA8"
			lines += "  [color=%s]%s: %s/%s[/color]\n" % [col, objective.get("text", "Objective"), cur, req]
		lines += "\n"
	if not has_active:
		lines += "[color=#8F8A81]No active quests yet. Explore to uncover your path.[/color]"
	_set_rich_text(_quest_text, lines.strip_edges())


func _render_techniques(player: Dictionary) -> void:
	var skills = player.get("skills", [])
	var lines := "[color=#D6A64A]TECHNIQUES[/color]\n\n"
	if skills.is_empty():
		lines += "[color=#8F8A81]No techniques known.[/color]"
		_set_rich_text(_techniques_text, lines)
		return
	for skill in skills:
		if typeof(skill) == TYPE_DICTIONARY:
			var is_active := str(skill.get("type", "")) == "active"
			var head_col := "#D6A64A" if is_active else "#51BDED"
			lines += "[color=%s][b]%s[/b][/color]\n" % [head_col, skill.get("name", skill.get("id", "Technique"))]
			if is_active:
				lines += "[color=#8F8A81]Active | Qi Cost: %s | Cooldown: %s[/color]\n" % [skill.get("qi_cost", 0), skill.get("cooldown", 0)]
			else:
				lines += "[color=#8F8A81]Passive[/color]\n"
			var desc := str(skill.get("description", ""))
			if desc != "":
				lines += "[color=#C7BCA8]%s[/color]\n" % desc
			lines += "\n"
		else:
			lines += "[color=#F2E8D5]%s[/color]\n" % _title_from_id(str(skill))
	_set_rich_text(_techniques_text, lines.strip_edges())


func _set_combat_mode(active: bool) -> void:
	_combat_actions.visible = active
	_action_box.visible = not active
	_combat_panel.visible = active


func _update_enemy(enemy: Dictionary) -> void:
	_enemy_name.text = "%s (%s)" % [str(enemy.get("name", "?")), str(enemy.get("realm", "Unknown Realm"))]
	_enemy_hp_bar.max_value = int(max(1, int(enemy.get("max_hp", 1))))
	_enemy_hp_bar.value = int(enemy.get("hp", 0))
	var rewards: Dictionary = enemy.get("reward_preview", {})
	var lines := ""
	lines += "Enemy HP: %s/%s\n" % [enemy.get("hp", 0), enemy.get("max_hp", 0)]
	lines += "Threat: [color=#D27A2C]%s[/color]\n" % enemy.get("threat", "Unknown")
	lines += "Possible EXP: %s\n" % rewards.get("exp", 0)
	lines += "Possible Items: %s" % _join_array(rewards.get("items", []))
	_set_rich_text(_enemy_details, lines)


func _render_event(result: Dictionary) -> void:
	_showing_event_result = true
	var event := str(result.get("event", ""))
	match event:
		"TRAIN_RESULT":
			var title := "Body Training" if str(result.get("track_id", "")) == "body_transformation" else "Essence Training"
			var text := str(result.get("player_message", "You cultivate steadily."))
			text += "\n\nProgress +%s | %s / %s | EXP +%s" % [result.get("progress_gained", result.get("gained", 0)), result.get("progress", 0), result.get("required_progress", 100), result.get("exp_gained", 0)]
			if result.has("current_strain"):
				text += "\nStrain: %s / 100" % result.get("current_strain", 0)
			_set_situation(title, text)
			_append("Cultivated: Progress +%s, EXP +%s" % [result.get("progress_gained", result.get("gained", 0)), result.get("exp_gained", 0)])
		"BREAKTHROUGH_RESULT":
			_render_breakthrough(result)
		"STABILISE_RESULT":
			var text := str(result.get("player_message", "You steady your foundation."))
			text += "\n\nStrain -%s | Stability +%s | Comprehension +%s" % [result.get("strain_reduced", 0), result.get("foundation_gained", 0), result.get("comprehension_gain", 0)]
			_set_situation("Stabilise Foundation", text)
			_append("Stabilised: Strain %s / 100, Stability %s / 100" % [result.get("current_strain", 0), result.get("foundation_stability", 0)])
		"STARTING_FATE_ROLLED":
			_set_situation("Starting Talents", str(result.get("player_message", "Your starting talents have been revealed.")))
		"STARTING_FATE_ACCEPTED":
			_set_situation("Starting Talents", str(result.get("player_message", "You accept your starting talents.")))
		"PLAYER_DIED":
			var age_text := str(result.get("age_years", "?"))
			_set_situation("Your Dao Ends", "%s\n\n[color=#C0393A]You perished at the age of %s. Your journey is over.[/color]" % [str(result.get("player_message", "Your lifespan is exhausted.")), age_text])
			_append("[color=#C0393A]You died of old age at %s.[/color]" % age_text)
		"CHARACTER_ENCOUNTER":
			_render_character_encounter(result)
		"CHARACTER_INTERACTION":
			_set_situation(str(result.get("name", "Conversation")), str(result.get("player_message", "They acknowledge you.")))
			_append("Talked with %s" % result.get("name", result.get("character_id", "someone")))
		"EXPLORE_RESULT":
			_set_situation("Exploration", str(result.get("text", "You roam the wilds.")))
			_append(str(result.get("text", "Explored the area.")))
		"COMBAT":
			_set_combat_mode(true)
			_update_enemy(result.get("enemy", {}))
			_set_situation("Combat Encounter", str(result.get("text", "A battle begins!")))
			_append("[color=#D27A2C]%s[/color]" % str(result.get("text", "A battle begins!")))
		"COMBAT_TURN":
			_render_turns(result)
			_sync_combat_bars(result)
		"COMBAT_END":
			_render_combat_end(result)
		"LOOT":
			_set_situation("Loot Found", "Obtained %s x%s." % [result.get("name", "item"), _format_quantity(result.get("count", 1))])
			_append("Loot gained: %s x%s" % [result.get("name", "item"), _format_quantity(result.get("count", 1))])
		"SPECIAL":
			_render_special(result)
		"ITEM_USED":
			_set_situation("Item Used", "You use %s. Remaining: %s" % [result.get("name", "item"), _format_quantity(result.get("remaining", 0))])
			_append("Used %s" % result.get("name", "item"))
		"SHOP":
			_show_shop(result)
			_append("Opened %s" % result.get("shop", {}).get("display_name", "market"))
		"ITEM_PURCHASED":
			_set_situation("Purchased", str(result.get("player_message", "Item purchased.")))
			_append("Purchased %s for %s" % [result.get("name", result.get("item_id", "item")), _format_price(result.get("price", {}))])
		"TRAINER":
			_show_trainer(result)
			_append("Consulted %s" % result.get("trainer", {}).get("display_name", "a technique master"))
		"SKILL_LEARNED":
			var price_text := ""
			if result.has("price") and typeof(result.get("price")) == TYPE_DICTIONARY and not result.get("price", {}).is_empty():
				price_text = " (%s)" % _format_price(result.get("price", {}))
			_set_situation("Technique Learned", str(result.get("player_message", "You learn a new technique.")))
			_append("Learned %s%s" % [result.get("name", result.get("skill_id", "a technique")), price_text])
		"EQUIP_ITEM_RESULT":
			_set_situation("Equipped", str(result.get("player_message", "Item equipped.")))
			_append("Equipped %s to %s" % [result.get("display_name", result.get("item_id", "item")), result.get("slot", "slot")])
		"UNEQUIP_ITEM_RESULT":
			_set_situation("Unequipped", str(result.get("player_message", "Item unequipped.")))
			_append("Unequipped %s from %s" % [result.get("display_name", result.get("item_id", "item")), result.get("slot", "slot")])
		"REST_RESULT":
			_set_situation("Rest", "Recovered %s HP and %s Qi." % [result.get("healed", 0), result.get("qi_restored", 0)])
			_append("Rested: HP +%s, Qi +%s" % [result.get("healed", 0), result.get("qi_restored", 0)])
		"MEDITATE_RESULT":
			_set_situation("Meditation", "Qi restored: %s\nComprehension gained: %s" % [result.get("qi_restored", 0), result.get("comprehension_gain", 0)])
			_append("Meditated: Qi +%s" % result.get("qi_restored", 0))
		"TRAVEL_RESULT":
			var location: Dictionary = result.get("location", {})
			_set_situation(str(location.get("name", "Travel")), str(location.get("description", "You arrive.")))
			_append("Travelled to %s" % location.get("name", "a new location"))
		"SAVE_RESULT":
			_set_situation("Saved", "Your progress has been saved." if bool(result.get("success", false)) else _translate_reason(str(result.get("reason", "WRITE_FAILED")), result))
			_append("Saved game." if bool(result.get("success", false)) else "Save failed.")
		"LOAD_RESULT":
			_set_situation("Loaded", "Your saved game has been loaded." if bool(result.get("success", false)) else _translate_reason(str(result.get("reason", "SAVE_NOT_FOUND")), result))
			_append("Loaded game." if bool(result.get("success", false)) else "Load failed.")
		"INVENTORY":
			_show_inventory(result)
		"STATUS":
			_show_status(result)
		"ERROR":
			var reason := str(result.get("reason", "unknown"))
			_set_situation("Unable To Act", _translate_reason(reason, result))
			if debug_mode:
				_append("[color=#C0393A]Error:[/color] %s" % reason)
		"HELP":
			_set_situation("Command Reference", "Train, gather essence, explore, rest, meditate, break through, travel, save, or open inventory/status.")
		"QUIT":
			_append("Farewell, cultivator.")
		_:
			if debug_mode:
				_append(str(result))


func _render_breakthrough(result: Dictionary) -> void:
	if bool(result.get("success", false)):
		var text := "%s\n\n%s -> %s" % [result.get("player_message", "Breakthrough achieved."), result.get("previous", ""), result.get("cultivation", "")]
		_set_situation("Breakthrough", text)
		_append("[color=#D6A84F]Breakthrough:[/color] %s" % result.get("cultivation", ""))
		_render_quest_updates(result.get("quest_updates", []))
		return
	var reason := str(result.get("reason", result.get("message_code", "FAILED_ATTEMPT")))
	_set_situation("Breakthrough Failed", _translate_reason(reason, result))
	_append("Breakthrough failed.")


func _render_character_encounter(result: Dictionary) -> void:
	_clear_action_grids()
	var characters: Array = result.get("characters", [])
	var text := str(result.get("player_message", "You encounter familiar cultivators nearby."))
	var names: Array = []
	for character in characters:
		if typeof(character) != TYPE_DICTIONARY:
			continue
		names.append(str(character.get("name", character.get("id", "Unknown"))))
		for option in character.get("options", []):
			if typeof(option) != TYPE_DICTIONARY:
				continue
			var action_name := str(option.get("action", ""))
			var character_id := str(option.get("character_id", character.get("id", "")))
			var label := "%s %s" % [option.get("label", "Act"), character.get("name", character_id)]
			_cultivation_grid.add_child(_make_action_card(label, str(character.get("relationship_tier", "")), func(): api.send_action({"action": action_name, "character_id": character_id})))
	_cultivation_grid.add_child(_make_action_card("Continue", "Return to normal actions", func(): _render_actions(_last_state.get("player", {}))))
	if names.size() > 0:
		text += "\n\n" + _join_array(names)
	_set_situation("Encounter", text)
	_append("Encountered named cultivators.")


func _render_special(result: Dictionary) -> void:
	var lines := str(result.get("text", "Something unusual happens."))
	var effect_lines: Array = []
	if result.has("healed"):
		effect_lines.append("HP +%s" % result.get("healed", 0))
	if result.has("qi_restored"):
		effect_lines.append("Qi +%s" % result.get("qi_restored", 0))
	if result.has("progress_boost"):
		effect_lines.append("Cultivation Progress +%s" % result.get("progress_boost", 0))
	if result.has("exp_gained"):
		effect_lines.append("EXP +%s" % result.get("exp_gained", 0))
	if effect_lines.size() > 0:
		lines += "\n\nEffects:\n" + _join_array(effect_lines)
	_set_situation("Discovery", lines)
	_append("Discovery: %s" % str(result.get("special_id", "special event")).replace("_", " "))


func _render_combat_end(result: Dictionary) -> void:
	_render_turns(result)
	var outcome := str(result.get("outcome", "?"))
	var text := "Outcome: %s" % outcome.capitalize()
	if outcome == "VICTORY":
		text += "\nEXP +%s" % result.get("exp_reward", 0)
		for drop in result.get("loot", []):
			text += "\nLoot: %s x%s" % [drop.get("name", "item"), _format_quantity(drop.get("count", 1))]
	elif outcome == "DEFEAT":
		var pen: Dictionary = result.get("penalty", {})
		text += "\nYou were rescued. Progress lost: %s, revived HP: %s." % [pen.get("progress_lost", 0), pen.get("revived_hp", 0)]
	_set_situation("Combat Ended", text)
	_append("Combat ended: %s" % outcome)
	_render_quest_updates(result.get("quest_updates", []))
	_set_combat_mode(false)


func _render_quest_updates(updates: Array) -> void:
	for update in updates:
		if typeof(update) == TYPE_DICTIONARY:
			_append("Quest complete: %s" % update.get("title", "Quest"))


func _render_turns(result: Dictionary) -> void:
	for turn_event in result.get("turn_events", []):
		_append("  " + _describe_turn(turn_event))


func _describe_turn(ev: Dictionary) -> String:
	var actor := str(ev.get("actor", ""))
	var action := str(ev.get("action", ""))
	match action:
		"ATTACK":
			if actor == "PLAYER":
				return "You strike for %s damage. (enemy HP %s)" % [ev.get("damage", 0), ev.get("target_hp", 0)]
			return "%s hits you for %s damage. (your HP %s)" % [ev.get("enemy_name", "Enemy"), ev.get("damage", 0), ev.get("target_hp", 0)]
		"SKILL":
			if ev.has("damage"):
				return "You unleash %s for %s damage. (enemy HP %s)" % [ev.get("skill", ""), ev.get("damage", 0), ev.get("target_hp", 0)]
			return "You channel %s." % ev.get("skill", "")
		"USE_ITEM":
			return "You use %s." % ev.get("item", "")
		"FLEE_SUCCESS":
			return "You slip away from the battle!"
		"FLEE_FAILED":
			return "You fail to escape!"
		_:
			return str(ev)


func _sync_combat_bars(result: Dictionary) -> void:
	if result.has("enemy_hp"):
		_enemy_hp_bar.max_value = int(result.get("enemy_max_hp", _enemy_hp_bar.max_value))
		_enemy_hp_bar.value = int(result.get("enemy_hp", 0))
		_enemy_name.text = str(result.get("enemy_name", _enemy_name.text))


func _show_inventory(result: Dictionary) -> void:
	_focus_tab(0)


func _show_status(result: Dictionary) -> void:
	var player: Dictionary = result.get("player", {})
	if not player.is_empty():
		_render_character(player)
		_render_status_summary(player)
	_focus_tab(3)


func _set_situation(title: String, text: String) -> void:
	# There is no dedicated situation panel any more; narrate to the event log.
	_append("[color=#F0C76A][b]%s[/b][/color] %s" % [title, text.replace("\n", "  ")])


func _set_rich_text(control: RichTextLabel, text: String) -> void:
	control.clear()
	control.append_text(text)


func _translate_reason(reason: String, result: Dictionary = {}) -> String:
	match reason:
		"INSUFFICIENT_PROGRESS":
			return "Your cultivation has not yet reached the required threshold.\n\nCurrent Progress: %s / %s\nContinue training, meditating, or seeking spiritual resources before attempting again." % [result.get("progress", 0), result.get("required_progress", 100)]
		"STRAIN_TOO_HIGH":
			return "Cultivation strain is too high for a safe breakthrough.\n\nCurrent Strain: %s / 100\nAllowed Strain: %s / 100\nStabilise your foundation before attempting again." % [result.get("current_strain", 0), result.get("max_allowed_strain", 45)]
		"FOUNDATION_UNSTABLE":
			return "Your foundation stability is too low for a safe breakthrough.\n\nCurrent Stability: %s / 100\nRequired Stability: %s / 100\nStabilise your foundation before attempting again." % [result.get("foundation_stability", 0), result.get("required_foundation_stability", 70)]
		"FAILED_ATTEMPT":
			return "Your foundation trembles and the breakthrough slips away. Stabilise your cultivation before attempting again."
		"PROGRESS":
			return "Your cultivation progress is not high enough yet."
		"FOUNDATION":
			return "Your foundation is not stable enough for a safe breakthrough."
		"ESSENCE_LOCKED_BY_BODY_PULSE":
			return "Essence Gathering has not opened yet. Complete Body Transformation's Pulse Condensation realm before gathering true essence."
		"NO_DESTINATION":
			return "Choose a destination before travelling."
		"UNKNOWN_LOCATION":
			return "That place is not known yet."
		"ALREADY_THERE":
			return "You are already there."
		"NO_ROUTE":
			return "There is no direct route from your current location."
		"SAVE_NOT_FOUND":
			return "No save exists in that slot."
		"SAVE_VERSION_MISMATCH":
			return "That save was created with an incompatible version."
		"SAVE_CORRUPT":
			return "That save file could not be read."
		"WRITE_FAILED":
			return "The game could not write the save file."
		"ITEM_NOT_OWNED":
			return "You do not have that item."
		"NO_SHOP_AVAILABLE":
			return "There is no market available at your current location."
		"SHOP_NOT_AVAILABLE":
			return "That market is not available at your current location."
		"SHOP_ITEM_NOT_AVAILABLE":
			return "That item is not sold at this market."
		"INSUFFICIENT_FUNDS":
			return "You do not have enough currency for that purchase."
		"SHOP_STOCK_TOO_LOW":
			return "The market does not have enough stock for that purchase."
		"NO_TRAINER_AVAILABLE":
			return "There is no technique master at your current location."
		"TRAINER_NOT_AVAILABLE":
			return "That technique master is not here."
		"TECHNIQUE_NOT_OFFERED":
			return "That technique is not taught here."
		"SKILL_ALREADY_KNOWN":
			return "You already know that technique."
		"UNKNOWN_SKILL":
			return "That technique does not exist."
		"CANNOT_STUDY_IN_COMBAT":
			return "You cannot study a technique manual mid-battle."
		"EQUIPMENT_QUANTITY_NOT_SUPPORTED":
			return "Equipment can only be purchased one at a time."
		"INVALID_QUANTITY":
			return "Choose a valid purchase quantity."
		"NOT_ENOUGH_QI":
			return "You do not have enough Qi for that technique."
		_:
			if debug_mode:
				return reason
			return "That action cannot be completed right now."


func _title_from_id(value: String) -> String:
	return value.replace("_", " ").capitalize()


func _format_quantity(value) -> String:
	if typeof(value) == TYPE_INT:
		return str(value)
	if typeof(value) == TYPE_FLOAT:
		var number := float(value)
		if is_equal_approx(number, round(number)):
			return str(int(round(number)))
		return "%.1f" % number
	return str(value)


func _format_price(price) -> String:
	if typeof(price) != TYPE_DICTIONARY:
		return str(price)
	var parts: Array[String] = []
	for currency in price.keys():
		var label := str(currency).replace("_", " ").capitalize()
		parts.append("%s %s" % [_format_quantity(price.get(currency, 0)), label])
	return ", ".join(parts)


func _join_array(values) -> String:
	var parts: Array[String] = []
	for value in values:
		parts.append(str(value))
	return ", ".join(parts)


func _danger_color(value: String) -> String:
	match value.to_lower():
		"safe", "low":
			return "#70D36B"
		"moderate":
			return "#E6B24A"
		"high", "deadly", "lethal":
			return "#E05A5A"
		_:
			return "#C7BCA8"


func _append(text: String) -> void:
	if _log == null:
		return
	if text.begins_with("  "):
		_log.append_text(text + "\n")
	else:
		_log.append_text("[color=#8F8A81][Year %d][/color] %s\n" % [_year, text])
