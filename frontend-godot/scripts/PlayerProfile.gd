extends Node
## Persistent player identity: the cultivator's display name and chosen avatar.
##
## The engine owns the *name* (it is written into every save and every line of
## prose, so the client renames through the RENAME action); this autoload owns
## the *choice* -- what to call the next new game, and which portrait the client
## wears. Both live in ``user://profile.cfg`` so they survive quitting, and the
## avatar is presentation only: it is never sent to the backend.
##
## Autoloaded as ``Profile``.

const CONFIG_PATH := "user://profile.cfg"
const SECTION := "identity"
const AVATAR_DIR := "res://assets/avatars"
## Mirrors the engine's guard (``game/core/engine/views.py`` MAX_NAME_LENGTH).
const MAX_NAME_LENGTH := 24
const DEFAULT_NAME := "Daoist"

## The selectable portraits, each a stock archetype of the cultivation-novel
## canon (at least ten of each gender). Art: ``res://assets/avatars/<id>.png`` --
## a painting imported by ``tools/import_avatar_art.py`` where one exists, a
## generated placeholder from ``tools/gen_avatar_art.py`` otherwise.
## ``tests/test_player_identity.py`` pins this roster against that recipe table,
## so the two cannot drift.
const AVATARS: Array = [
	{"id": "mortal_disciple", "name": "Mortal Disciple", "gender": "male", "epithet": "A village boy who refused to stay mortal."},
	{"id": "sword_immortal", "name": "Sword Immortal", "gender": "male", "epithet": "One blade, one lifetime of cold light."},
	{"id": "azure_prodigy", "name": "Azure Prodigy", "gender": "male", "epithet": "A genius who stunned three sects in one night."},
	{"id": "demon_path_heir", "name": "Demon Path Heir", "gender": "male", "epithet": "Power taken, never granted."},
	{"id": "alchemist_sage", "name": "Alchemist Sage", "gender": "male", "epithet": "A furnace, a gourd, and infinite patience."},
	{"id": "dharma_monk", "name": "Dharma Monk", "gender": "male", "epithet": "The staff is heavy; so is mercy."},
	{"id": "thunder_sovereign", "name": "Thunder Sovereign", "gender": "male", "epithet": "The heavens answer him in lightning."},
	{"id": "beast_blood_hunter", "name": "Beast-Blood Hunter", "gender": "male", "epithet": "He learned the mountain by surviving it."},
	{"id": "young_master", "name": "Young Master", "gender": "male", "epithet": "Born to gold, tested by fire."},
	{"id": "wandering_swordsman", "name": "Wandering Swordsman", "gender": "male", "epithet": "No sect, no master -- only the road."},
	{"id": "sect_patriarch", "name": "Sect Patriarch", "gender": "male", "epithet": "Three generations of disciples have never seen him stand."},
	{"id": "sword_maiden", "name": "Sword Maiden", "gender": "female", "epithet": "Her blade hums before she draws it."},
	{"id": "nine_tailed_fox", "name": "Nine-Tailed Fox", "gender": "female", "epithet": "A fox spirit who smiles at heaven."},
	{"id": "jade_sect_mistress", "name": "Jade Sect Mistress", "gender": "female", "epithet": "She rules a mountain and its silence."},
	{"id": "moon_palace_fairy", "name": "Moon Palace Fairy", "gender": "female", "epithet": "Cold light, cold palace, a warm heart."},
	{"id": "phoenix_heiress", "name": "Phoenix Heiress", "gender": "female", "epithet": "Fire remembers her bloodline."},
	{"id": "poison_valley_disciple", "name": "Poison Valley Disciple", "gender": "female", "epithet": "Sweetness with a bitter end."},
	{"id": "ice_phoenix_princess", "name": "Ice Phoenix Princess", "gender": "female", "epithet": "Winter answers when she speaks."},
	{"id": "beast_girl_tamer", "name": "Beast Tamer", "gender": "female", "epithet": "The wolves came when she called."},
	{"id": "rogue_swordswoman", "name": "Rogue Swordswoman", "gender": "female", "epithet": "She left the sect and took the blade."},
	{"id": "dragon_princess", "name": "Dragon Princess", "gender": "female", "epithet": "The tide itself bows to her."},
]

## The chosen name for the next (or current) life.
var player_name := DEFAULT_NAME
## The chosen portrait id (always one of ``AVATARS``).
var avatar_id := ""

var _textures: Dictionary = {}


func _ready() -> void:
	load_profile()


# --- persistence ------------------------------------------------------------


func load_profile() -> void:
	var config := ConfigFile.new()
	if config.load(CONFIG_PATH) == OK:
		player_name = str(config.get_value(SECTION, "player_name", DEFAULT_NAME))
		avatar_id = str(config.get_value(SECTION, "avatar_id", ""))
	player_name = sanitize_name(player_name)
	if not has_avatar(avatar_id):
		avatar_id = default_avatar_id()


func save_profile() -> void:
	var config := ConfigFile.new()
	config.set_value(SECTION, "player_name", player_name)
	config.set_value(SECTION, "avatar_id", avatar_id)
	config.save(CONFIG_PATH)


func set_identity(new_name: String, new_avatar_id: String) -> void:
	"""Adopt a name + portrait, clamp them to what the game accepts, and persist."""
	player_name = sanitize_name(new_name)
	if has_avatar(new_avatar_id):
		avatar_id = new_avatar_id
	elif avatar_id == "":
		avatar_id = default_avatar_id()
	save_profile()


## Collapse whitespace and cap the length, exactly as the engine does, so the
## name the client shows is the name the engine stored (and the one in the save).
func sanitize_name(raw: String) -> String:
	var clean := ""
	for part in raw.strip_edges().split(" ", false):
		if clean != "":
			clean += " "
		clean += part
	if clean.length() > MAX_NAME_LENGTH:
		clean = clean.substr(0, MAX_NAME_LENGTH).strip_edges()
	return clean if clean != "" else DEFAULT_NAME


# --- roster -----------------------------------------------------------------


func default_avatar_id() -> String:
	if AVATARS.is_empty():
		return ""
	return str(AVATARS[0]["id"])


func has_avatar(id: String) -> bool:
	return not avatar_entry(id).is_empty()


func avatar_entry(id: String) -> Dictionary:
	for entry in AVATARS:
		if str(entry["id"]) == id:
			return entry
	return {}


## Entries matching a gender filter; ``""`` returns the whole roster.
func avatars_for_gender(gender: String) -> Array:
	if gender == "":
		return AVATARS
	var filtered := []
	for entry in AVATARS:
		if str(entry["gender"]) == gender:
			filtered.append(entry)
	return filtered


func avatar_display_name(id: String) -> String:
	var entry := avatar_entry(id)
	return str(entry.get("name", "Unadorned"))


func avatar_path(id: String) -> String:
	return "%s/%s.png" % [AVATAR_DIR, id]


## The portrait texture, or ``null`` when the art is missing (callers fall back
## to a monogram). Textures are cached; a missing portrait is cached too, so a
## broken install never re-reads the disk every frame.
func avatar_texture(id: String) -> Texture2D:
	if _textures.has(id):
		return _textures[id]
	var texture: Texture2D = null
	var path := avatar_path(id)
	if ResourceLoader.exists(path):
		texture = load(path)
	elif FileAccess.file_exists(path):
		# Before the editor has imported the PNG there is no imported resource.
		var image := Image.new()
		if image.load(path) == OK:
			texture = ImageTexture.create_from_image(image)
	_textures[id] = texture
	return texture


## The portrait currently worn (falls back to the first roster entry).
func current_texture() -> Texture2D:
	return avatar_texture(avatar_id if has_avatar(avatar_id) else default_avatar_id())


## The first letter of the current name, for the monogram fallback.
func monogram() -> String:
	if player_name.length() == 0:
		return "?"
	return player_name.substr(0, 1).to_upper()
