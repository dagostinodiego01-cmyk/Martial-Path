extends VBoxContainer
class_name IdentityEditor
## The name-and-avatar picker, shared by the main menu and the in-game dossier.
##
## Self-contained by design: it reads and writes ``Profile`` itself and reports
## the outcome with one signal, so both hosts get the same widget without
## duplicating the grid, the gender filter, or the persistence rules. The host
## only decides how to frame it (a dialog band in-game, a popup before a new
## game).
##
## The name is applied through the engine's RENAME action by the host (the
## engine owns the living cultivator's name); this widget owns the avatar, which
## is presentation only.

signal committed(player_name: String, avatar_id: String)
signal cancelled()

# Mirrors the lacquer/gold palette of the controllers (kept local so the widget
# can be hosted by either scene without importing their constants).
const COLOR_PANEL_SOFT := Color("242019")
const COLOR_PANEL_RAISED := Color("2A241B")
const COLOR_BORDER := Color("4B3E22")
const COLOR_GOLD := Color("C9A24D")
const COLOR_GOLD_BRIGHT := Color("E4C87F")
const COLOR_TEXT := Color("E7DDC6")
const COLOR_MUTED := Color("8E8471")

const ART_SIZE := 76
const GRID_COLUMNS := 5

## Pre-filled name, set by the host before the widget enters the tree. Empty
## falls back to the stored profile name; in-game the host passes the living
## cultivator's name instead, which may differ from a newly loaded save.
var initial_name := ""

var _name_field: LineEdit
var _grid: GridContainer
var _selected_line: Label
var _gender := ""
var _selected_id := ""
var _cards: Dictionary = {}
var _frames: Dictionary = {}
var _labels: Dictionary = {}
var _filter_buttons: Dictionary = {}


func _ready() -> void:
	add_theme_constant_override("separation", 10)
	_selected_id = Profile.avatar_id
	if not Profile.has_avatar(_selected_id):
		_selected_id = Profile.default_avatar_id()
	_build()
	_refresh_grid()


# --- construction -----------------------------------------------------------


func _build() -> void:
	add_child(_caption("YOUR NAME"))
	_name_field = LineEdit.new()
	_name_field.text = Profile.sanitize_name(initial_name) if initial_name != "" else Profile.player_name
	_name_field.placeholder_text = Profile.DEFAULT_NAME
	_name_field.max_length = Profile.MAX_NAME_LENGTH
	_name_field.custom_minimum_size = Vector2(0, 38)
	_name_field.add_theme_font_size_override("font_size", 16)
	_name_field.text_submitted.connect(func(_text: String): _commit())
	add_child(_name_field)

	add_child(_caption("PORTRAIT"))

	var filters := HBoxContainer.new()
	filters.add_theme_constant_override("separation", 8)
	add_child(filters)
	var group := ButtonGroup.new()
	for option in [["", "ALL"], ["male", "MALE"], ["female", "FEMALE"]]:
		var button := Button.new()
		button.text = str(option[1])
		button.toggle_mode = true
		button.button_group = group
		button.custom_minimum_size = Vector2(96, 30)
		button.button_pressed = str(option[0]) == _gender
		button.pressed.connect(_on_filter_pressed.bind(str(option[0])))
		_filter_buttons[str(option[0])] = button
		filters.add_child(button)

	_grid = GridContainer.new()
	_grid.columns = GRID_COLUMNS
	_grid.add_theme_constant_override("h_separation", 8)
	_grid.add_theme_constant_override("v_separation", 8)
	_grid.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	add_child(_grid)

	_selected_line = Label.new()
	_selected_line.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_selected_line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_selected_line.custom_minimum_size = Vector2(0, 40)
	_selected_line.add_theme_font_size_override("font_size", 13)
	_selected_line.add_theme_color_override("font_color", COLOR_TEXT)
	add_child(_selected_line)

	var actions := HBoxContainer.new()
	actions.add_theme_constant_override("separation", 8)
	add_child(actions)
	var spacer := Control.new()
	spacer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	actions.add_child(spacer)
	var cancel := Button.new()
	cancel.text = "Close"
	cancel.custom_minimum_size = Vector2(120, 38)
	cancel.pressed.connect(func(): cancelled.emit())
	actions.add_child(cancel)
	var commit := Button.new()
	commit.text = "INSCRIBE"
	commit.custom_minimum_size = Vector2(160, 38)
	commit.add_theme_stylebox_override("normal", _primary_style(COLOR_GOLD))
	commit.add_theme_stylebox_override("hover", _primary_style(COLOR_GOLD_BRIGHT))
	commit.add_theme_stylebox_override("pressed", _primary_style(Color("A9863C")))
	commit.add_theme_color_override("font_color", Color("241B0D"))
	commit.add_theme_color_override("font_hover_color", Color("241B0D"))
	commit.add_theme_color_override("font_pressed_color", Color("241B0D"))
	commit.add_theme_font_size_override("font_size", 15)
	commit.pressed.connect(_commit)
	actions.add_child(commit)


func _caption(text: String) -> Label:
	var label := Label.new()
	label.text = text
	label.add_theme_font_size_override("font_size", 12)
	label.add_theme_color_override("font_color", COLOR_GOLD)
	return label


func _primary_style(fill: Color) -> StyleBoxFlat:
	var style := StyleBoxFlat.new()
	style.bg_color = fill
	style.border_color = fill
	style.set_border_width_all(1)
	style.content_margin_left = 12
	style.content_margin_right = 12
	style.content_margin_top = 6
	style.content_margin_bottom = 6
	return style


# --- the avatar grid --------------------------------------------------------


func _refresh_grid() -> void:
	for child in _grid.get_children():
		child.queue_free()
	_cards.clear()
	_frames.clear()
	_labels.clear()
	for entry: Dictionary in Profile.avatars_for_gender(_gender):
		var id := str(entry["id"])
		var card := _make_card(entry)
		_cards[id] = card
		_grid.add_child(card)
	_paint_cards()
	_update_selected_line()


func _make_card(entry: Dictionary) -> PanelContainer:
	var id := str(entry["id"])
	var card := PanelContainer.new()
	card.mouse_filter = Control.MOUSE_FILTER_STOP
	card.tooltip_text = str(entry.get("epithet", ""))
	card.gui_input.connect(func(event: InputEvent): _on_card_input(event, id))

	var column := VBoxContainer.new()
	column.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_theme_constant_override("separation", 4)
	card.add_child(column)

	var frame := PanelContainer.new()
	frame.custom_minimum_size = Vector2(ART_SIZE, ART_SIZE)
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(frame)
	_frames[id] = frame

	var art := TextureRect.new()
	art.texture = Profile.avatar_texture(id)
	art.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	art.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
	art.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.add_child(art)

	var name_label := Label.new()
	name_label.text = str(entry.get("name", id))
	name_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	name_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	name_label.custom_minimum_size = Vector2(ART_SIZE, 0)
	name_label.add_theme_font_size_override("font_size", 11)
	name_label.add_theme_color_override("font_color", COLOR_MUTED)
	name_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	column.add_child(name_label)
	_labels[id] = name_label
	return card


## A card is a click target, not a Button: it holds a portrait and a caption, so
## its minimum size must come from its content.
func _on_card_input(event: InputEvent, id: String) -> void:
	if event is InputEventMouseButton and event.pressed and event.button_index == MOUSE_BUTTON_LEFT:
		_selected_id = id
		_paint_cards()
		_update_selected_line()


func _paint_cards() -> void:
	for key in _cards:
		var id := str(key)
		var chosen := id == _selected_id
		var card: PanelContainer = _cards[key]
		var card_style := StyleBoxFlat.new()
		card_style.bg_color = COLOR_PANEL_RAISED if chosen else Color(0, 0, 0, 0)
		card_style.border_color = COLOR_GOLD_BRIGHT if chosen else Color(0, 0, 0, 0)
		card_style.set_border_width_all(1)
		card_style.content_margin_left = 6
		card_style.content_margin_right = 6
		card_style.content_margin_top = 6
		card_style.content_margin_bottom = 6
		card.add_theme_stylebox_override("panel", card_style)

		var frame: PanelContainer = _frames[key]
		var frame_style := StyleBoxFlat.new()
		frame_style.bg_color = Color("0E0C08")
		frame_style.border_color = COLOR_GOLD_BRIGHT if chosen else COLOR_BORDER
		frame_style.set_border_width_all(2 if chosen else 1)
		frame.add_theme_stylebox_override("panel", frame_style)

		var name_label: Label = _labels[key]
		name_label.add_theme_color_override("font_color", COLOR_GOLD_BRIGHT if chosen else COLOR_MUTED)


func _update_selected_line() -> void:
	var entry := Profile.avatar_entry(_selected_id)
	if entry.is_empty():
		_selected_line.text = ""
		return
	_selected_line.text = "%s - %s" % [str(entry.get("name", _selected_id)), str(entry.get("epithet", ""))]


func _on_filter_pressed(gender: String) -> void:
	_gender = gender
	_refresh_grid()


# --- committing -------------------------------------------------------------


## The pending name (already clamped the way the engine will clamp it).
func chosen_name() -> String:
	return Profile.sanitize_name(_name_field.text)


## The pending portrait id.
func chosen_avatar() -> String:
	return _selected_id


func focus_name_field() -> void:
	if _name_field != null:
		_name_field.grab_focus()
		_name_field.select_all()


func _commit() -> void:
	Profile.set_identity(_name_field.text, _selected_id)
	_name_field.text = Profile.player_name
	committed.emit(Profile.player_name, Profile.avatar_id)
