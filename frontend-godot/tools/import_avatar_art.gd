extends SceneTree
## Asset-pipeline helper: turn source portraits into square avatar PNGs.
##
## The project has no Python imaging library, but it does have an engine with
## every codec a painter is likely to hand over (JPEG, PNG, WebP). This script
## is driven by ``tools/import_avatar_art.py``, which writes the job file, runs
## Godot headless, and records the provenance afterwards:
##
##     python tools/import_avatar_art.py sword_maiden=C:/art/wi5UL.jpg
##
## Run directly (rarely useful) with:
##     godot --headless --path frontend-godot -s res://tools/import_avatar_art.gd -- <job.json>
##
## This directory carries a ``.gdignore``, so nothing here is scanned by the
## editor or shipped in an export.
##
## Job file: {"size": 512, "items": [{"id", "source", "dest", "zoom", "top"}]}
## Result:  one ``AVATAR_IMPORT {json}`` line on stdout, then exit code 0/1.
##
## ``anchor`` decides the crop window: ``face`` (default) frames a head-and-
## shoulders bust around the topmost skin cluster, ``top``/``center`` take a
## square from the top or the middle at ``zoom`` of the short side. The face
## window is measured, not guessed twice: its geometry comes back in the result
## (``face``: face width as a fraction of the square, brow and centre position)
## and lands in the provenance manifest, so tests can pin the framing without
## pinning a single painted pixel.

const PREFIX := "AVATAR_IMPORT "

#: Face width as a fraction of the square: below the low end the subject is a
#: speck, above the high end the crop is inside the face.
const FACE_WIDTH_RANGE := Vector2(0.20, 0.55)
#: Where the brow sits vertically in the square, and how far the crop may drift
#: from a minimum-sided window when the detector finds nothing.
const BROW_AT := 0.30
const MIN_SIDE_FRACTION := 0.25


func _initialize() -> void:
	var args := OS.get_cmdline_user_args()
	if args.is_empty():
		printerr("usage: -s res://tools/import_avatar_art.gd -- <job.json>")
		quit(2)
		return

	var raw := FileAccess.get_file_as_string(args[0])
	if raw.is_empty():
		printerr("job file is missing or empty: %s" % args[0])
		quit(2)
		return
	var job = JSON.parse_string(raw)
	if typeof(job) != TYPE_DICTIONARY:
		printerr("job file is not a JSON object: %s" % args[0])
		quit(2)
		return

	var size := int(job.get("size", 512))
	var imported: Array = []
	var failed: Array = []
	for raw_item in job.get("items", []):
		if typeof(raw_item) != TYPE_DICTIONARY:
			continue
		var item: Dictionary = raw_item
		var result := _import_one(item, size)
		if result.is_empty():
			failed.append(str(item.get("id", "?")))
		else:
			imported.append(result)

	print(PREFIX + JSON.stringify({"imported": imported, "failed": failed}))
	quit(1 if failed.size() > 0 else 0)


func _import_one(item: Dictionary, size: int) -> Dictionary:
	var id := str(item.get("id", ""))
	var source := str(item.get("source", ""))
	var dest := str(item.get("dest", ""))
	if id == "" or source == "" or dest == "":
		printerr("incomplete job item: %s" % JSON.stringify(item))
		return {}

	var image := Image.new()
	var err := image.load(source)
	if err != OK:
		printerr("could not read %s (error %d)" % [source, err])
		return {}

	var width := image.get_width()
	var height := image.get_height()
	var window := _crop_window(image, item)
	var left := int(window["left"])
	var top := int(window["top"])
	var side := int(window["side"])
	var skin := _skin_box(image, 0.0, 1.0)
	var cropped := image.get_region(Rect2i(left, top, side, side))

	# ``size`` is a cap, not a target: the client's largest portrait is 76px, so
	# upscaling a small crop would add bytes and soften the face for nothing.
	var shipped := mini(size, side)
	# Avatars are drawn opaque and cover-cropped (a transparent pixel would
	# punch a hole in the picker), so a source with an alpha channel is
	# flattened to RGB rather than shipped with one nobody reads.
	if cropped.get_format() != Image.FORMAT_RGB8:
		cropped.convert(Image.FORMAT_RGB8)
	if cropped.get_width() != shipped or cropped.get_height() != shipped:
		cropped.resize(shipped, shipped, Image.INTERPOLATE_LANCZOS)
	var save_err := cropped.save_png(dest)
	if save_err != OK:
		printerr("could not write %s (error %d)" % [dest, save_err])
		return {}

	# Where the face sits inside the square it just became: the framing contract,
	# reported so a crop can be judged from the job output (and from the tests)
	# without opening the image. Only meaningful when the detector chose the
	# window -- on an explicit ``zoom``/``top`` crop a background that reads as
	# skin would report a face that is not there.
	var face := {}
	if window.get("anchor", "") == "face" and not window.get("head", {}).is_empty():
		var head: Dictionary = window["head"]
		var centre := ((float(head["left"]) + float(head["right"])) / 2.0 - float(left)) / float(side)
		var brow := (float(head["top"]) - float(top)) / float(side)
		face = {
			"width": (float(head["right"]) - float(head["left"])) / float(side),
			"centre": clampf(centre, 0.0, 1.0),
			"brow": clampf(brow, 0.0, 1.0),
			"prominent": (float(head["right"]) - float(head["left"])) / float(side) >= FACE_WIDTH_RANGE.x,
		}

	return {
		"id": id,
		"source": source,
		"dest": dest,
		"source_width": width,
		"source_height": height,
		"crop": {"left": left, "top": top, "side": side,
			"zoom": window.get("zoom", 1.0), "anchor": window.get("anchor", "top")},
		"size": shipped,
		"requested_size": size,
		"face": face,
		# Informational: where the subject's skin tones sit in the source (a
		# heuristic, reported so a crop can be judged without opening the file).
		"skin_box": skin,
	}


## The square of the source that becomes the avatar.
##
## ``face`` (the default) measures the subject first: the topmost substantial
## run of skin tones is the brow/forehead, the widest run in the band just below
## it is the face, and the window is sized so that face lands at
## ``FACE_WIDTH_RANGE`` and the brow at ``BROW_AT`` -- a head-and-shoulders bust
## with hair room above. This is a hint, not a promise: painted backgrounds can
## read as skin (warm rock, blossom, lamplight), and the subjects themselves can
## be too desaturated to detect. A source the detector misses falls back to the
## plain top crop, which is why the anchor comes back in the result -- and why
## ``zoom``/``top`` exist, so a stubborn painting is framed by hand and the
## manifest records exactly what was shipped.
func _crop_window(image: Image, item: Dictionary) -> Dictionary:
	var width := image.get_width()
	var height := image.get_height()
	var short := mini(width, height)
	var anchor := str(item.get("anchor", "face"))
	var zoom := clampf(float(item.get("zoom", 1.0)), 0.15, 1.0)
	var head := _head_box(image)

	var side := int(round(float(short) * zoom))
	var left := int((width - side) / 2.0)
	var top := int((height - side) / 2.0) if anchor == "center" else 0
	if anchor == "face" and not head.is_empty():
		var face_width := float(head["right"]) - float(head["left"])
		side = int(round(face_width / FACE_WIDTH_RANGE.x))
		side = maxi(side, int(round(float(short) * MIN_SIDE_FRACTION)))
		left = int(round((float(head["left"]) + float(head["right"])) / 2.0 - float(side) / 2.0))
		top = int(round(float(head["top"]) - float(side) * BROW_AT))
	else:
		anchor = "center" if anchor == "center" else "top"

	side = clampi(side, 8, short)
	left = clampi(left, 0, width - side)
	top = clampi(top + int(round(height * float(item.get("top", 0.0)))), 0, height - side)
	return {"left": left, "top": top, "side": side, "zoom": zoom, "anchor": anchor, "head": head}


## The topmost skin cluster: the forehead the crop hangs off.
##
## Two guards keep this from latching onto scenery. A run counts as skin only
## when it is wide enough to be a face (``min_run_fraction`` of the width) -- a
## rock fleck, a red seal or a blossom petal is a few stray pixels, not a face.
## And scanning stops at ``bottom_fraction`` of the height, because below a bust
## the skin tones stop being a face (bare shoulders, a hand on a sword), and a
## box around those would frame a torso instead of a head. A painting whose
## tones the detector misses entirely is not a failure: it ships as a top crop,
## and the operator frames it explicitly with ``zoom``/``top``.
func _head_box(image: Image, bottom_fraction: float = 0.55, min_run_fraction: float = 0.03) -> Dictionary:
	var width := image.get_width()
	var height := image.get_height()
	var step := maxi(1, int(minf(width, height) / 384.0))
	var limit := int(height * bottom_fraction)
	var min_run := maxi(4, int(width * min_run_fraction))
	var brow := -1
	var y := 0
	while y < limit:
		var run := _skin_run(image, y, step)
		if not run.is_empty() and int(run["right"]) - int(run["left"]) + 1 >= min_run:
			brow = y
			break
		y += step
	if brow < 0:
		return {}

	# A band below the brow holds the widest part of the face (eyes, cheeks);
	# it is deliberately short so a long neck or bare chest cannot widen it.
	var band := mini(limit, brow + maxi(step, int(height * 0.05)))
	var left := width
	var right := -1
	var bottom := brow
	var scan := brow
	while scan <= band:
		var run := _skin_run(image, scan, step)
		if not run.is_empty() and int(run["right"]) - int(run["left"]) + 1 >= min_run:
			left = mini(left, int(run["left"]))
			right = maxi(right, int(run["right"]))
			bottom = scan
		scan += step
	if right < 0:
		return {}
	return {"top": brow, "bottom": bottom, "left": left, "right": right}


## Horizontal extent of skin-toned pixels on one row, or ``{}`` if there is none.
func _skin_run(image: Image, y: int, step: int) -> Dictionary:
	var left := -1
	var right := -1
	var x := 0
	while x < image.get_width():
		if _is_skin(image.get_pixel(x, y)):
			if left < 0:
				left = x
			right = x
		x += step
	if right < 0:
		return {}
	return {"left": left, "right": right}


## Rough portrait checker: the bounding box of skin-toned pixels, as fractions
## of the image. Reported (never acted on) so a crop can be judged from the job
## output; it is a heuristic on the source art, so a miss costs nothing.
func _skin_box(image: Image, from_fraction: float, to_fraction: float) -> Dictionary:
	var width := image.get_width()
	var height := image.get_height()
	var y0 := int(height * from_fraction)
	var y1 := int(height * to_fraction)
	var step := maxi(1, int(minf(width, height) / 256.0))
	var top := -1
	var bottom := -1
	var left := width
	var right := -1
	var y := y0
	while y < y1:
		var x := 0
		while x < width:
			if _is_skin(image.get_pixel(x, y)):
				top = y if top < 0 else top
				bottom = y
				left = mini(left, x)
				right = maxi(right, x)
			x += step
		y += step
	if top < 0:
		return {}
	return {
		"top": float(top) / float(height),
		"bottom": float(bottom) / float(height),
		"left": float(left) / float(width),
		"right": float(right) / float(width),
	}


func _is_skin(colour: Color) -> bool:
	var r := colour.r
	var g := colour.g
	var b := colour.b
	if r < 0.32 or r > 1.0:
		return false
	if r <= g or g <= b:
		return false
	var warm := (r - b) / maxf(0.0001, r)
	return warm > 0.12 and warm < 0.62 and (r - g) / maxf(0.0001, r) < 0.34
