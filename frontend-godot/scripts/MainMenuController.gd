extends Control
## Main menu for the Godot frontend.
##
## This scene owns desktop flow only. It never mutates gameplay state directly;
## it calls the Python backend through ApiClient and switches scenes after the
## backend confirms the requested action.

const MARTIAL_THEME := preload("res://ui/themes/martial_path_theme.tres")
const COLOR_BACKGROUND := Color("#070A0D")
const COLOR_PRIMARY_TEXT := Color("#E6DDC8")
const COLOR_MUTED := Color("#7F8A8D")
const COLOR_TITLE_GOLD := Color("#D6A84F")

var api: ApiClient
var _status_label: Label
var _logo: TextureRect
var _gated_buttons: Array[Button] = []


func _ready() -> void:
	theme = MARTIAL_THEME
	_build_ui()
	_apply_app_icon()
	api = ApiClient.new()
	add_child(api)
	api.state_loaded.connect(_on_state_loaded)
	api.action_completed.connect(_on_action_completed)
	api.request_failed.connect(_on_request_failed)
	_wire_backend_gate()


func _apply_app_icon() -> void:
	var image := Image.new()
	if image.load("res://icon.png") != OK:
		return
	DisplayServer.set_icon(image)
	if _logo:
		_logo.texture = ImageTexture.create_from_image(image)


func _build_ui() -> void:
	var background := ColorRect.new()
	background.color = COLOR_BACKGROUND
	background.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(background)

	var margin := MarginContainer.new()
	margin.set_anchors_preset(Control.PRESET_FULL_RECT)
	margin.add_theme_constant_override("margin_left", 32)
	margin.add_theme_constant_override("margin_top", 32)
	margin.add_theme_constant_override("margin_right", 32)
	margin.add_theme_constant_override("margin_bottom", 32)
	add_child(margin)

	var outer := CenterContainer.new()
	outer.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	outer.size_flags_vertical = Control.SIZE_EXPAND_FILL
	margin.add_child(outer)

	var menu := VBoxContainer.new()
	menu.custom_minimum_size = Vector2(360, 0)
	menu.add_theme_constant_override("separation", 10)
	outer.add_child(menu)

	_logo = TextureRect.new()
	_logo.custom_minimum_size = Vector2(176, 176)
	_logo.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	_logo.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	_logo.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	menu.add_child(_logo)

	var title := Label.new()
	title.text = "MARTIAL PATH"
	title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	title.add_theme_font_size_override("font_size", 38)
	title.add_theme_color_override("font_color", COLOR_TITLE_GOLD)
	menu.add_child(title)

	var subtitle := Label.new()
	subtitle.text = "A cultivation path through body, essence, and consequence"
	subtitle.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	subtitle.add_theme_color_override("font_color", COLOR_MUTED)
	menu.add_child(subtitle)

	var continue_button := _make_button("Continue", func(): _load_slot("default"))
	var new_game_button := _make_button("New Game", func(): _new_game())
	var load_button := _make_button("Load Game", func(): _load_slot("default"))
	_gated_buttons = [continue_button, new_game_button, load_button]
	menu.add_child(continue_button)
	menu.add_child(new_game_button)
	menu.add_child(load_button)
	menu.add_child(_make_button("Settings", func(): _set_status("Settings will be added with the next UI pass.")))
	menu.add_child(_make_button("Credits", func(): _set_status("Martial Path - original cultivation RPG prototype.")))
	menu.add_child(_make_button("Quit", func(): get_tree().quit()))

	_status_label = Label.new()
	_status_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_status_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_status_label.add_theme_color_override("font_color", COLOR_PRIMARY_TEXT)
	menu.add_child(_status_label)


func _make_button(text: String, callback: Callable) -> Button:
	var button := Button.new()
	button.text = text
	button.custom_minimum_size = Vector2(0, 36)
	button.pressed.connect(callback)
	return button


func _new_game() -> void:
	_set_status("Starting new game...")
	api.new_game("Daoist", null)


func _load_slot(slot: String) -> void:
	_set_status("Loading save...")
	api.load_game(slot)


func _on_state_loaded(state: Dictionary) -> void:
	_open_gameplay()


func _on_action_completed(result: Dictionary) -> void:
	if str(result.get("event", "")) == "LOAD_RESULT" and bool(result.get("success", false)):
		_open_gameplay()
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
		return
	_set_gated(false)
	_set_status("Awakening the world...")
	Backend.backend_ready.connect(_on_backend_ready)
	Backend.backend_failed.connect(_on_backend_failed)


func _on_backend_ready() -> void:
	_set_gated(true)
	_set_status("")


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
