extends Control
## Martial Path - Godot frontend controller.
##
## Builds the UI in code, forwards commands to the Python backend through
## ApiClient, and renders returned state/result dictionaries. Presentation
## only: all gameplay rules remain in the Python engine.
##
## FILE LAYOUT: this controller owns the shell -- top bar, character dossier,
## location frame, chronicle, action grids and the styled dialogs -- and drives
## the API. The overlay's five tabs and the presentation kit live in their own
## scripts (UIKit.gd, InventoryPanel.gd, EquipmentPanel.gd, JournalPanel.gd,
## StatusPanel.gd, TechniquesPanel.gd) so each tab has exactly one writer;
## frontend-godot/tests/check_panels.gd smoke-checks them headlessly.
##
## DESIGN CONTRACT (direction: the category standard played straight at full
## commitment; craft bar: Slay the Spire / Wo Long / Tale of Immortal):
## THESIS: a xianxia interface carved like a lacquer screen - warm ink ground,
## gold-ruled panels, parchment text - where every tab is a purposeful spread.
## OWN-WORLD: #12100B ground, #1C1813 panels, gold #C9A24D hairline frames,
## parchment #E7DDC6 text, cinnabar #B03A2E accents, qi cyan #4FA8D8.
## STORY: the player always reads where they are, what they own, and how far
## their lifetime has run, without parsing a wall of text.
## FIRST VIEWPORT: top vitals rail; left character dossier with realm ladder;
## center location frame with art, chips; right chronicle; action
## grids as card menus with lock reasons stated plainly.
## FINISH: unreviewed and undocumented is unfinished; this build ends with the
## finish review, the verdict, DESIGN.md, and every shipping raster carrying
## its provenance.

const PANEL_MIN_WIDTH := 220
const CENTER_MIN_WIDTH := 420
const MARTIAL_THEME := preload("res://ui/themes/martial_path_theme.tres")
const GRAIN_TEXTURE := preload("res://assets/ink_grain.png")
const WORLD_MAP_PATH := "res://assets/sky_spill_continent_map.png"
const WORLD_MAP_SIZE := Vector2(960, 640)
const WORLD_MAP_ASPECT := 1.5

# --- Palette -----------------------------------------------------------------
# The palette and the stateless widget/stylebox factory live in UIKit, so the
# per-panel scripts (InventoryPanel, EquipmentPanel, ...) can dress themselves
# without inheriting this controller. The names stay local so the hundreds of
# call sites below read unchanged -- and there is still exactly one source of
# truth for every colour.
const COLOR_BACKGROUND := UIKit.COLOR_BACKGROUND
const COLOR_SECONDARY_BACKGROUND := UIKit.COLOR_SECONDARY_BACKGROUND
const COLOR_PANEL := UIKit.COLOR_PANEL
const COLOR_PANEL_SOFT := UIKit.COLOR_PANEL_SOFT
const COLOR_PANEL_RAISED := UIKit.COLOR_PANEL_RAISED
const COLOR_BORDER := UIKit.COLOR_BORDER
const COLOR_BORDER_STRONG := UIKit.COLOR_BORDER_STRONG
const COLOR_PRIMARY_TEXT := UIKit.COLOR_PRIMARY_TEXT
const COLOR_SECONDARY_TEXT := UIKit.COLOR_SECONDARY_TEXT
const COLOR_MUTED := UIKit.COLOR_MUTED
const COLOR_TITLE_GOLD := UIKit.COLOR_TITLE_GOLD
const COLOR_ANTIQUE_GOLD := UIKit.COLOR_ANTIQUE_GOLD
const COLOR_SEAL_RED := UIKit.COLOR_SEAL_RED
const COLOR_QI := UIKit.COLOR_QI
const COLOR_QI_DARK := UIKit.COLOR_QI_DARK
const COLOR_HP := UIKit.COLOR_HP
const COLOR_HP_DARK := UIKit.COLOR_HP_DARK
const COLOR_BODY := UIKit.COLOR_BODY
const COLOR_BODY_DARK := UIKit.COLOR_BODY_DARK
const COLOR_ESSENCE := UIKit.COLOR_ESSENCE
const COLOR_INVENTORY_BLUE := UIKit.COLOR_INVENTORY_BLUE
const COLOR_WARNING := UIKit.COLOR_WARNING
const COLOR_DANGER := UIKit.COLOR_DANGER
const COLOR_SUCCESS := UIKit.COLOR_SUCCESS

const INVENTORY_CAPACITY := UIKit.INVENTORY_CAPACITY
const EQUIPMENT_SLOT_ORDER := UIKit.EQUIPMENT_SLOT_ORDER

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
## The cultivator's portrait in the top rail (the identity cluster's face).
var _top_avatar: TextureRect
var _hp_bar: ProgressBar
var _qi_bar: ProgressBar
var _hp_text: Label
var _qi_text: Label
var _year_label: Label
var _season_label: Label
var _age_label: Label
var _world_btn: Button
var _last_world_view: Dictionary = {}

# Character panel refs (left).
var _portrait_initial: Label
var _portrait_texture: TextureRect
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
var _overlay_tab_buttons: Array = []
var _active_tab := -1

# Tab panels (inside the floating overlay). Each one builds itself, owns its own
# widgets and repaints from the state snapshot, so a UI change is a single-writer
# change to that panel's file rather than an edit to this controller.
var _inventory_panel: InventoryPanel
var _equipment_panel: EquipmentPanel
var _journal_panel: JournalPanel
var _status_panel: StatusPanel
var _techniques_panel: TechniquesPanel

# Action refs.
var _action_box: VBoxContainer
var _body_cultivation_grid: GridContainer
var _essence_cultivation_grid: GridContainer
var _exploration_grid: GridContainer
var _support_grid: GridContainer
var _combat_actions: HBoxContainer
var _log: RichTextLabel
var _narrative_text: RichTextLabel

# Cached destinations for the Travel popup (from the last state snapshot).
var _destinations: Array = []
var _travel_ids: Array = []
var _last_state: Dictionary = {}
var _equip_choices: Array = []
var _unequip_choices: Array = []
var _shop_choices: Array = []
var _trainer_choices: Array = []
var _sect_choices: Array = []
var _current_sect_id: String = ""
var _talent_choices: Array = []
var _known_skills: Array = []
var _use_choices: Array = []
var _refine_ids: Array[String] = []
var _dao_ids: Array[String] = []
var _unlock_choices: Array = []
var _cooldowns: Dictionary = {}

# Cosmetic display state (the engine tracks years via lifespan).
var _year := 0

# Active styled dialog (travel, shop, trainer, sects, refine, talents, dao,
# legacy, settings). One at a time; carries {panel, content, title}.
var _dialog: Dictionary = {}


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

	# Ink grain: a faint tileable fiber texture so large grounds read as
	# material rather than a flat fill.
	var grain := TextureRect.new()
	grain.texture = GRAIN_TEXTURE
	grain.stretch_mode = TextureRect.STRETCH_TILE
	grain.set_anchors_preset(Control.PRESET_FULL_RECT)
	grain.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(grain)

	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 36)
	margin.add_theme_constant_override("margin_top", 26)
	margin.add_theme_constant_override("margin_right", 36)
	margin.add_theme_constant_override("margin_bottom", 26)
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
	top.custom_minimum_size = Vector2(0, 86)
	root.add_child(top)

	var row := HBoxContainer.new()
	row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_theme_constant_override("separation", 18)
	top.add_child(row)

	# The identity cluster: the cultivator's portrait and name, one click target
	# so the player can rename themselves and choose a portrait at any moment.
	var identity_body := HBoxContainer.new()
	identity_body.mouse_filter = Control.MOUSE_FILTER_IGNORE
	identity_body.add_theme_constant_override("separation", 12)

	_top_avatar = TextureRect.new()
	_top_avatar.custom_minimum_size = Vector2(52, 52)
	_top_avatar.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_top_avatar.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_top_avatar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var emblem_tex := _load_texture("res://icon.png")
	if emblem_tex != null:
		_top_avatar.texture = emblem_tex
	identity_body.add_child(_top_avatar)

	var title_box := VBoxContainer.new()
	title_box.custom_minimum_size = Vector2(260, 0)
	title_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	identity_body.add_child(title_box)

	var title := _make_label("MARTIAL PATH", 24, COLOR_TITLE_GOLD, true)
	title.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_box.add_child(title)
	_name_label = _make_label(Profile.player_name, 14, COLOR_SECONDARY_TEXT)
	_name_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	title_box.add_child(_name_label)

	var identity_card := _make_clickable_card(identity_body, false, Color(0, 0, 0, 0), func(): _open_identity())
	identity_card.size_flags_horizontal = Control.SIZE_SHRINK_BEGIN
	identity_card.tooltip_text = "Identity: set your cultivator's name and portrait."
	row.add_child(identity_card)

	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	row.add_child(spacer)

	var hp_group := _make_bar_group("HP", COLOR_HP, COLOR_HP_DARK)
	_hp_bar = hp_group["bar"]
	_hp_text = hp_group["cap"]
	row.add_child(hp_group["box"])

	var qi_group := _make_bar_group("QI", COLOR_QI, COLOR_QI_DARK)
	_qi_bar = qi_group["bar"]
	_qi_text = qi_group["cap"]
	row.add_child(qi_group["box"])

	var year_box := VBoxContainer.new()
	year_box.custom_minimum_size = Vector2(72, 0)
	row.add_child(year_box)
	year_box.add_child(_make_label("YEAR", 11, COLOR_MUTED))
	_year_label = _make_label("0", 17, COLOR_PRIMARY_TEXT)
	year_box.add_child(_year_label)

	# E.4: the living world's season chip (Yield/Travel/Odds shifts).
	var season_box := VBoxContainer.new()
	season_box.custom_minimum_size = Vector2(96, 0)
	row.add_child(season_box)
	season_box.add_child(_make_label("SEASON", 11, COLOR_MUTED))
	_season_label = _make_label("Spring", 17, COLOR_PRIMARY_TEXT)
	season_box.add_child(_season_label)

	# Age at a glance: the player must always know how long they have left.
	var age_box := VBoxContainer.new()
	age_box.custom_minimum_size = Vector2(128, 0)
	row.add_child(age_box)
	age_box.add_child(_make_label("AGE", 11, COLOR_MUTED))
	_age_label = _make_label("- / -", 17, COLOR_PRIMARY_TEXT)
	age_box.add_child(_age_label)

	for i in TAB_TITLES.size():
		row.add_child(_make_tab_button(TAB_TITLES[i], i))

	var settings_btn := _make_button("Settings", func(): _open_settings(), "Save, load, or start a new game.")
	settings_btn.custom_minimum_size = Vector2(96, 0)
	row.add_child(settings_btn)

	# E.1-E.5: the living world report (sects, market, rumors).
	_world_btn = _make_button("World", func(): _send_world_info(), "The living world: sects, market, rumors.")
	_world_btn.custom_minimum_size = Vector2(84, 0)
	row.add_child(_world_btn)


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

	# Right column: narrative output (the event log was removed; prose is the
	# single feed of what just happened).
	var right := VBoxContainer.new()
	right.custom_minimum_size = Vector2(PANEL_MIN_WIDTH, 0)
	right.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	right.size_flags_vertical = Control.SIZE_EXPAND_FILL
	right.size_flags_stretch_ratio = 26.0
	right.add_theme_constant_override("separation", 12)
	body.add_child(right)
	_build_narrative_panel(right)


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
	portrait_panel.custom_minimum_size = Vector2(76, 76)
	portrait_panel.clip_contents = true
	portrait_panel.add_theme_stylebox_override("panel", _make_portrait_style())
	portrait_panel.tooltip_text = "Set your name and portrait."
	portrait_panel.gui_input.connect(func(event: InputEvent):
		if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
			_open_identity())
	header.add_child(portrait_panel)

	var portrait_holder := Control.new()
	portrait_holder.mouse_filter = Control.MOUSE_FILTER_IGNORE
	portrait_panel.add_child(portrait_holder)
	_portrait_texture = TextureRect.new()
	_portrait_texture.set_anchors_preset(Control.PRESET_FULL_RECT)
	_portrait_texture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_portrait_texture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	_portrait_texture.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_portrait_texture.visible = false
	portrait_holder.add_child(_portrait_texture)
	# Monogram fallback: shown only while no portrait art can be loaded.
	_portrait_initial = _make_label("?", 30, COLOR_TITLE_GOLD, true)
	_portrait_initial.set_anchors_preset(Control.PRESET_FULL_RECT)
	_portrait_initial.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_portrait_initial.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_portrait_initial.mouse_filter = Control.MOUSE_FILTER_IGNORE
	portrait_holder.add_child(_portrait_initial)

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
	_body_progress_bar.custom_minimum_size = Vector2(0, 12)
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

	_location_title = _make_label("OUTER FOREST", 22, COLOR_TITLE_GOLD, true)
	box.add_child(_location_title)

	# Location artwork: a TextureRect (from res://assets/locations/<id>.png) with
	# a centred name label as the fallback when a location has no image yet.
	var art := PanelContainer.new()
	art.custom_minimum_size = Vector2(0, 200)
	art.size_flags_vertical = Control.SIZE_EXPAND_FILL
	art.clip_contents = true
	var art_style := _make_panel_style(Color("0E0C08"), COLOR_BORDER, 1)
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
	_enemy_hp_bar.custom_minimum_size = Vector2(0, 14)
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

	_action_box.add_child(_make_label("Body Cultivation", 12, COLOR_ANTIQUE_GOLD))
	_body_cultivation_grid = _make_action_grid(3)
	_action_box.add_child(_body_cultivation_grid)

	_action_box.add_child(_make_label("Essence Cultivation", 12, COLOR_ANTIQUE_GOLD))
	_essence_cultivation_grid = _make_action_grid(3)
	_action_box.add_child(_essence_cultivation_grid)

	_action_box.add_child(_make_label("Exploration", 12, COLOR_ANTIQUE_GOLD))
	_exploration_grid = _make_action_grid(4)
	_action_box.add_child(_exploration_grid)

	_action_box.add_child(_make_label("Commerce & Support", 12, COLOR_ANTIQUE_GOLD))
	_support_grid = _make_action_grid(4)
	_action_box.add_child(_support_grid)

	_combat_actions = _make_action_row()
	_combat_actions.visible = false
	box.add_child(_combat_actions)
	_rebuild_combat_actions()


func _render_actions(player: Dictionary) -> void:
	_clear_action_grids()
	var essence_unlocked := bool(player.get("essence_unlocked", true))
	var cultivation: Dictionary = player.get("cultivation_state", {})
	var essence: Dictionary = cultivation.get("essence_gathering", {})
	var req := str(essence.get("unlock_requirement", ""))
	var locked_reason := ""
	if not essence_unlocked:
		locked_reason = ("Locked - %s." % req) if req != "" else "Essence Gathering is still locked."

	_body_cultivation_grid.add_child(_make_action_card("Train Body", "Cultivate your body", func(): _send("TRAIN_BODY")))
	_body_cultivation_grid.add_child(_make_action_card("Stabilise Foundation", "Settle strain", func(): _send("STABILISE_FOUNDATION")))
	_body_cultivation_grid.add_child(_make_action_card("Body Breakthrough", "Attempt advancement", func(): _send("BODY_BREAKTHROUGH")))

	_essence_cultivation_grid.add_child(_make_action_card("Gather Essence", ("Absorb spiritual energy" if essence_unlocked else "Locked"), func(): _send("TRAIN_ESSENCE"), essence_unlocked, locked_reason))
	_essence_cultivation_grid.add_child(_make_action_card("Stabilise Essence", ("Settle essence strain" if essence_unlocked else "Locked"), func(): _send("STABILISE_ESSENCE"), essence_unlocked, locked_reason))
	_essence_cultivation_grid.add_child(_make_action_card("Essence Breakthrough", ("Attempt advancement" if essence_unlocked else "Locked"), func(): _send("ESSENCE_BREAKTHROUGH"), essence_unlocked, locked_reason))

	_exploration_grid.add_child(_make_action_card("Explore", "Search the area", func(): _send("EXPLORE")))
	_exploration_grid.add_child(_make_action_card("Rest", "Recover HP & Qi", func(): _send("REST")))
	_exploration_grid.add_child(_make_action_card("Travel", "Move to another area", func(): _open_travel_popup()))
	_exploration_grid.add_child(_make_action_card("Gather Herbs", "Harvest local herbs", func(): _send("GATHER"), _has_gathering(), "No herbs grow here."))
	_exploration_grid.add_child(_make_action_card("World Map", "Show your location", Callable(self, "_open_world_map_popup"), _has_map_position(), "This location has no map marker."))
	if _has_realm_active():
		_exploration_grid.add_child(_make_action_card("Continue Realm", "Press deeper", func(): _send("REALM_ADVANCE")))
		_exploration_grid.add_child(_make_action_card("Leave Realm", "Retreat to the surface", func(): _send("REALM_LEAVE")))
	else:
		_exploration_grid.add_child(_make_action_card("Secret Realm", "Descend into a hidden realm", func(): _send("ENTER_REALM"), _has_realm(), "No realm opens here."))
		var can_endless := bool(_last_state.get("campaign", {}).get("can_endless_realm", false))
		_exploration_grid.add_child(_make_action_card("Endless Road", "Descend into a generated realm", func(): _send("ENDLESS_REALM"), can_endless, "The endless road opens when the campaign is won or an endless run begins."))

	_support_grid.add_child(_make_action_card("Market", "Buy supplies and equipment", func(): _send("SHOP"), _has_available_shop(), "No market is available here."))
	_support_grid.add_child(_make_action_card("Masters", "Learn techniques", func(): _send("TRAINERS"), _has_available_trainer(), "No technique master is here."))
	_support_grid.add_child(_make_action_card("Sects", "Visit the local sect", func(): _open_sects_popup(), _has_available_sect(), "No sect holds ground here."))
	_support_grid.add_child(_make_action_card("Refine Pills", "Refine herbs into pills", func(): _open_refine_popup()))
	_support_grid.add_child(_make_action_card("Codex", "Realms, sects, and faction arcs", func(): _send("CODEX")))
	_support_grid.add_child(_make_action_card("Talents", "View and upgrade your talents", func(): _send("TALENTS")))
	_support_grid.add_child(_make_action_card("Dao", "View and awaken the Dao", func(): _send("DAO_VIEW")))
	_support_grid.add_child(_make_action_card("Tournament", "Enter the sect tournament", func(): _send("TOURNAMENT"), _has_tournament(), "No tournament is held here."))
	_support_grid.add_child(_make_action_card("Legacy", "Spend Ancestral Memory across runs", func(): _send("UNLOCK_TREE")))
	var can_retire := bool(player.get("can_retire", false))
	_support_grid.add_child(_make_action_card("Ascend", "Retire this life and bank your legacy", func(): _send("RETIRE_ASSENT"), can_retire, "Reach the Divine Transformation essence realm to ascend."))


func _make_action_card(title: String, subtitle: String, cb: Callable, enabled: bool = true, locked_reason: String = "") -> Button:
	var button := Button.new()
	button.disabled = not enabled
	button.tooltip_text = locked_reason if locked_reason != "" else subtitle
	button.custom_minimum_size = Vector2(0, 54)
	button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	button.focus_mode = Control.FOCUS_NONE
	# Card menu: warm raised ground, gold left accent when available, flat
	# muted ground with the lock reason stated when not.
	if enabled:
		var normal := _make_button_style(COLOR_PANEL_RAISED, COLOR_BORDER)
		normal.border_width_left = 3
		normal.border_color = COLOR_ANTIQUE_GOLD
		button.add_theme_stylebox_override("normal", normal)
		var hover := _make_button_style(COLOR_PANEL_RAISED, COLOR_BORDER_STRONG)
		hover.border_width_left = 3
		button.add_theme_stylebox_override("hover", hover)
		var pressed := _make_button_style(COLOR_SECONDARY_BACKGROUND, COLOR_BORDER_STRONG)
		pressed.border_width_left = 3
		button.add_theme_stylebox_override("pressed", pressed)
	else:
		var disabled := _make_button_style(COLOR_SECONDARY_BACKGROUND, COLOR_BORDER)
		disabled.border_width_left = 3
		disabled.border_color = Color("3A3225")
		button.add_theme_stylebox_override("normal", disabled)
		button.add_theme_stylebox_override("hover", disabled)
		button.add_theme_stylebox_override("pressed", disabled)
		button.add_theme_stylebox_override("disabled", disabled)
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
		sub_text = locked_reason
		sub_color = COLOR_SECONDARY_TEXT
	var sub_label := _make_label(sub_text, 11, sub_color)
	sub_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(sub_label)
	return button


func _focus_tab(index: int) -> void:
	_open_overlay(index)


# --- Styled dialogs (replacements for PopupMenu lists) ----------------------

## Open a centered styled dialog. Returns {panel, content}; track it in
## _dialog. Any action that resolves the session refreshes state, which is
## allowed to leave the dialog open (lists re-populate only when re-opened).
func _open_dialog(title: String, min_size: Vector2 = Vector2(560, 0)) -> Dictionary:
	_close_dialog()
	_dialog = {}
	var layer := Control.new()
	layer.set_anchors_preset(Control.PRESET_FULL_RECT)
	layer.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(layer)

	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.6)
	dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	dim.mouse_filter = Control.MOUSE_FILTER_STOP
	dim.gui_input.connect(_on_dialog_dim_input)
	layer.add_child(dim)

	# Same geometry as the tab overlay: an anchored band of the window. A dialog
	# therefore can never outgrow the screen (the old center-grow panels let
	# long content push their own header off the top) and matches the tabs
	# visually - one dialog language across the whole game.
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", _make_popup_style())
	panel.anchor_left = 0.18
	panel.anchor_right = 0.82
	panel.anchor_top = 0.07
	panel.anchor_bottom = 0.93
	panel.custom_minimum_size = min_size
	panel.grow_horizontal = Control.GROW_DIRECTION_BOTH
	panel.grow_vertical = Control.GROW_DIRECTION_BOTH
	layer.add_child(panel)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 10)
	panel.add_child(box)

	var header := HBoxContainer.new()
	box.add_child(header)
	var title_label := _make_label(title.to_upper(), 20, COLOR_TITLE_GOLD, true)
	header.add_child(title_label)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(spacer)
	header.add_child(_make_button("X", func(): _close_dialog(), "Close."))

	var rule := ColorRect.new()
	rule.color = COLOR_BORDER
	rule.custom_minimum_size = Vector2(0, 1)
	box.add_child(rule)

	var scroll := ScrollContainer.new()
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	# Deliberately no minimum height: the panel's cap must always win over
	# content pressure, and this body absorbs whatever room remains.
	box.add_child(scroll)

	var content := VBoxContainer.new()
	content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	content.add_theme_constant_override("separation", 8)
	scroll.add_child(content)

	_dialog = {"layer": layer, "panel": panel, "content": content, "title": title}
	return _dialog


func _close_dialog() -> void:
	if _dialog.is_empty():
		return
	var layer: Control = _dialog.get("layer", null)
	if layer != null:
		layer.queue_free()
	_dialog = {}


func _on_dialog_dim_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_close_dialog()


## One selectable row inside a dialog: title line, meta (price / state),
## optional description, disabled state with reason. index routes back to the
## caller's pick handler.
## A full-card clickable row. Buttons cannot size themselves to their content
## (children never raise a Button's minimum), so rich rows use a PanelContainer
## whose minimum IS the content's minimum; the click arrives via gui_input.
func _make_clickable_card(body: Control, disabled: bool, ground: Color, cb: Callable, locked_note: String = "") -> PanelContainer:
	var card := PanelContainer.new()
	card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	card.mouse_filter = Control.MOUSE_FILTER_STOP if not disabled else Control.MOUSE_FILTER_IGNORE
	card.tooltip_text = locked_note if disabled else ""
	var style := _make_button_style(ground, COLOR_BORDER if not disabled else Color("33291c"))
	card.add_theme_stylebox_override("panel", style)
	if not disabled:
		var hover := _make_button_style(COLOR_PANEL_RAISED, COLOR_ANTIQUE_GOLD)
		card.mouse_entered.connect(func(): card.add_theme_stylebox_override("panel", hover))
		card.mouse_exited.connect(func(): card.add_theme_stylebox_override("panel", style))
		card.gui_input.connect(func(event: InputEvent):
			if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
				card.add_theme_stylebox_override("panel", style)
				cb.call()
		)
	card.add_child(body)
	return card


func _add_dialog_row(title: String, meta: String, desc: String, disabled: bool, note: String, index: int, pick_cb: Callable) -> void:
	if _dialog.is_empty():
		return
	var content: VBoxContainer = _dialog["content"]
	var margin := MarginContainer.new()
	margin.add_theme_constant_override("margin_left", 12)
	margin.add_theme_constant_override("margin_top", 8)
	margin.add_theme_constant_override("margin_right", 12)
	margin.add_theme_constant_override("margin_bottom", 8)
	var card := _make_clickable_card(
		margin, disabled,
		COLOR_PANEL_SOFT if not disabled else COLOR_SECONDARY_BACKGROUND,
		pick_cb.bind(index) if not disabled else Callable(),
		note if disabled else "")
	content.add_child(card)

	var v := VBoxContainer.new()
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_theme_constant_override("separation", 3)
	margin.add_child(v)

	var head := HBoxContainer.new()
	head.mouse_filter = Control.MOUSE_FILTER_IGNORE
	head.add_theme_constant_override("separation", 10)
	v.add_child(head)
	var title_label := _make_label(title, 15, COLOR_PRIMARY_TEXT if not disabled else COLOR_MUTED)
	title_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	head.add_child(title_label)
	var meta_spacer := Control.new()
	meta_spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	meta_spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	head.add_child(meta_spacer)
	if meta != "":
		var meta_label := _make_label(meta, 13, COLOR_ANTIQUE_GOLD if not disabled else COLOR_MUTED)
		meta_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		head.add_child(meta_label)

	if desc != "":
		var desc_label := _make_label(desc, 12, COLOR_SECONDARY_TEXT)
		desc_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		desc_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(desc_label)
	if disabled and note != "":
		var note_label := _make_label(note, 12, COLOR_WARNING)
		note_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
		v.add_child(note_label)



## A quiet section caption between dialog groups.
func _add_dialog_caption(text: String) -> void:
	if _dialog.is_empty():
		return
	var content: VBoxContainer = _dialog["content"]
	content.add_child(_make_label(text.to_upper(), 12, COLOR_MUTED))


func _add_dialog_empty(text: String) -> void:
	if _dialog.is_empty():
		return
	var content: VBoxContainer = _dialog["content"]
	var label := _make_label(text, 13, COLOR_MUTED)
	label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	content.add_child(label)


func _add_dialog_footer(text: String, color: Color = COLOR_SECONDARY_TEXT) -> void:
	if _dialog.is_empty():
		return
	var content: VBoxContainer = _dialog["content"]
	content.add_child(_make_label(text, 13, color))


func _open_settings() -> void:
	_open_dialog("Settings")
	_add_dialog_caption("Identity")
	_add_dialog_row("Name & Portrait", "", "Choose what the world calls you, and the face it knows.", false, "", 4, _on_settings_pick)
	_add_dialog_caption("Session")
	_add_dialog_row("New Game", "", "Abandon this life and roll a new one.", false, "", 0, _on_settings_pick)
	_add_dialog_row("Save Game", "slot: default", "Record this life.", false, "", 1, _on_settings_pick)
	_add_dialog_row("Load Game", "slot: default", "Restore a saved life.", false, "", 2, _on_settings_pick)
	_add_dialog_caption("Application")
	_add_dialog_row("Quit", "", "Leave the world.", false, "", 3, _on_settings_pick)


func _on_settings_pick(index: int) -> void:
	if index == 4:
		# Replacing the dialog, not closing back to the game.
		_close_dialog()
		_open_identity()
		return
	match index:
		0:
			_start_new_game()
		1:
			api.save_game("default")
		2:
			api.load_game("default")
		3:
			get_tree().quit()
	_close_dialog()


# --- Identity (name + portrait) ---------------------------------------------


## The name the engine holds for the living cultivator ("" before the first
## state snapshot arrives).
func _live_player_name() -> String:
	var player: Dictionary = _last_state.get("player", {})
	if player.is_empty():
		return ""
	return str(player.get("name", ""))


## The name-and-avatar picker; opened from the top-rail identity cluster, the
## dossier portrait, and the Settings dialog rows.
func _open_identity() -> void:
	_open_dialog("Identity", Vector2(760, 0))
	var editor := IdentityEditor.new()
	# Prefer the living cultivator's name over the stored one: a loaded save may
	# have been started under a different name.
	editor.initial_name = _live_player_name()
	editor.committed.connect(_on_identity_committed)
	editor.cancelled.connect(func(): _close_dialog())
	var content: VBoxContainer = _dialog["content"]
	content.add_child(editor)


func _on_identity_committed(new_name: String, _avatar_id: String) -> void:
	_close_dialog()
	_apply_identity_art(new_name)
	if new_name != _live_player_name():
		# The engine owns the name: it is written into the save and into prose.
		api.send_action({"action": "RENAME", "player_name": new_name})
		_set_situation("Identity", "From this day the world will know you as [color=#E4C87F]%s[/color]." % new_name)


## Point the top-rail portrait and the dossier portrait at the chosen avatar,
## falling back to a monogram while the art cannot be loaded.
func _apply_identity_art(player_name: String) -> void:
	var texture := Profile.current_texture()
	_apply_portrait(_top_avatar, texture)
	_apply_portrait(_portrait_texture, texture)
	if _portrait_initial != null:
		_portrait_initial.visible = texture == null
		_portrait_initial.text = player_name.substr(0, 1).to_upper() if player_name.length() > 0 else "?"


func _apply_portrait(target: TextureRect, texture: Texture2D) -> void:
	if target == null:
		return
	target.texture = texture
	target.visible = texture != null


func _open_travel_popup() -> void:
	_travel_ids = []
	_open_dialog("Travel", Vector2(600, 0))
	for dest in _destinations:
		if typeof(dest) != TYPE_DICTIONARY:
			continue
		var dest_id := str(dest.get("id", ""))
		if dest_id == "":
			continue
		var reachable := bool(dest.get("reachable", true))
		var title := str(dest.get("display_name", dest_id))
		var danger := str(dest.get("danger", "?"))
		_add_dialog_row(title, "Danger: %s" % danger, str(dest.get("description", "")), not reachable, str(dest.get("reason", "You cannot travel there yet.")), _travel_ids.size(), _on_travel_pick)
		_travel_ids.append(dest_id)
	if _travel_ids.is_empty():
		_add_dialog_empty("Nowhere to travel from here.")
	_close_dialog_footer()


func _close_dialog_footer() -> void:
	if _dialog.is_empty():
		return
	var content: VBoxContainer = _dialog["content"]
	var footer := HBoxContainer.new()
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	footer.add_child(spacer)
	footer.add_child(_make_button("Close", func(): _close_dialog(), "Close this panel."))
	content.add_child(footer)


func _on_travel_pick(index: int) -> void:
	if index >= 0 and index < _travel_ids.size() and str(_travel_ids[index]) != "":
		api.travel(str(_travel_ids[index]))
	_close_dialog()


func _open_world_map_popup() -> void:
	var location: Dictionary = _last_state.get("location", {})
	var position: Dictionary = location.get("map_position", {})
	if position.is_empty():
		_set_situation("World Map", "No map marker is available for this location.")
		return

	_open_dialog("World Map", Vector2(1010, 0))
	var content: VBoxContainer = _dialog["content"]

	var map_holder := Control.new()
	# Fill the dialog body's remaining space (never a fixed 640px floor: that
	# overflowed the dialog band). The content-rect math letterboxes the image.
	map_holder.custom_minimum_size = Vector2(0, 320)
	map_holder.size_flags_vertical = Control.SIZE_EXPAND_FILL
	map_holder.clip_contents = true
	content.add_child(map_holder)

	var map_texture := TextureRect.new()
	map_texture.set_anchors_preset(Control.PRESET_FULL_RECT)
	map_texture.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	map_texture.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	map_texture.texture = _load_texture(WORLD_MAP_PATH)
	map_texture.mouse_filter = Control.MOUSE_FILTER_IGNORE
	map_holder.add_child(map_texture)

	var marker := Label.new()
	marker.text = "\u25c6"
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

	_close_dialog_footer()
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
	_open_dialog("Equip Item", Vector2(600, 0))
	for item in _last_state.get("inventory_items", []):
		if typeof(item) != TYPE_DICTIONARY or str(item.get("type", "")) != "equipment":
			continue
		var item_id := str(item.get("item_id", ""))
		for slot in item.get("valid_slots", []):
			var target_slot := str(slot)
			if item_id == "" or target_slot == "":
				continue
			var title := str(item.get("name", item_id))
			_add_dialog_row(title, "to %s" % _slot_label(target_slot), str(item.get("description", "")), false, "", _equip_choices.size(), _on_equip_pick)
			_equip_choices.append({"item_id": item_id, "slot": target_slot})
	if _equip_choices.is_empty():
		_add_dialog_empty("No equippable items in inventory.")
	_close_dialog_footer()


func _on_equip_pick(index: int) -> void:
	if index < 0 or index >= _equip_choices.size():
		return
	var choice: Dictionary = _equip_choices[index]
	api.send_action({"action": "EQUIP_ITEM", "item_id": choice.get("item_id", ""), "slot": choice.get("slot", "")})
	_close_dialog()


func _open_use_popup() -> void:
	_use_choices = []
	_open_dialog("Use Item", Vector2(600, 0))
	for item in _last_state.get("inventory_items", []):
		if typeof(item) != TYPE_DICTIONARY or not bool(item.get("usable", false)):
			continue
		var item_id := str(item.get("item_id", ""))
		if item_id == "":
			continue
		var title := "%s  x%s" % [str(item.get("name", item_id)), _format_quantity(item.get("count", 1))]
		_add_dialog_row(title, "", str(item.get("description", "")), false, "", _use_choices.size(), _on_use_pick)
		_use_choices.append({"item_id": item_id})
	if _use_choices.is_empty():
		_add_dialog_empty("No usable items in inventory.")
	_close_dialog_footer()


func _on_use_pick(index: int) -> void:
	if index < 0 or index >= _use_choices.size():
		return
	var choice: Dictionary = _use_choices[index]
	api.send_action({"action": "USE_ITEM", "item_id": choice.get("item_id", "")})
	_close_dialog()


func _open_unequip_popup() -> void:
	_unequip_choices = []
	_open_dialog("Unequip", Vector2(600, 0))
	var player: Dictionary = _last_state.get("player", {})
	var equipment: Dictionary = player.get("equipment", {})
	var details: Dictionary = player.get("equipment_details", {})
	for slot in equipment.keys():
		var raw_item_id = equipment.get(slot)
		if raw_item_id == null or str(raw_item_id) == "":
			continue
		var item_id := str(raw_item_id)
		var equipped: Dictionary = details.get(slot, {})
		var title := "%s: %s" % [_slot_label(str(slot)), equipped.get("display_name", item_id)]
		_add_dialog_row(title, "", str(equipped.get("description", "")), false, "", _unequip_choices.size(), _on_unequip_pick)
		_unequip_choices.append({"slot": str(slot)})
	if _unequip_choices.is_empty():
		_add_dialog_empty("No equipment is currently worn.")
	_close_dialog_footer()


func _on_unequip_pick(index: int) -> void:
	if index < 0 or index >= _unequip_choices.size():
		return
	var choice: Dictionary = _unequip_choices[index]
	api.send_action({"action": "UNEQUIP_ITEM", "slot": choice.get("slot", "")})
	_close_dialog()


func _show_shop(result: Dictionary) -> void:
	_shop_choices = []
	var shop: Dictionary = result.get("shop", {})
	var shop_id := str(shop.get("id", ""))
	var shop_name := str(shop.get("display_name", "Market"))
	_open_dialog(shop_name, Vector2(640, 0))
	if str(shop.get("description", "")) != "":
		_add_dialog_footer(str(shop.get("description", "")))
	for item in result.get("stock", []):
		if typeof(item) != TYPE_DICTIONARY:
			continue
		var item_id := str(item.get("item_id", ""))
		if item_id == "":
			continue
		var title := str(item.get("name", item_id))
		_add_dialog_row(title, _format_price(item.get("price", {})), str(item.get("description", "")), false, "", _shop_choices.size(), _on_shop_pick)
		_shop_choices.append({"shop_id": shop_id, "item_id": item_id})
	if _shop_choices.is_empty():
		_add_dialog_empty("No stock available.")
	_close_dialog_footer()
	_set_situation(shop_name, str(shop.get("description", "Available wares are listed.")))


func _on_shop_pick(index: int) -> void:
	if index < 0 or index >= _shop_choices.size():
		return
	var choice: Dictionary = _shop_choices[index]
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


func _has_available_sect() -> bool:
	return not _last_state.get("sects", []).is_empty()


func _has_gathering() -> bool:
	return bool(_last_state.get("gathering_available", false))


func _has_realm() -> bool:
	return bool(_last_state.get("realm_available", false))


func _has_realm_active() -> bool:
	var realm = _last_state.get("realm")
	return typeof(realm) == TYPE_DICTIONARY and not realm.is_empty()


func _has_tournament() -> bool:
	return bool(_last_state.get("tournament_available", false))


func _open_refine_popup() -> void:
	_refine_ids = []
	_open_dialog("Refine Pills", Vector2(780, 0))
	var content: VBoxContainer = _dialog["content"]

	# A recipe browser, not a wall of buttons: brewable first with have/need
	# counts, then what still blocks the rest. The backend stays the authority;
	# these counts are presentation only.
	var counts := _inventory_counts()
	var brewable: Array = []
	var locked: Array = []
	for recipe in _last_state.get("refining_recipes", []):
		if typeof(recipe) != TYPE_DICTIONARY:
			continue
		var reason := _recipe_lock_reason(recipe, counts)
		if reason == "":
			brewable.append(recipe)
		else:
			locked.append([recipe, reason])

	# The dialog body already scrolls; the recipe list lives directly in it.
	var list := VBoxContainer.new()
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	list.add_theme_constant_override("separation", 6)
	content.add_child(list)

	list.add_child(_make_refine_section("BREWABLE NOW · %d" % brewable.size()))
	for recipe in brewable:
		list.add_child(_make_refine_row(recipe, ""))
	if brewable.is_empty():
		list.add_child(_make_refine_empty("Nothing can be brewed with the herbs you carry. Gather more."))
	list.add_child(_make_refine_section("STILL OUT OF REACH · %d" % locked.size()))
	for entry in locked:
		list.add_child(_make_refine_row(entry[0], entry[1]))
	if locked.is_empty():
		list.add_child(_make_refine_empty("Every known recipe is within your grasp."))

	_close_dialog_footer()


func _inventory_counts() -> Dictionary:
	var state: Dictionary = _last_state
	var player: Dictionary = state.get("player", {})
	var inv = player.get("inventory", {})
	var counts := {}
	if typeof(inv) == TYPE_DICTIONARY:
		for item_id in inv.keys():
			counts[str(item_id)] = int(inv[item_id])
	elif typeof(inv) == TYPE_ARRAY:
		for entry in inv:
			if typeof(entry) == TYPE_DICTIONARY:
				counts[str(entry.get("item_id", entry.get("id", "")))] = int(entry.get("count", entry.get("quantity", 0)))
	# Equipped gear no longer sits in inventory but the engine still reports it
	# separately; refineries only consume loose materials either way.
	return counts


func _recipe_lock_reason(recipe: Dictionary, counts: Dictionary) -> String:
	var reasons: Array[String] = []
	# The backend's `available` flag is the realm gate (null realms never block);
	# `realm_met` is not part of this payload, so never gate on it here.
	if not bool(recipe.get("available", true)):
		var breq = recipe.get("minimum_body_realm")
		var ereq = recipe.get("minimum_essence_realm")
		if breq != null:
			reasons.append("Requires %s body cultivation" % _humanize_key(str(breq)))
		if ereq != null:
			reasons.append("Requires %s essence" % _humanize_key(str(ereq)))
		if reasons.is_empty():
			reasons.append("Your cultivation is not deep enough")
	var missing: Array[String] = []
	var inputs: Dictionary = recipe.get("inputs", {})
	for item_id in inputs.keys():
		var need := int(inputs[item_id])
		var have := int(counts.get(str(item_id), 0))
		if have < need:
			missing.append("%d/%d %s" % [have, need, _title_from_id(str(item_id))])
	if not missing.is_empty():
		reasons.append("Needs %s" % ", ".join(missing))
	return "; ".join(reasons)


func _make_refine_section(caption: String) -> Control:
	var label := _make_label(caption, 12, COLOR_MUTED)
	return label


func _make_refine_empty(text: String) -> Control:
	return _make_label(text, 13, COLOR_MUTED)


func _make_refine_row(recipe: Dictionary, lock_reason: String) -> Control:
	var index := _refine_ids.size()
	_refine_ids.append(str(recipe.get("id", "")))
	var disabled := lock_reason != ""

	var margin := MarginContainer.new()
	margin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	margin.add_theme_constant_override("margin_left", 12)
	margin.add_theme_constant_override("margin_top", 8)
	margin.add_theme_constant_override("margin_right", 12)
	margin.add_theme_constant_override("margin_bottom", 8)
	var button := _make_clickable_card(
		margin, disabled,
		COLOR_PANEL_SOFT if not disabled else COLOR_SECONDARY_BACKGROUND,
		_on_refine_pick.bind(index) if not disabled else Callable(),
		lock_reason)

	var v := VBoxContainer.new()
	v.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_theme_constant_override("separation", 3)
	margin.add_child(v)

	var head := HBoxContainer.new()
	head.mouse_filter = Control.MOUSE_FILTER_IGNORE
	v.add_child(head)
	head.add_child(_make_label(str(recipe.get("display_name", recipe.get("id", ""))), 15, COLOR_PRIMARY_TEXT))
	var head_spacer := Control.new()
	head_spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	head_spacer.mouse_filter = Control.MOUSE_FILTER_IGNORE
	head.add_child(head_spacer)
	head.add_child(_make_label("BREWABLE" if not disabled else "LOCKED", 11, COLOR_SUCCESS if not disabled else COLOR_MUTED))

	var desc := str(recipe.get("description", ""))
	if desc != "":
		v.add_child(_make_label(desc, 12, COLOR_SECONDARY_TEXT))

	var parts: Array[String] = []
	var counts := _inventory_counts()
	var inputs: Dictionary = recipe.get("inputs", {})
	for item_id in inputs.keys():
		var need := int(inputs[item_id])
		var have := int(counts.get(str(item_id), 0))
		var tag := "%d× %s" % [need, _title_from_id(str(item_id))]
		if have < need:
			tag += " (have %d)" % have
		parts.append("[color=%s]%s[/color]" % ["#7ea75a" if have >= need else "#d24a43", tag])
	var output: Dictionary = recipe.get("output", {})
	var out_text := ""
	if not output.is_empty():
		out_text = "  →  %d× %s" % [int(output.get("count", 1)), _title_from_id(str(output.get("item_id", "")))]
	parts.append("[color=#a08f74]%s[/color]" % out_text.strip_edges())
	var formula := RichTextLabel.new()
	formula.bbcode_enabled = true
	formula.fit_content = true
	formula.mouse_filter = Control.MOUSE_FILTER_IGNORE
	formula.add_theme_color_override("default_color", COLOR_SECONDARY_TEXT)
	formula.scroll_active = false
	formula.append_text("  ·  ".join(parts))
	v.add_child(formula)

	if disabled:
		v.add_child(_make_label(lock_reason, 12, COLOR_DANGER))
	return button


func _on_refine_pick(index: int) -> void:
	if index >= 0 and index < _refine_ids.size():
		api.send_action({"action": "REFINE", "recipe_id": _refine_ids[index]})
	_close_dialog()


func _show_dao_view(result: Dictionary) -> void:
	_dao_ids = []
	var current_id := str(result.get("current_dao_id", ""))
	_open_dialog("Dao", Vector2(600, 0))
	_add_dialog_footer("Current Dao: %s - choose another to awaken to it." % str(result.get("current_dao_name", "")))
	for dao in result.get("daos", []):
		if typeof(dao) != TYPE_DICTIONARY:
			continue
		var dao_id := str(dao.get("id", ""))
		var is_current := dao_id == current_id
		_add_dialog_row(str(dao.get("display_name", dao_id)), "current" if is_current else "", str(dao.get("description", "")), is_current, "Already awakened to this Dao.", _dao_ids.size(), _on_dao_pick)
		_dao_ids.append(dao_id)
	_close_dialog_footer()
	_set_situation("Dao", "Current Dao: %s - choose another to awaken to it." % str(result.get("current_dao_name", "")))


func _on_dao_pick(index: int) -> void:
	if index >= 0 and index < _dao_ids.size():
		api.send_action({"action": "DAO_AWAKEN", "dao_id": _dao_ids[index]})
	_close_dialog()


func _show_talents(result: Dictionary) -> void:
	_talent_choices = []
	var martial: Dictionary = result.get("martial_talent", {})
	var body: Dictionary = result.get("body_talent", {})
	_open_dialog("Talents", Vector2(620, 0))
	_add_dialog_footer("Martial: %s   -   Body: %s" % [str(martial.get("display_name", "?")), str(body.get("display_name", "?"))])

	_add_dialog_caption("Martial upgrades")
	for option in result.get("martial_upgrades", []):
		if typeof(option) == TYPE_DICTIONARY:
			_add_talent_upgrade_row(option, "Martial")

	_add_dialog_caption("Body upgrades")
	for option in result.get("body_upgrades", []):
		if typeof(option) == TYPE_DICTIONARY:
			_add_talent_upgrade_row(option, "Body")

	if _talent_choices.is_empty():
		_add_dialog_empty("No upgrades are offered right now.")
	_close_dialog_footer()
	_set_situation("Talents", "Martial: %s  -  Body: %s" % [str(martial.get("display_name", "?")), str(body.get("display_name", "?"))])


func _add_talent_upgrade_row(option: Dictionary, track: String) -> void:
	var target_id := str(option.get("target_id", ""))
	if target_id == "":
		return
	var affordable := bool(option.get("affordable", true))
	var cost: Dictionary = option.get("cost", {})
	var title := str(option.get("target_name", target_id))
	_add_dialog_row(title, _format_price(cost), "Advance the %s talent." % track.to_lower(), not affordable, "Need resources for this upgrade.", _talent_choices.size(), _on_talent_pick)
	_talent_choices.append({"track": track.to_lower(), "target_id": target_id})


func _on_talent_pick(index: int) -> void:
	if index < 0 or index >= _talent_choices.size():
		return
	var choice: Dictionary = _talent_choices[index]
	api.send_action({"action": "UPGRADE_TALENT", "track": choice.get("track", ""), "target_id": choice.get("target_id", "")})
	_close_dialog()


func _has_usable_item() -> bool:
	for item in _last_state.get("inventory_items", []):
		if typeof(item) == TYPE_DICTIONARY and bool(item.get("usable", false)):
			return true
	return false


func _show_trainer(result: Dictionary) -> void:
	_trainer_choices = []
	var trainer: Dictionary = result.get("trainer", {})
	var trainer_id := str(trainer.get("id", ""))
	var trainer_name := str(trainer.get("display_name", "Technique Master"))
	_open_dialog(trainer_name, Vector2(640, 0))
	if str(trainer.get("description", "")) != "":
		_add_dialog_footer(str(trainer.get("description", "")))
	for technique in result.get("techniques", []):
		if typeof(technique) != TYPE_DICTIONARY:
			continue
		var skill_id := str(technique.get("skill_id", ""))
		if skill_id == "":
			continue
		var known := bool(technique.get("already_known", false))
		var affordable := bool(technique.get("affordable", true))
		var note := ""
		if known:
			note = "Already known."
		elif not affordable:
			note = "Not enough funds."
		_add_dialog_row(str(technique.get("name", skill_id)), _format_price(technique.get("price", {})), str(technique.get("description", "")), known or not affordable, note, _trainer_choices.size(), _on_trainer_pick)
		_trainer_choices.append({"trainer_id": trainer_id, "skill_id": skill_id})
	if _trainer_choices.is_empty():
		_add_dialog_empty("No techniques on offer.")
	_close_dialog_footer()
	_set_situation(trainer_name, str(trainer.get("description", "Techniques available to learn are listed.")))


func _on_trainer_pick(index: int) -> void:
	if index < 0 or index >= _trainer_choices.size():
		return
	var choice: Dictionary = _trainer_choices[index]
	api.send_action({"action": "LEARN_SKILL", "trainer_id": choice.get("trainer_id", ""), "skill_id": choice.get("skill_id", "")})


func _show_sect(result: Dictionary) -> void:
	_sect_choices = []
	var sect: Dictionary = result.get("sect", {})
	_current_sect_id = str(sect.get("id", ""))
	var tier := int(sect.get("tier", 0))
	var join: Dictionary = sect.get("join_status", {})
	var join_label := "Visiting"
	if bool(join.get("already_joined", false)):
		join_label = "Joined"
	elif bool(join.get("allowed", false)):
		join_label = "May join"
	var situation := "%s (Tier %d - %s)" % [str(sect.get("display_name", "Sect")), tier, join_label]
	_set_situation(situation, str(sect.get("description", "")))
	var techniques: Array = sect.get("techniques", [])
	if techniques.is_empty():
		_append("The hall offers no techniques at this tier.")


func _open_sects_popup() -> void:
	_sect_choices = []
	var sects: Array = _last_state.get("sects", [])
	if sects.is_empty():
		return
	_open_dialog("Sects", Vector2(620, 0))
	var labels: Array[String] = []
	for sect in sects:
		if typeof(sect) != TYPE_DICTIONARY:
			continue
		var sect_id := str(sect.get("id", ""))
		if sect_id == "":
			continue
		var title := str(sect.get("display_name", sect_id))
		_add_dialog_row(title, "Tier %s" % str(sect.get("tier", "?")), "Visit the sect.", false, "", _sect_choices.size(), _on_sect_pick)
		labels.append(title)
		_sect_choices.append({"kind": "visit", "sect_id": sect_id})
	var joined: Dictionary = _last_state.get("player", {}).get("joined_sect", {})
	if not joined.is_empty() and str(joined.get("sect_id", "")) != "":
		_add_dialog_caption("Your sect's teachings")
		for technique in joined.get("techniques", []):
			if typeof(technique) != TYPE_DICTIONARY:
				continue
			var skill_id := str(technique.get("skill_id", ""))
			if skill_id == "":
				continue
			var known := bool(technique.get("already_known", false))
			var affordable := bool(technique.get("affordable", true))
			var locked := bool(technique.get("path_locked", false))
			var note := ""
			if known:
				note = "Already known."
			elif locked:
				note = "Locked to another path."
			elif not affordable:
				note = "Not enough funds."
			_add_dialog_row("Learn %s" % str(technique.get("name", skill_id)), _format_price(technique.get("price", {})), str(technique.get("description", "")), known or locked or not affordable, note, _sect_choices.size(), _on_sect_pick)
			_sect_choices.append({"kind": "learn", "sect_id": str(joined.get("sect_id", "")), "skill_id": skill_id})
	_close_dialog_footer()
	if labels.is_empty():
		_set_situation("Sects", "No sect holds ground here.")


func _on_sect_pick(index: int) -> void:
	if index < 0 or index >= _sect_choices.size():
		return
	var choice: Dictionary = _sect_choices[index]
	if str(choice.get("kind", "")) == "learn":
		api.send_action({"action": "LEARN_SKILL", "sect_id": choice.get("sect_id", ""), "skill_id": choice.get("skill_id", "")})
	else:
		api.send_action({"action": "SECTS", "sect_id": choice.get("sect_id", "")})


func _open_codex_popup(result: Dictionary) -> void:
	_open_dialog("Codex", Vector2(640, 0))
	var content: VBoxContainer = _dialog["content"]
	# The codex lists the whole world; give it room to scroll.
	var scroll := ScrollContainer.new()
	scroll.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.custom_minimum_size = Vector2(0, 420)
	content.add_child(scroll)
	var inner := VBoxContainer.new()
	inner.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	inner.add_theme_constant_override("separation", 8)
	scroll.add_child(inner)
	_dialog["content"] = inner

	var max_tier := int(result.get("max_story_tier", 0))
	_add_dialog_caption("Your reach -- story tier %d" % max_tier)

	_add_dialog_caption("Secret Realms")
	for realm in result.get("realms", []):
		if typeof(realm) != TYPE_DICTIONARY:
			continue
		var discovered := bool(realm.get("discovered", false))
		var tier := int(realm.get("story_tier", 0))
		var meta := "Tier %d - %s" % [tier, str(realm.get("location_name", ""))]
		var note := ""
		if not discovered:
			note = "Undiscovered -- travel further along the story."
		_add_dialog_row(str(realm.get("display_name", "")), meta, str(realm.get("description", "")), true, note, -1, Callable())

	_add_dialog_caption("Sects & Technique Halls")
	for sect in result.get("sects", []):
		if typeof(sect) != TYPE_DICTIONARY:
			continue
		var joined := bool(sect.get("joined", false))
		var meta := "Tier %d - %d/%d techniques" % [int(sect.get("tier", 0)), int(sect.get("techniques_known", 0)), int(sect.get("technique_count", 0))]
		if joined:
			meta += " - Joined"
		_add_dialog_row(str(sect.get("display_name", "")), meta, str(sect.get("description", "")), true, "Visit the sect where it holds ground to learn.", -1, Callable())

	_add_dialog_caption("Faction Arcs")
	for arc in result.get("arcs", []):
		if typeof(arc) != TYPE_DICTIONARY:
			continue
		_add_dialog_empty(str(arc.get("title", "")))
		for quest in arc.get("quests", []):
			if typeof(quest) != TYPE_DICTIONARY:
				continue
			var status := str(quest.get("status", "locked"))
			_add_dialog_row(str(quest.get("title", "")), status, "", true, "", -1, Callable())

	if result.get("realms", []).is_empty() and result.get("sects", []).is_empty() and result.get("arcs", []).is_empty():
		_add_dialog_empty("The codex is empty.")

	_dialog["content"] = content
	_close_dialog_footer()


func _slot_label(slot: String) -> String:
	return UIKit.title_from_id(slot)


func _build_overlay() -> void:
	_overlay = Control.new()
	_overlay.set_anchors_preset(Control.PRESET_FULL_RECT)
	_overlay.visible = false
	_overlay.mouse_filter = Control.MOUSE_FILTER_STOP
	add_child(_overlay)

	_overlay_dim = ColorRect.new()
	_overlay_dim.color = Color(0, 0, 0, 0.62)
	_overlay_dim.set_anchors_preset(Control.PRESET_FULL_RECT)
	_overlay_dim.mouse_filter = Control.MOUSE_FILTER_STOP
	_overlay_dim.gui_input.connect(_on_overlay_dim_input)
	_overlay.add_child(_overlay_dim)

	_overlay_panel = PanelContainer.new()
	_overlay_panel.add_theme_stylebox_override("panel", _make_popup_style())
	_overlay_panel.anchor_left = 0.12
	_overlay_panel.anchor_right = 0.88
	_overlay_panel.anchor_top = 0.06
	_overlay_panel.anchor_bottom = 0.94
	_overlay.add_child(_overlay_panel)

	var root := VBoxContainer.new()
	root.add_theme_constant_override("separation", 10)
	_overlay_panel.add_child(root)

	var header := HBoxContainer.new()
	root.add_child(header)
	_overlay_title = _make_label("INVENTORY", 24, COLOR_TITLE_GOLD, true)
	header.add_child(_overlay_title)

	# The dialog carries its own tab strip: the top-bar buttons sit behind the
	# dim layer, so switching tabs from inside the overlay is the only honest
	# interaction. Mirrors _update_tab_button_states() with the top strip.
	var strip := HBoxContainer.new()
	strip.add_theme_constant_override("separation", 6)
	strip.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	for i in TAB_TITLES.size():
		var tab_button := _make_button(TAB_TITLES[i], func(): _open_overlay(i), "Open the %s panel." % TAB_TITLES[i])
		tab_button.focus_mode = Control.FOCUS_NONE
		tab_button.custom_minimum_size = Vector2(0, 32)
		_overlay_tab_buttons.append(tab_button)
		strip.add_child(tab_button)
	header.add_child(strip)

	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	header.add_child(spacer)
	header.add_child(_make_button("X", func(): _close_overlay(), "Close this panel."))

	var rule := ColorRect.new()
	rule.color = COLOR_BORDER
	rule.custom_minimum_size = Vector2(0, 1)
	root.add_child(rule)

	_overlay_content = VBoxContainer.new()
	_overlay_content.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_overlay_content.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(_overlay_content)

	_inventory_panel = InventoryPanel.new()
	_inventory_panel.use_requested.connect(func(item_id: String): api.send_action({"action": "USE_ITEM", "item_id": item_id}))
	_inventory_panel.equip_requested.connect(_equip_from_card)
	_add_tab(_inventory_panel)

	_equipment_panel = EquipmentPanel.new()
	_add_tab(_equipment_panel)

	_journal_panel = JournalPanel.new()
	_add_tab(_journal_panel)

	_status_panel = StatusPanel.new()
	_add_tab(_status_panel)

	_techniques_panel = TechniquesPanel.new()
	_add_tab(_techniques_panel)

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
			button.add_theme_stylebox_override("normal", _make_button_style(Color("332A1A"), COLOR_TITLE_GOLD))
			button.add_theme_color_override("font_color", COLOR_TITLE_GOLD)
		else:
			button.add_theme_stylebox_override("normal", _make_button_style(COLOR_PANEL_SOFT, COLOR_BORDER))
			button.add_theme_color_override("font_color", COLOR_PRIMARY_TEXT)
	for i in _overlay_tab_buttons.size():
		var active := (i == _active_tab)
		var button: Button = _overlay_tab_buttons[i]
		if active:
			button.add_theme_stylebox_override("normal", _make_button_style(Color("332A1A"), COLOR_TITLE_GOLD))
			button.add_theme_color_override("font_color", COLOR_TITLE_GOLD)
		else:
			button.add_theme_stylebox_override("normal", _make_button_style(COLOR_PANEL_SOFT, COLOR_BORDER))
			button.add_theme_color_override("font_color", COLOR_PRIMARY_TEXT)


func _on_overlay_dim_input(event: InputEvent) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_close_overlay()


# --- Tab pages --------------------------------------------------------------

## Hand a finished panel to the overlay. Each panel lays out its own margins,
## header and scroll region, so a tab is one file with one writer.
func _add_tab(page: Control) -> void:
	_overlay_content.add_child(page)
	_tab_pages.append(page)


# --- Narrative panel ---------------------------------------------------------

func _build_narrative_panel(root: VBoxContainer) -> void:
	# Single narrative output panel (the event log was removed; prose is the
	# UI's only feed of what just happened).
	var narrative_panel := _make_panel()
	narrative_panel.size_flags_vertical = Control.SIZE_EXPAND_FILL
	root.add_child(narrative_panel)
	var narrative_box := VBoxContainer.new()
	narrative_box.size_flags_vertical = Control.SIZE_EXPAND_FILL
	narrative_box.add_theme_constant_override("separation", 6)
	narrative_panel.add_child(narrative_box)
	narrative_box.add_child(_make_label("CHRONICLE", 14, COLOR_ANTIQUE_GOLD))
	_narrative_text = RichTextLabel.new()
	_narrative_text.bbcode_enabled = true
	_narrative_text.fit_content = true
	_narrative_text.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_narrative_text.add_theme_color_override("default_color", COLOR_PRIMARY_TEXT)
	narrative_box.add_child(_narrative_text)
	_set_narrative("Your journey as a cultivator begins.")


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
	for grid in [_body_cultivation_grid, _essence_cultivation_grid, _exploration_grid, _support_grid]:
		if grid != null:
			_clear_row(grid)


func _clear_row(container: Container) -> void:
	UIKit.clear(container)


func _make_portrait_style() -> StyleBoxFlat:
	return UIKit.portrait_style()


func _make_chip(caption: String, value: String, color: Color) -> PanelContainer:
	return UIKit.chip(caption, value, color)


func _render_chips(location: Dictionary) -> void:
	_clear_row(_chips_row)
	var danger := str(location.get("danger", "Unknown"))
	_chips_row.add_child(_make_chip("DANGER", danger, Color(_danger_color(danger))))
	var qi_label := str(location.get("qi_density_label", location.get("qi_density", "?")))
	_chips_row.add_child(_make_chip("QI", qi_label, COLOR_QI))
	var resources: Array = location.get("resources", [])
	_chips_row.add_child(_make_chip("RESOURCES", _join_array(resources) if not resources.is_empty() else "None", COLOR_ANTIQUE_GOLD))


func _make_bar_group(caption: String, color: Color, background_color: Color) -> Dictionary:
	return UIKit.bar_group(caption, color, background_color)


func _make_panel(fill: Color = COLOR_PANEL, border: Color = COLOR_BORDER, border_width: int = 1) -> PanelContainer:
	return UIKit.panel(fill, border, border_width)


func _make_panel_style(fill: Color, border: Color = COLOR_BORDER, border_width: int = 1) -> StyleBoxFlat:
	return UIKit.panel_style(fill, border, border_width)


func _make_popup_style() -> StyleBoxFlat:
	return UIKit.popup_style()


func _make_label(text: String, size: int, color: Color, display: bool = false) -> Label:
	return UIKit.label(text, size, color, display)


func _make_button(text: String, cb: Callable, tooltip: String = "") -> Button:
	return UIKit.button(text, cb, tooltip)


func _make_button_style(fill: Color, border: Color) -> StyleBoxFlat:
	return UIKit.button_style(fill, border)


func _apply_bar_style(bar: ProgressBar, color: Color, background_color: Color) -> void:
	UIKit.apply_bar_style(bar, color, background_color)


# --- Networking glue -------------------------------------------------------

func _send(action_name: String) -> void:
	api.send_action({"action": action_name})


func _start_new_game() -> void:
	_showing_event_result = false
	api.new_game(Profile.player_name, null)


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
	_known_skills = player.get("skills", [])
	_cooldowns = state.get("cooldowns", {})

	# E.1-E.5: capture the living-world summary before rendering (the season
	# drives the top-bar chip in the same frame).
	_last_world_view = state.get("world", {})
	_render_top_bar(player)
	_render_character(player)
	_render_location(state.get("location", {}))
	_render_inventory(state)
	_render_equipment(player)
	_render_quests(state.get("quests", []))
	_render_status_summary(player)
	_render_techniques(player)
	_render_actions(player)
	_rebuild_combat_actions()
	# B.9: a pending encounter owns the action grid. Rebuilding the choices from
	# state (rather than from the one-shot action result) means a state refresh
	# can never wipe the menu out from under the player.
	var pending_encounter = state.get("encounter", null)
	if bool(state.get("in_encounter", false)) and typeof(pending_encounter) == TYPE_DICTIONARY and not pending_encounter.is_empty():
		_render_encounter_choices(pending_encounter)

	var in_combat := bool(state.get("in_combat", false))
	_set_combat_mode(in_combat)
	var enemy = state.get("enemy", null)
	if in_combat and enemy != null:
		_update_enemy(enemy)


func _render_top_bar(player: Dictionary) -> void:
	var player_name := str(player.get("name", "Unknown"))
	_name_label.text = player_name
	_apply_identity_art(player_name)
	var hp := int(player.get("hp", 0))
	var mhp := int(max(1, int(player.get("max_hp", 1))))
	var qi := int(player.get("qi", 0))
	var mqi := int(max(1, int(player.get("max_qi", 1))))
	_hp_bar.max_value = mhp
	_hp_bar.value = hp
	_hp_text.text = "%d / %d" % [hp, mhp]
	_qi_bar.max_value = mqi
	_qi_bar.value = qi
	_qi_text.text = "%d / %d" % [qi, mqi]
	var lifespan: Dictionary = player.get("lifespan", {})
	_year = int(lifespan.get("year", 0))
	_year_label.text = str(_year)
	# E.4: the living world's season drives yield/travel/odds.
	_season_label.text = str(_last_world_view.get("season", "Spring"))
	# Age at a glance; tints toward danger as the lifespan runs out.
	var age_years := float(lifespan.get("age_years", 0.0))
	var remaining := float(lifespan.get("remaining_years", 0.0))
	if bool(lifespan.get("immortal", false)):
		_age_label.text = "Immortal"
		_age_label.add_theme_color_override("font_color", COLOR_TITLE_GOLD)
	else:
		_age_label.text = "%d / %d" % [int(age_years), int(age_years + remaining)]
		var span := maxf(1.0, age_years + remaining)
		_age_label.add_theme_color_override(
			"font_color",
			COLOR_DANGER if remaining / span < 0.2 else COLOR_PRIMARY_TEXT
		)


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
	_apply_identity_art(player_name)
	var lines := ""
	lines += "[color=#C9A24D]CULTIVATION[/color]\n"
	lines += "[color=#BFB298]Body[/color] [color=#7CA558][b]%s[/b][/color]  [color=#8E8471]%.0f / %.0f (%.0f%%)[/color]\n" % [body.get("display_name", player.get("realm", "-")), body_progress, body_required, body_percent]
	lines += "[color=#BFB298]Strain[/color] [color=#D9A441]%s / 100[/color]   [color=#BFB298]Stability[/color] [color=#7CA558]%s / 100[/color]\n" % [body.get("cultivation_strain", 0), body.get("foundation_stability", 100)]
	if bool(player.get("essence_unlocked", true)):
		lines += "[color=#BFB298]Essence[/color] [color=#A87ED8][b]%s[/b][/color]  [color=#8E8471]%.0f / %.0f (%.0f%%)[/color]\n" % [essence.get("display_name", player.get("essence_cultivation", "-")), essence_progress, essence_required, essence_percent]
		lines += "[color=#BFB298]Essence strain[/color] [color=#D9A441]%s / 100[/color]\n" % essence.get("cultivation_strain", 0)
	else:
		lines += "[color=#BFB298]Essence[/color] [color=#A87ED8][b]Locked[/b][/color]\n"
		var req := str(essence.get("unlock_requirement", ""))
		if req != "":
			lines += "[color=#8E8471]%s[/color]\n" % req
	lines += "\n[color=#C9A24D]FATE[/color]\n"
	lines += "[color=#BFB298]Martial Talent[/color] [color=#A87ED8]%s[/color]\n" % martial_talent.get("display_name", "Unknown")
	lines += "[color=#BFB298]Body Talent[/color] [color=#7CA558]%s[/color]\n" % body_talent.get("display_name", "Unknown")
	lines += "[color=#BFB298]Lifespan[/color] [color=#E4C87F]%s[/color]\n" % lifespan.get("display", "Unknown")
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


# --- Inventory tab: item card grid ------------------------------------------

func _rarity_color(rarity: String) -> Color:
	return UIKit.rarity_color(rarity)


func _render_inventory(state: Dictionary) -> void:
	_inventory_panel.render(state)


## Equip flow straight from an inventory card: one item, slot choice.
func _equip_from_card(item_id: String) -> void:
	_equip_choices = []
	var item: Dictionary = {}
	for candidate in _last_state.get("inventory_items", []):
		if typeof(candidate) == TYPE_DICTIONARY and str(candidate.get("item_id", "")) == item_id:
			item = candidate
			break
	_open_dialog("Equip - %s" % str(item.get("name", item_id)), Vector2(520, 0))
	for slot in item.get("valid_slots", []):
		var target_slot := str(slot)
		if target_slot == "":
			continue
		_add_dialog_row(_slot_label(target_slot), "", "", false, "", _equip_choices.size(), _on_equip_pick)
		_equip_choices.append({"item_id": item_id, "slot": target_slot})
	if _equip_choices.is_empty():
		_add_dialog_empty("This item has no valid slot.")
	_close_dialog_footer()


# --- Equipment tab ------------------------------------------------------------

func _render_equipment(player: Dictionary) -> void:
	_equipment_panel.render(player)


func _format_item_modifiers(item: Dictionary) -> String:
	return UIKit.format_item_modifiers(item)


func _format_modifier_group(group: Dictionary) -> String:
	return UIKit.format_modifier_group(group)


func _format_modifier_value(key: String, value: Variant) -> String:
	return UIKit.format_modifier_value(key, value)


func _humanize_key(key: String) -> String:
	return UIKit.humanize_key(key)


# --- Journal tab: quest cards -------------------------------------------------

func _render_quests(quests: Array) -> void:
	_journal_panel.render(quests)


# --- Status tab: structured sheet + realm ladder ------------------------------

func _render_status_summary(player: Dictionary) -> void:
	_status_panel.render(player)


# --- Techniques tab: skill cards ------------------------------------------------

func _render_techniques(player: Dictionary) -> void:
	_techniques_panel.render(player, _cooldowns)


func _rebuild_combat_actions() -> void:
	_clear_row(_combat_actions)
	_combat_actions.add_child(_make_button("Attack", func(): _send("ATTACK"), "Strike with a basic attack."))
	for skill in _known_skills:
		if typeof(skill) != TYPE_DICTIONARY:
			continue
		if str(skill.get("type", "")) != "active":
			continue
		var skill_id := str(skill.get("id", ""))
		if skill_id == "":
			continue
		var skill_name := str(skill.get("name", skill_id))
		var qi := int(skill.get("qi_cost", 0))
		var cd := int(skill.get("cooldown", 0))
		var insight := int(skill.get("insight_required", 0))
		var tooltip := "Qi: %d - Cooldown: %d" % [qi, cd]
		if insight > 0:
			tooltip += " - Requires %d Insight" % insight
		_combat_actions.add_child(_make_button(skill_name, api.send_action.bind({"action": "USE_SKILL", "skill_id": skill_id}), tooltip))
	_combat_actions.add_child(_make_button("Healing Pill", func(): api.send_action({"action": "USE_ITEM", "item_id": "healing_pill"}), "Use a healing pill."))
	_combat_actions.add_child(_make_button("Flee", func(): _send("FLEE"), "Attempt to escape."))
	# B.9 formations: when more than one foe stands, let the player pick which
	# one to face instead of locking the fight to whoever arrived first.
	# The engine always sends the "enemy" key, but sets it to null outside combat,
	# and Dictionary.get() returns that null rather than the {} fallback -- so the
	# value's type must be tested before it is read.
	var current_enemy = _last_state.get("enemy")
	var facing := ""
	if typeof(current_enemy) == TYPE_DICTIONARY:
		facing = str(current_enemy.get("id", ""))
	for foe in _last_state.get("enemies", []):
		if typeof(foe) != TYPE_DICTIONARY:
			continue
		var foe_id := str(foe.get("id", ""))
		if foe_id == "" or foe_id == facing:
			continue
		var foe_tooltip := "Face this foe: HP %s/%s, ATK %s." % [str(foe.get("hp", 0)), str(foe.get("max_hp", 0)), str(foe.get("attack", 0))]
		_combat_actions.add_child(_make_button("Face %s" % str(foe.get("name", foe_id)), api.send_action.bind({"action": "TARGET_FOE", "foe_id": foe_id}), foe_tooltip))


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
	lines += "Enemy HP: %s/%s   " % [enemy.get("hp", 0), enemy.get("max_hp", 0)]
	lines += "Threat: [color=#D9A441]%s[/color]\n" % enemy.get("threat", "Unknown")
	lines += "Possible EXP: %s   " % rewards.get("exp", 0)
	lines += "Possible Items: %s" % _join_array(rewards.get("items", []))
	var others: Array[String] = []
	for foe in _last_state.get("enemies", []):
		if typeof(foe) != TYPE_DICTIONARY or str(foe.get("id", "")) == str(enemy.get("id", "")):
			continue
		others.append("%s %s/%s" % [str(foe.get("name", "?")), str(foe.get("hp", 0)), str(foe.get("max_hp", 0))])
	if others.size() > 0:
		lines += "\n[color=#C9A24D]Also here:[/color] %s" % _join_array(others)
	_set_rich_text(_enemy_details, lines)


func _show_debate(result: Dictionary) -> void:
	# B.7: conviction bars for the debate of dao (mirrors the combat bars).
	var debate: Dictionary = result.get("debate", {})
	var lines: Array[String] = []
	lines.append("[color=#C9A24D]Round %s / %s[/color]" % [str(debate.get("round", 0)), str(debate.get("max_rounds", 0))])
	lines.append("Your conviction: %s / %s" % [str(debate.get("player_conviction", 0)), str(debate.get("max_conviction", 0))])
	lines.append("%s's conviction: %s / %s" % [str(debate.get("foe_name", "Foe")), str(debate.get("foe_conviction", 0)), str(debate.get("foe_max_conviction", debate.get("max_conviction", 0)))])
	if debate.has("oath") and debate.get("oath", null) != null:
		lines.append("[color=#C9A24D]A spirit oath binds this debate.[/color]")
	lines.append("Stances: assert presses - probe exposes - transcend evades - yield concedes")
	_set_situation("Dao Debate", "\n".join(lines))

func _render_debate_end(result: Dictionary) -> void:
	var outcome := str(result.get("outcome", ""))
	var oath: Dictionary = result.get("oath", {})
	var lines: Array[String] = [str(result.get("player_message", "The debate ends."))]
	if outcome == "DEBATE_WON" and not oath.is_empty():
		lines.append("[color=#7CA558]The oath pays out: +%s gold, +%s exp.[/color]" % [str(oath.get("gold_won", 0)), str(oath.get("exp_won", 0))])
	elif outcome == "DEBATE_LOST" and not oath.is_empty():
		lines.append("[color=#C0393A]The oath collects: -%s gold, -%s exp.[/color]" % [str(oath.get("gold_lost", 0)), str(oath.get("exp_lost", 0))])
	elif outcome == "DEBATE_ABANDONED" and not oath.is_empty():
		lines.append("[color=#C0393A]The oath's breach costs you %s gold.[/color]" % str(oath.get("gold_forfeit", 0)))
	_set_situation("Debate Concluded", "\n".join(lines))
	_append("Debate outcome: %s" % outcome)

func _send_world_info() -> void:
	api.send_action({"action": "WORLD_INFO"})

func _append_world_tick(result: Dictionary) -> void:
	# E.1-E.3: surface the world's happenings after any time-consuming action.
	if not result.has("world_tick"):
		return
	var tick: Dictionary = result.get("world_tick", {})
	var deaths: Array = tick.get("deaths", [])
	for death_id in deaths:
		_append("[color=#C0393A]Word arrives: %s has fallen.[/color]" % str(death_id).replace("_", " ").capitalize())
	var gains: Array = tick.get("rank_gains", [])
	if gains.size() > 0:
		_append("Cultivators deepen their dao beyond your sight.")
	var shifts: Array = tick.get("sect_shifts", [])
	for shift in shifts:
		var direction: String = "rises" if float(shift.get("delta", 0.0)) > 0.0 else "wanes"
		_append("A sect %s in power." % direction)
	var rumors: Array = tick.get("rumors", [])
	for rumor in rumors:
		_append("[color=#C9A24D]Rumor: %s[/color]" % str(rumor.get("summary", "")))
	if float(tick.get("price_multiplier", 1.0)) >= 1.05:
		_append("[color=#D9A441]The markets tighten; prices climb.[/color]")
	elif float(tick.get("price_multiplier", 1.0)) <= 0.95:
		_append("[color=#7CA558]Goods flood the markets; prices fall.[/color]")

func _render_rumor_learned(result: Dictionary) -> void:
	# E.5: a learned rumor becomes a concrete reveal (sect/location/npc).
	if not result.has("rumor_learned"):
		return
	var learned: Dictionary = result.get("rumor_learned", {})
	var reveal: Dictionary = learned.get("reveal", {})
	var reveal_name := str(reveal.get("name", reveal.get("id", "")))
	if reveal_name != "":
		_append("[color=#C9A24D]They speak of it: %s (%s).[/color]" % [str(learned.get("rumor", {}).get("summary", "")), reveal_name])

func _show_world_info(result: Dictionary) -> void:
	var lines: Array[String] = []
	lines.append("[color=#C9A24D]Year %s - %s[/color]" % [str(result.get("year", 0.0)), str(result.get("season", ""))])
	var mods: Dictionary = result.get("season_modifiers", {})
	lines.append("Season -- Yield x%s - Travel x%s - Danger x%s" % [str(mods.get("gather_yield", 1.0)), str(mods.get("travel_years", 1.0)), str(mods.get("combat_bias", 1.0))])
	lines.append("Market prices: x%s" % str(result.get("market_price_multiplier", 1.0)))
	lines.append("Cultivators: %s / %s alive" % [str(result.get("cultivators_alive", 0)), str(result.get("cultivators_total", 0))])
	var ranking: Array = result.get("sect_ranking", [])
	if ranking.size() > 0:
		lines.append("[color=#C9A24D]SECT POWER[/color]")
		for entry in ranking:
			lines.append("%s -- %s" % [str(entry.get("name", entry.get("sect_id", ""))), str(entry.get("power", 0.0))])
	var rumors: Array = result.get("rumors", [])
	lines.append("[color=#C9A24D]RUMORS[/color]")
	if rumors.is_empty():
		lines.append("The world is quiet; no rumors stir.")
	for rumor in rumors:
		var known := bool(rumor.get("learned", false))
		var mark: String = "(known)" if known else "(overheard)"
		lines.append("%s %s" % [mark, str(rumor.get("summary", ""))])
	_set_situation("The Living World", "\n".join(lines))
	_append("Consulted the winds of the world.")
	_season_label.text = str(result.get("season", _season_label.text))




# --- Narrative + log plumbing (canon pass) ----------------------------------


func _set_situation(title: String, text: String) -> void:
	# Mirror the latest situation to the narrative panel; richer engine prose may
	# replace it afterwards via _set_narrative when a narrative field exists.
	_set_narrative("[color=#F0C76A][b]%s[/b][/color]
%s" % [title, text])
	_append("[color=#F0C76A][b]%s[/b][/color] %s" % [title, text.replace("
", "  ")])


func _set_narrative(text: String) -> void:
	if _narrative_text == null:
		return
	_narrative_text.clear()
	_narrative_text.append_text(text)


func _set_rich_text(control: RichTextLabel, text: String) -> void:
	UIKit.set_rich_text(control, text)


func _title_from_id(value: String) -> String:
	return UIKit.title_from_id(value)


func _format_quantity(value) -> String:
	return UIKit.format_quantity(value)


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
		_log.append_text(text + "
")
	else:
		_log.append_text("[color=#8F8A81][Year %d][/color] %s
" % [_year, text])


func _render_event(result: Dictionary) -> void:
	_showing_event_result = true
	var event := str(result.get("event", ""))
	var prose := str(result.get("narrative", ""))
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
			var summary: Dictionary = result.get("summary", {})
			var summary_text := ""
			if not summary.is_empty():
				var peak := str(summary.get("body_realm", "?"))
				var essence_name := str(summary.get("essence_realm", ""))
				if essence_name != "":
					peak += " / " + essence_name
				summary_text = "\n\n[color=#C7BCA8]Peak realms: %s[/color]" % peak
				summary_text += "\nDao: %s  ·  Path: %s" % [str(summary.get("dao", "?")), str(summary.get("path", "Unassigned"))]
				summary_text += "\nQuests completed: %s  ·  Ancestral Memory: %s" % [str(summary.get("quests_completed", 0)), str(result.get("ancestral_memory", 0))]
			_set_situation("Your Dao Ends", "%s\n\n[color=#C0393A]You perished at the age of %s. Your journey is over.[/color]%s" % [str(result.get("player_message", "Your lifespan is exhausted.")), age_text, summary_text])
			_append("[color=#C0393A]You died at %s.[/color]" % age_text)
		"CHARACTER_ENCOUNTER":
			_render_character_encounter(result)
		"CHARACTER_INTERACTION":
			_set_situation(str(result.get("name", "Conversation")), str(result.get("player_message", "They acknowledge you.")))
			_append("Talked with %s" % result.get("name", result.get("character_id", "someone")))
			_render_rumor_learned(result)
		"EXPLORE_RESULT":
			_set_situation("Exploration", str(result.get("text", "You roam the wilds.")))
			_append(str(result.get("text", "Explored the area.")))
		"ENCOUNTER":
			_render_encounter(result)
		"ENCOUNTER_RESULT":
			_render_encounter_result(result)
		"COMBAT":
			_set_combat_mode(true)
			var combat_enemy = result.get("enemy")
			if typeof(combat_enemy) == TYPE_DICTIONARY:
				_update_enemy(combat_enemy)
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
		"BOON":
			_set_situation("Boon Received", str(result.get("player_message", "They grant you a gift.")))
			_append("Received a boon from %s" % result.get("name", result.get("character_id", "an ally")))
		"DIALOGUE_CHOICE":
			_set_situation(str(result.get("name", "Dialogue")), str(result.get("player_message", "")))
		"SECTS":
			_set_situation(str(result.get("sect", {}).get("display_name", "Sect")), str(result.get("sect", {}).get("description", "")))
		"SECT_JOINED":
			_set_situation("Sect Joined", str(result.get("player_message", "You join the sect.")))
			_append("Joined %s" % result.get("name", result.get("sect_id", "a sect")))
		"ITEM_SOLD":
			_set_situation("Item Sold", str(result.get("player_message", "You sell the item.")))
			_append("Sold %s for %s gold" % [result.get("name", "item"), result.get("total", 0)])
		"TALENTS":
			# The engine answers with the live upgrade table, so the arm has to open
			# the dialog that spends it -- a caption here made the action a dead end
			# and orphaned _show_talents().
			_show_talents(result)
		"TALENT_UPGRADED":
			_set_situation("Talent Advanced", str(result.get("player_message", "Your talent advances.")))
			_append("Talent advanced to %s" % result.get("display_name", result.get("talent_id", "")))
		"CLOSED_DOOR_RESULT":
			_set_situation("Closed-Door Cultivation", str(result.get("player_message", "You cultivate in seclusion.")))
			_append("Secluded cultivation for %s year(s)" % result.get("years", 0))
		"REPAIR_RESULT":
			_set_situation("Repaired", str(result.get("player_message", "Item repaired.")))
			_append("Repaired %s" % result.get("item_id", "item"))
		"GATHER_RESULT":
			_set_situation("Herbs Gathered", "Gathered %s x%s." % [result.get("name", "herb"), _format_quantity(result.get("count", 1))])
			_append("Gathered %s" % result.get("name", "herb"))
		"REFINE_RESULT":
			_set_situation("Refined", str(result.get("name", "Refinement complete.")))
			_append("Refined %s x%s" % [result.get("item_id", "item"), _format_quantity(result.get("count", 1))])
		"REALM_ENTERED":
			var realm_name := str(result.get("realm", {}).get("display_name", "a secret realm"))
			var realm_text := str(result.get("player_message", "You descend into the realm."))
			if bool(result.get("endless", false)):
				realm_text += "\n[color=#9B6ADB]Endless depth %s.[/color]" % str(result.get("endless_depth", 1))
				if str(result.get("realm_cap_lifted", "")) != "":
					realm_text += "\n[color=#D6A84F]The final realm is no longer barred: %s awaits.[/color]" % str(result.get("realm_cap_lifted", "")).replace("_", " ").capitalize()
			_set_situation(realm_name, realm_text)
			_append("[color=#9B6ADB]Entered %s[/color]" % realm_name)
		"REALM_ROOM":
			_set_situation("Secret Realm", str(result.get("player_message", "You press on through the realm.")))
			_append(str(result.get("player_message", "You press on through the realm.")))
		"REALM_COMPLETED":
			_set_situation("Realm Conquered", str(result.get("player_message", "You conquer the realm.")))
			_append("[color=#D6A84F]Realm conquered:[/color] %s" % str(result.get("realm", "")))
		"DAO_VIEW":
			_show_dao_view(result)
		"DAO_AWAKENED":
			_set_situation("Dao Awakened", str(result.get("player_message", "You awaken to a new Dao.")))
			_append("[color=#9B6ADB]Awakened to the %s[/color]" % result.get("dao_name", result.get("dao_id", "Dao")))
		"SAVE_EXPORTED":
			_set_situation("Save Exported", str(result.get("player_message", "Your save has been exported.")))
		"SAVE_IMPORTED":
			_set_situation("Save Imported", str(result.get("player_message", "Your save has been imported.")))
		"LOCATION":
			_set_situation("Location", str(result.get("display_name", result.get("name", ""))))
		"MAP":
			_set_situation("World Map", str(result.get("location_name", "The known world")))
		"QUEST_UPDATE":
			_set_situation("Quest Progress", str(result.get("title", "A quest advances.")))
		"MESSAGE":
			_set_situation("Message", str(result.get("text", "")))
		"DEBATE_STARTED":
			_show_debate(result)
		"OATH_DUEL_STARTED":
			_show_debate(result)
		"DEBATE_END":
			_render_debate_end(result)
		"CODEX":
			_set_situation("Codex", "The wanderer's codex: secret realms, sects, and faction arcs.")
			_append("Opened the codex.")
			_open_codex_popup(result)
		"WORLD_INFO":
			_show_world_info(result)
		"TECHNIQUES":
			var taught: Array = result.get("skills", [])
			_set_situation("Techniques", "Techniques known: %s" % str(taught.size()))
			for taught_entry in taught:
				if typeof(taught_entry) == TYPE_DICTIONARY:
					_append("%s - %s" % [str(taught_entry.get("name", taught_entry.get("skill_id", "?"))), str(taught_entry.get("category", ""))])
		"DEBATE_ROUND":
			_show_debate(result)
			_append(str(result.get("player_message", "The exchange turns.")))
		"HAZARD":
			_set_situation("Hazard", "The land answers your step: %s." % str(result.get("hazard_id", "an unseen hazard")))
		"RETIRED":
			_set_situation("Ascension", "%s\n\n[color=#D6A84F]Ancestral Memory +%s.[/color]" % [str(result.get("player_message", "Your run is complete.")), str(result.get("reward", 0))])
			_append("Ascended at age %s." % str(result.get("age_years", "?")))
		"NAME_CHANGED":
			var renamed := str(result.get("name", ""))
			_set_situation("Identity", prose if prose != "" else "The world will know you as %s." % renamed)
		"RUMOR_LEARNED":
			var heard: Dictionary = result.get("rumor", {})
			var revealed: Dictionary = result.get("reveal", {})
			_set_situation("Rumor Learned", str(result.get("player_message", heard.get("summary", ""))))
			_append("[color=#C9A24D]%s (%s)[/color]" % [str(heard.get("summary", "")), str(revealed.get("name", revealed.get("id", "")))])
		"WORLD_RUMORS":
			var stirring: Array = result.get("rumors", [])
			_set_situation("Rumors", "Year %s - %s rumor(s) stirring." % [str(result.get("year", 0.0)), str(stirring.size())])
			for rumor_entry in stirring:
				if typeof(rumor_entry) == TYPE_DICTIONARY:
					_append("%s %s" % ["[known]" if bool(rumor_entry.get("learned", false)) else "[overheard]", str(rumor_entry.get("summary", ""))])
		"UNLOCK_TREE":
			var legacy_tiers: Array = result.get("tiers", [])
			_set_situation("Legacy", "Ancestral Memory: %s\n%s tier(s) of unlocks." % [str(result.get("ancestral_memory", 0)), str(legacy_tiers.size())])
		"UNLOCK_PURCHASED":
			_set_situation("Legacy Unlock", str(result.get("player_message", "Unlock purchased.")))
			_append("Ancestral Memory remaining: %s" % str(result.get("ancestral_memory", 0)))
		_:
			if debug_mode:
				_append(str(result))
	_append_world_tick(result)
	if prose != "":
		_set_narrative(prose)


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
			_body_cultivation_grid.add_child(_make_action_card(label, str(character.get("relationship_tier", "")), func(): api.send_action({"action": action_name, "character_id": character_id})))
	_body_cultivation_grid.add_child(_make_action_card("Continue", "Return to normal actions", func(): _render_actions(_last_state.get("player", {}))))
	if names.size() > 0:
		text += "\n\n" + _join_array(names)
	_set_situation("Encounter", text)
	_append("Encountered named cultivators.")


func _render_encounter(result: Dictionary) -> void:
	# The choice cards are rebuilt from state each refresh (see _refresh_state),
	# so this only narrates the scene and logs what is waiting.
	var lines: Array[String] = []
	var prose := str(result.get("narrative", ""))
	if prose != "":
		lines.append(prose)
	var detail := str(result.get("text", ""))
	if detail != "" and detail != prose:
		lines.append(detail)
	lines.append_array(_encounter_detail_lines(result))
	var outcome: Dictionary = result.get("outcome", {})
	if not outcome.is_empty() and str(outcome.get("player_message", "")) != "":
		lines.append(str(outcome.get("player_message", "")))
	_set_situation(str(result.get("title", "Encounter")), "\n".join(lines))
	_append("A decision waits: %s" % str(result.get("title", "an encounter")))


func _encounter_detail_lines(result: Dictionary) -> Array[String]:
	# What the player can see: who is here, how bad it looks, and anything an
	# observation already revealed (a hazard, a ward on a find).
	var lines: Array[String] = []
	var foes: Array = result.get("foes", [])
	if foes.size() > 0:
		var names: Array[String] = []
		for foe in foes:
			names.append("%s (%s)" % [str(foe.get("name", "?")), str(foe.get("realm", "?"))])
		lines.append("[color=#C9A24D]Facing:[/color] %s" % _join_array(names))
		lines.append("Threat: [color=#D9A441]%s[/color]" % str(result.get("threat", "Unknown")))
	var reveal: Dictionary = result.get("reveal", {})
	if reveal.has("hazard"):
		var hazard: Dictionary = reveal.get("hazard", {})
		lines.append("[color=#9B6ADB]%s[/color] - %s damage if it catches you." % [str(hazard.get("name", "Hazard")), str(hazard.get("damage", 0))])
	if reveal.has("trap"):
		var trap: Dictionary = reveal.get("trap", {})
		if bool(trap.get("trapped", false)):
			lines.append("[color=#C0393A]%s[/color] - %s damage. Read as it is, you can take it safely." % [str(trap.get("name", "Ward")), str(trap.get("damage", 0))])
	return lines


func _render_encounter_choices(encounter: Dictionary) -> void:
	_clear_action_grids()
	var options: Array = encounter.get("options", [])
	for option in options:
		if typeof(option) != TYPE_DICTIONARY:
			continue
		var choice_id := str(option.get("choice_id", ""))
		var label := str(option.get("label", choice_id))
		var hint := str(option.get("hint", ""))
		var odds = option.get("chance", null)
		if odds != null:
			hint += "  [%d%%]" % int(round(float(odds) * 100.0))
		var cost: Dictionary = option.get("cost", {})
		if not cost.is_empty():
			hint += "  [%s]" % _format_price(cost)
		var usable := bool(option.get("available", true))
		var reason := str(option.get("reason", "Not possible here."))
		_body_cultivation_grid.add_child(_make_action_card(label, hint, api.send_action.bind({"action": "ENCOUNTER_CHOICE", "choice_id": choice_id}), usable, reason))
	if options.is_empty():
		_body_cultivation_grid.add_child(_make_action_card("Continue", "Nothing left to decide", func(): api.get_state()))


func _render_encounter_result(result: Dictionary) -> void:
	var lines: Array[String] = []
	var message := str(result.get("player_message", ""))
	if message != "":
		lines.append(message)
	var cost: Dictionary = result.get("cost", {})
	if not cost.is_empty():
		lines.append("Paid: %s" % _format_price(cost))
	if result.has("damage"):
		lines.append("[color=#C0393A]Hurt for %s[/color] (HP %s)." % [str(result.get("damage", 0)), str(result.get("hp", 0))])
	if bool(result.get("shrugged_off", false)):
		lines.append("You keep your feet - barely.")
	if result.has("exp_gained"):
		lines.append("EXP +%s" % str(result.get("exp_gained", 0)))
	if result.has("reputation_gained"):
		lines.append("Reputation +%s" % str(result.get("reputation_gained", 0)))
	if result.has("insight_gained"):
		lines.append("Insight +%s" % str(result.get("insight_gained", 0)))
	var loot: Dictionary = result.get("loot", {})
	if not loot.is_empty():
		lines.append("Obtained: %s x%s" % [str(loot.get("name", "item")), str(loot.get("count", 1))])
	_set_situation("Resolved", "\n".join(lines))
	_append(message if message != "" else "The moment resolves.")


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
		if bool(result.get("tournament_won", false)):
			text += "\n[color=#D6A84F]You win the tournament bout![/color]"
		var realm_meta: Dictionary = result.get("realm", {})
		if not realm_meta.is_empty():
			text += "\n[color=#9B6ADB]Realm room cleared (%s/%s).[/color]" % [realm_meta.get("room_cleared", 0), realm_meta.get("total", 0)]
			if bool(realm_meta.get("was_boss", false)):
				text += "\nThe realm's guardian has fallen. Press on to claim the reward."
	elif outcome == "DEFEAT":
		var pen: Dictionary = result.get("penalty", {})
		text += "\nYou were rescued. Progress lost: %s, revived HP: %s." % [pen.get("progress_lost", 0), pen.get("revived_hp", 0)]
	_set_situation("Combat Ended", text)
	_append("Combat ended: %s" % outcome)
	_render_quest_updates(result.get("quest_updates", []))
	var act := str(result.get("act_complete", ""))
	if act != "":
		var act_names := {"act_one": "Act One", "act_two": "Act Two", "act_three": "Act Three"}
		var act_label := str(act_names.get(act, act))
		_append("[color=#D6A84F]%s is complete. The path ahead is open.[/color]" % act_label)
	var campaign: Dictionary = result.get("campaign_complete", {})
	if not campaign.is_empty():
		_append("[color=#D6A84F]THE CAMPAIGN IS WON: %s[/color]" % str(campaign.get("ending_name", "")))
		_append("Ancestral Memory +%s banked. The endless road is open." % str(campaign.get("legacy_bonus", 0)))
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


func _show_inventory(_result: Dictionary) -> void:
	_focus_tab(0)


func _show_status(result: Dictionary) -> void:
	var player: Dictionary = result.get("player", {})
	if not player.is_empty():
		_render_character(player)
		_render_status_summary(player)
	_focus_tab(3)

func _translate_reason(reason: String, result: Dictionary = {}) -> String:
	# The engine explains every refusal it can produce (game/utils/reasons.py) and
	# ships the sentence on the result as ``message``. Show that first: the table
	# below only knows a third of the engine's reason codes, so preferring it is
	# how the player ended up reading "That action cannot be completed right now."
	# for two thirds of refusals.
	var explained := str(result.get("message", ""))
	if explained != "":
		return explained
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
		"ITEM_NOT_USABLE":
			# The engine already explains why in ``detail`` (a refining material is
			# spent by the action that consumes it, not by USE_ITEM) -- surface its
			# wording rather than falling through to the generic refusal.
			return str(result.get("detail", "That cannot be used directly; another action spends it."))
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
		"NO_HERBS_HERE":
			return "No herbs grow at this location."
		"UNKNOWN_RECIPE":
			return "That refinement recipe is not known."
		"INSUFFICIENT_RESOURCES":
			return "You do not have the herbs required for that refinement."
		"REALM_TOO_LOW":
			return "Your cultivation realm is too low for that. Required: %s." % _humanize_key(str(result.get("required", "a higher realm")))
		"NO_REALM_HERE":
			return "No secret realm opens at this location."
		"ALREADY_IN_REALM":
			return "You are already within the secret realm."
		"NOT_IN_REALM":
			return "You are not inside a secret realm."
		"NO_TOURNAMENT_HERE":
			return "No tournament is held at this location."
		"UNKNOWN_DAO":
			return "That Dao is not among the paths."
		"NO_DAO_SPECIFIED":
			return "Choose a Dao to awaken to."
		"DAO_AWAKENING_LOCKED":
			return "The Dao heart has not opened to you yet. Walk the Act One path further."
		"DAO_ALREADY_AWAKENED":
			return "You have already awakened to your Dao."
		_:
			if debug_mode:
				return reason
			return "That action cannot be completed right now."
