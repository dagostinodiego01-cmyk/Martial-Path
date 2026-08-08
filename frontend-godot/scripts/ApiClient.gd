extends Node
class_name ApiClient
## Thin HTTP client for the Martial Path FastAPI backend.
##
## Sends structured commands and emits parsed JSON results. It performs NO game
## logic: Python remains the single source of truth. One request is in flight at
## a time (HTTPRequest is single-flight), guarded by ``_busy``.

signal state_loaded(state: Dictionary)
signal action_completed(result: Dictionary)
signal request_failed(message: String)

const BASE_URL := "http://127.0.0.1:8000"

var _http: HTTPRequest
var _busy := false


func _ready() -> void:
	_http = HTTPRequest.new()
	_http.timeout = 10.0
	add_child(_http)
	_http.request_completed.connect(_on_request_completed)


func get_state() -> void:
	if _busy:
		return
	_busy = true
	var err := _http.request(BASE_URL + "/state")
	if err != OK:
		_busy = false
		request_failed.emit("Could not reach backend (state). Is uvicorn running? [%s]" % err)


func send_action(action_data: Dictionary) -> void:
	if _busy:
		request_failed.emit("Please wait for the current action to finish.")
		return
	_busy = true
	var headers := ["Content-Type: application/json"]
	var body := JSON.stringify(action_data)
	var err := _http.request(BASE_URL + "/action", headers, HTTPClient.METHOD_POST, body)
	if err != OK:
		_busy = false
		request_failed.emit("Could not reach backend (action). Is uvicorn running? [%s]" % err)


func travel(location_id: String) -> void:
	send_action({"action": "TRAVEL", "location_id": location_id})


func save_game(slot: String = "default") -> void:
	send_action({"action": "SAVE", "slot": slot})


func load_game(slot: String = "default") -> void:
	send_action({"action": "LOAD", "slot": slot})


func new_game(player_name: String = "Daoist", seed_value = null) -> void:
	if _busy:
		request_failed.emit("Please wait for the current action to finish.")
		return
	_busy = true
	var headers := ["Content-Type: application/json"]
	var payload := {"player_name": player_name}
	if seed_value != null:
		payload["seed"] = seed_value
	var err := _http.request(BASE_URL + "/new-game", headers, HTTPClient.METHOD_POST, JSON.stringify(payload))
	if err != OK:
		_busy = false
		request_failed.emit("Could not reach backend (new-game). Is uvicorn running? [%s]" % err)


func _on_request_completed(result: int, response_code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	_busy = false

	if result != HTTPRequest.RESULT_SUCCESS:
		request_failed.emit("HTTP request failed (result %s). Is the backend running?" % result)
		return

	if response_code < 200 or response_code >= 300:
		request_failed.emit("API returned HTTP %s: %s" % [response_code, body.get_string_from_utf8()])
		return

	var parsed = JSON.parse_string(body.get_string_from_utf8())
	if typeof(parsed) != TYPE_DICTIONARY:
		request_failed.emit("API returned unexpected payload.")
		return

	# Results carry an "event"; state snapshots do not.
	if parsed.has("event"):
		action_completed.emit(parsed)
	else:
		state_loaded.emit(parsed)
