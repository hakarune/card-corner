extends Control
## Main menu: pick one of the four games. Ported from LauncherScreen
## (legacy/ui/launcher.py). The launcher art IS the button now -- no white
## card, no border box at rest. Each tile shows the game's illustration at
## full size with its name in a marker font overlapping the lower edge; a
## faint game-colour glow appears on hover/press.
## (Update-check UI is intentionally not ported -- deferred.)

const GAMES := [
	{"key": "go_fish", "label": "Go Fish"},
	{"key": "old_maid", "label": "Old Maid"},
	{"key": "memory", "label": "Memory"},
	{"key": "letter_match", "label": "Letter Match"},
]

## The four tiles fill a 2x2 grid between GRID_TOP and GRID_BOTTOM, centred
## horizontally. Cells never overlap: a gutter of GUTTER_PCT * cell-size
## sits between them on both axes. CELL_ASPECT is tuned to the illustration
## panels so KEEP_ASPECT_COVERED shows them whole with only a hair of crop.
const GRID_TOP := 150.0
const GRID_BOTTOM := 700.0
const CELL_ASPECT := 1.30
const GUTTER_PCT := 0.05
const LABEL_H := 58.0

const LABEL_FONT_PATH := "res://assets/fonts/PermanentMarker-Regular.ttf"

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

	# Solve cell + gutter so 2 cells + 1 gutter exactly span the grid box,
	# with gutter = GUTTER_PCT of the cell on each axis.
	var cell_h := (GRID_BOTTOM - GRID_TOP) / (2.0 + GUTTER_PCT)
	var gutter_y := cell_h * GUTTER_PCT
	var cell_w := cell_h * CELL_ASPECT
	var gutter_x := cell_w * GUTTER_PCT
	var grid_w := 2.0 * cell_w + gutter_x
	var start_x := (ThemeData.WINDOW_SIZE.x - grid_w) * 0.5
	var label_font := _label_font()

	for i in GAMES.size():
		var g: Dictionary = GAMES[i]
		var col := i % 2
		var row := i / 2
		var pos := Vector2(
			start_x + col * (cell_w + gutter_x),
			GRID_TOP + row * (cell_h + gutter_y))
		var accent: Color = ThemeData.GAME_COLORS[g["key"]]

		var btn := Button.new()
		btn.position = pos
		btn.size = Vector2(cell_w, cell_h)
		btn.focus_mode = Control.FOCUS_NONE
		var empty := StyleBoxEmpty.new()
		btn.add_theme_stylebox_override("normal", empty)
		btn.add_theme_stylebox_override("disabled", empty)
		btn.add_theme_stylebox_override("hover", _hover_box(accent))
		btn.add_theme_stylebox_override("pressed", _hover_box(accent))
		btn.pressed.connect(_select.bind(g["key"]))
		add_child(btn)

		var art := _launcher_art(g["key"])
		if art != null:
			var tr := TextureRect.new()
			tr.texture = art
			# COVERED fills the tile and crops the art's transparent padding, so
			# the rounded illustration panel reads edge-to-edge like the mock-up.
			tr.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_COVERED
			# EXPAND_IGNORE_SIZE: without this the 512px source sets the rect's
			# minimum size, so `size` below is ignored and the art spills out of
			# the tile, over its neighbours and the label. Clip as a backstop.
			tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
			tr.clip_contents = true
			tr.position = pos
			tr.size = Vector2(cell_w, cell_h)
			tr.mouse_filter = Control.MOUSE_FILTER_IGNORE
			add_child(tr)

		var lbl := Label.new()
		lbl.text = g["label"]
		lbl.position = pos + Vector2(0, cell_h - LABEL_H - 4)
		lbl.size = Vector2(cell_w, LABEL_H)
		lbl.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		lbl.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		if label_font != null:
			lbl.add_theme_font_override("font", label_font)
		lbl.add_theme_font_size_override("font_size", 44)
		lbl.add_theme_color_override("font_color", Color.BLACK)
		# white sticker halo -- keeps the name readable over busy art
		lbl.add_theme_color_override("font_outline_color", ThemeData.PANEL)
		lbl.add_theme_constant_override("outline_size", 8)
		lbl.mouse_filter = Control.MOUSE_FILTER_IGNORE
		add_child(lbl)

	_build_toggles()


func _hover_box(accent: Color) -> StyleBoxFlat:
	var sb := StyleBoxFlat.new()
	sb.bg_color = Color(accent.r, accent.g, accent.b, 0.12)
	sb.set_corner_radius_all(28)
	sb.set_border_width_all(4)
	sb.border_color = accent
	return sb


func _label_font() -> Font:
	if ResourceLoader.exists(LABEL_FONT_PATH):
		return load(LABEL_FONT_PATH)
	return null


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
