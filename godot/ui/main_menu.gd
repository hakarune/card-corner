extends Control
## Main menu: pick one of the four games. Ported from LauncherScreen
## (legacy/ui/launcher.py). Icons + color coding lead; label underneath.
## (Update-check UI is intentionally not ported -- deferred; the legacy
## procedural launcher-icon fallbacks aren't ported either since real
## launcher art exists at res://assets/icons/launcher/.)

const GAMES := [
	{"key": "go_fish", "label": "Go Fish"},
	{"key": "old_maid", "label": "Old Maid"},
	{"key": "memory", "label": "Memory"},
	{"key": "letter_match", "label": "Letter Match"},
]

const TILE_W := 420.0
const TILE_H := 220.0
const GAP := 40.0


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	CCRouter.consume()  # defensive: never inherit stale routing config
	_build()
	CCAudio.start_music()


func _build() -> void:
	var bg := ColorRect.new()
	bg.color = ThemeData.BACKGROUND
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)

	_center_label("Card Corner", 90, 64, ThemeData.TEXT_DARK)
	_center_label("Pick a game to play!", 145, 28, ThemeData.TEXT_MUTED)

	var grid_w := 2 * TILE_W + GAP
	var start_x := (ThemeData.WINDOW_SIZE.x - grid_w) * 0.5
	var start_y := 190.0

	for i in GAMES.size():
		var g: Dictionary = GAMES[i]
		var col := i % 2
		var row := i / 2
		var pos := Vector2(start_x + col * (TILE_W + GAP), start_y + row * (TILE_H + GAP))

		var btn := Button.new()
		btn.position = pos
		btn.size = Vector2(TILE_W, TILE_H)
		btn.focus_mode = Control.FOCUS_NONE
		var sb := StyleBoxFlat.new()
		sb.bg_color = ThemeData.GAME_COLORS[g["key"]]
		sb.set_corner_radius_all(20)
		sb.set_border_width_all(3)
		sb.border_color = ThemeData.TEXT_DARK
		btn.add_theme_stylebox_override("normal", sb)
		btn.add_theme_stylebox_override("hover", sb)
		btn.add_theme_stylebox_override("pressed", sb)
		btn.pressed.connect(_select.bind(g["key"]))
		add_child(btn)

		var art := _launcher_art(g["key"])
		if art != null:
			var tr := TextureRect.new()
			tr.texture = art
			tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
			tr.position = pos + Vector2(20, 10)
			tr.size = Vector2(TILE_W - 40, TILE_H - 90)
			tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
			add_child(tr)

		var lbl := Label.new()
		lbl.text = g["label"]
		lbl.position = pos + Vector2(0, TILE_H - 56)
		lbl.size = Vector2(TILE_W, 40)
		lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lbl.add_theme_font_size_override("font_size", 34)
		lbl.add_theme_color_override("font_color", ThemeData.TEXT_LIGHT)
		lbl.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(lbl)

	_build_toggles()


func _build_toggles() -> void:
	var s := float(ThemeData.MIN_TOUCH_TARGET)
	var full := Button.new()
	full.text = "⛶"
	full.position = Vector2(ThemeData.WINDOW_SIZE.x - s - 24, 24)
	full.size = Vector2(s, s)
	full.focus_mode = Control.FOCUS_NONE
	full.pressed.connect(_toggle_fullscreen)
	add_child(full)

	var mute := Button.new()
	mute.text = "🔇" if CCAudio.muted else "🔊"
	mute.position = Vector2(ThemeData.WINDOW_SIZE.x - 2 * s - 40, 24)
	mute.size = Vector2(s, s)
	mute.focus_mode = Control.FOCUS_NONE
	mute.pressed.connect(func():
		CCAudio.set_muted(not CCAudio.muted)
		mute.text = "🔇" if CCAudio.muted else "🔊")
	add_child(mute)


func _center_label(txt: String, y: float, px: int, color: Color) -> void:
	var l := Label.new()
	l.text = txt
	l.position = Vector2(0, y)
	l.size = Vector2(ThemeData.WINDOW_SIZE.x, px + 8)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.add_theme_font_size_override("font_size", px)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(l)


func _launcher_art(key: String) -> Texture2D:
	for ext in ["png", "svg", "jpg"]:
		var p := "res://assets/icons/launcher/%s.%s" % [key, ext]
		if ResourceLoader.exists(p):
			return load(p)
	return null


func _toggle_fullscreen() -> void:
	var m := DisplayServer.window_get_mode()
	if m == DisplayServer.WINDOW_MODE_FULLSCREEN or m == DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_WINDOWED)
	else:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN)


func _select(key: String) -> void:
	CCAudio.play_sfx("button")
	CCRouter.goto_difficulty(key)
