extends Control
## Main menu: pick one of the four games. Ported from LauncherScreen
## (legacy/ui/launcher.py). The launcher icons carry the game identity now,
## so tiles are a clean white card with a thin game-colour accent border --
## no solid colour fill behind the icon.
## (Update-check UI is intentionally not ported -- deferred.)

const GAMES := [
	{"key": "go_fish", "label": "Go Fish"},
	{"key": "old_maid", "label": "Old Maid"},
	{"key": "memory", "label": "Memory"},
	{"key": "letter_match", "label": "Letter Match"},
]

const TILE_W := 420.0
const TILE_H := 220.0
const GAP := 44.0

var _mute_btn: MenuToggle
var _full_btn: MenuToggle


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

	_center_label("Card Corner", 40, 58, ThemeData.TEXT_DARK)
	_center_label("Pick a game to play!", 108, 26, ThemeData.TEXT_MUTED)

	var grid_w := 2 * TILE_W + GAP
	var start_x := (ThemeData.WINDOW_SIZE.x - grid_w) * 0.5
	var start_y := 168.0

	for i in GAMES.size():
		var g: Dictionary = GAMES[i]
		var col := i % 2
		var row := i / 2
		var pos := Vector2(start_x + col * (TILE_W + GAP), start_y + row * (TILE_H + GAP))
		var accent: Color = ThemeData.GAME_COLORS[g["key"]]

		var btn := Button.new()
		btn.position = pos
		btn.size = Vector2(TILE_W, TILE_H)
		btn.focus_mode = Control.FOCUS_NONE
		var normal := _tile_box(accent, false)
		btn.add_theme_stylebox_override("normal", normal)
		btn.add_theme_stylebox_override("disabled", normal)
		btn.add_theme_stylebox_override("hover", _tile_box(accent, true))
		btn.add_theme_stylebox_override("pressed", _tile_box(accent, true))
		btn.pressed.connect(_select.bind(g["key"]))
		add_child(btn)

		var art := _launcher_art(g["key"])
		if art != null:
			var tr := TextureRect.new()
			tr.texture = art
			tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
			# EXPAND_IGNORE_SIZE: without this the 512px source sets the rect's
			# minimum size, so `size` below is ignored and the art spills out of
			# the tile, over its neighbours and the label. Clip as a backstop.
			tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			tr.clip_contents = true
			tr.position = pos + Vector2(16, 12)
			tr.size = Vector2(TILE_W - 32, TILE_H - 78)
			tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
			add_child(tr)

		var lbl := Label.new()
		lbl.text = g["label"]
		lbl.position = pos + Vector2(0, TILE_H - 56)
		lbl.size = Vector2(TILE_W, 44)
		lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lbl.add_theme_font_size_override("font_size", 32)
		lbl.add_theme_color_override("font_color", ThemeData.TEXT_DARK)
		lbl.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(lbl)

	_build_toggles()


func _tile_box(accent: Color, hovered: bool) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = ThemeData.PANEL if not hovered else accent.lerp(ThemeData.PANEL, 0.82)
	sb.set_corner_radius_all(22)
	sb.set_border_width_all(4)
	sb.border_color = accent
	sb.shadow_color = Color(0, 0, 0, 0.12)
	sb.shadow_size = 6
	sb.shadow_offset = Vector2(0, 3)
	return sb


func _build_toggles() -> void:
	var s := 64.0
	_full_btn = MenuToggle.new()
	_full_btn.kind = "fullscreen"
	_full_btn.position = Vector2(ThemeData.WINDOW_SIZE.x - s - 24, 24)
	_full_btn.size = Vector2(s, s)
	_full_btn.pressed.connect(_toggle_fullscreen)
	add_child(_full_btn)

	_mute_btn = MenuToggle.new()
	_mute_btn.kind = "mute"
	_mute_btn.position = Vector2(ThemeData.WINDOW_SIZE.x - 2 * s - 40, 24)
	_mute_btn.size = Vector2(s, s)
	_mute_btn.set_active(CCAudio.muted)
	_mute_btn.pressed.connect(func():
		CCAudio.set_muted(not CCAudio.muted)
		_mute_btn.set_active(CCAudio.muted))
	add_child(_mute_btn)


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
	var fs := m == DisplayServer.WINDOW_MODE_FULLSCREEN or m == DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN
	DisplayServer.window_set_mode(
		DisplayServer.WINDOW_MODE_WINDOWED if fs else DisplayServer.WINDOW_MODE_FULLSCREEN)
	_full_btn.set_active(not fs)


func _select(key: String) -> void:
	CCAudio.play_sfx("button")
	CCRouter.goto_difficulty(key)
