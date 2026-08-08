extends Node
class_name BackendLauncher
## Boots and supervises the local Python engine backend for packaged builds.
##
## In an exported build the FastAPI engine ships as a sibling executable
## (``MartialPathBackend/MartialPathBackend.exe``). This autoload launches it on
## start-up, waits until its ``/health`` endpoint answers, and terminates it when
## the game exits so no server is left holding the port.
##
## It contains NO game logic -- it only manages a child process and polls a health
## URL. When run from the Godot editor the sibling executable does not exist, so it
## simply waits for a backend you started manually (uvicorn) instead of spawning one.

signal backend_ready
signal backend_failed(message: String)

const HEALTH_URL := "http://127.0.0.1:8000/health"
const POLL_INTERVAL_SECONDS := 0.5
const STARTUP_TIMEOUT_SECONDS := 45.0
const BACKEND_RELATIVE_PATH := "MartialPathBackend/MartialPathBackend.exe"

var is_ready := false

var _http: HTTPRequest
var _timer: Timer
var _pid := -1
var _we_started_it := false
var _shutdown_done := false
var _elapsed := 0.0


func _ready() -> void:
	# The child is ours to stop, so intercept the window-close request instead of
	# letting the tree quit before cleanup runs.
	get_tree().set_auto_accept_quit(false)

	_http = HTTPRequest.new()
	_http.timeout = 3.0
	add_child(_http)
	_http.request_completed.connect(_on_health_checked)

	_maybe_launch_backend()

	_timer = Timer.new()
	_timer.wait_time = POLL_INTERVAL_SECONDS
	_timer.one_shot = false
	add_child(_timer)
	_timer.timeout.connect(_poll_health)
	_timer.start()
	_poll_health()


func _maybe_launch_backend() -> void:
	var exe := OS.get_executable_path().get_base_dir().path_join(BACKEND_RELATIVE_PATH)
	if not FileAccess.file_exists(exe):
		# Editor / dev run: no bundled backend beside us -> use a manual uvicorn.
		return
	var pid := OS.create_process(exe, PackedStringArray())
	if pid > 0:
		_pid = pid
		_we_started_it = true


func _poll_health() -> void:
	if is_ready:
		return
	_elapsed += POLL_INTERVAL_SECONDS
	if _elapsed >= STARTUP_TIMEOUT_SECONDS:
		_timer.stop()
		backend_failed.emit("The game engine did not start in time.")
		return
	# HTTPRequest is single-flight: only probe when the previous one has finished.
	if _http.get_http_client_status() == HTTPClient.STATUS_DISCONNECTED:
		_http.request(HEALTH_URL)


func _on_health_checked(result: int, response_code: int, _headers: PackedStringArray, _body: PackedByteArray) -> void:
	if is_ready:
		return
	if result == HTTPRequest.RESULT_SUCCESS and response_code == 200:
		is_ready = true
		_timer.stop()
		backend_ready.emit()


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST:
		_shutdown_backend()
		get_tree().quit()
	elif what == NOTIFICATION_EXIT_TREE or what == NOTIFICATION_PREDELETE:
		_shutdown_backend()


func _shutdown_backend() -> void:
	if _shutdown_done:
		return
	_shutdown_done = true
	if _we_started_it and _pid > 0 and OS.is_process_running(_pid):
		OS.kill(_pid)
