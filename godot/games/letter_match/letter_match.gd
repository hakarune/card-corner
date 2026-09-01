extends GameScreen
## Letter Match screen: solo, no AI, no win/lose framing -- gentle
## reinforcement on a match, no-penalty retry on a miss. Ported from
## legacy/games/letter_match/screen.py.

const RESOLVE_PAUSE := 0.7
const GRID_COLS := 4
const MODE_MESSAGES := {
	"letters": "Match each big letter to its little letter!",
	"animals": "Match each animal to its starting letter!",
}

@export var mode := "letters"

var _game: LetterMatchGame
var _msg := ""
var _locked := false
var _timer := 0.0
var _pending := Callable()
var _elapsed := 0.0

var _title: Label
var _time_label: Label
var _msg_label: Label
var _board_host := Control.new()
var _tiles: Array[CardView] = []
var _modal: Panel
var _modal_label: Label


func _ready() -> void:
	super._ready()
	var cfg := CCRouter.consume()
	mode = cfg.get("mode", "letters")
	_build_ui()
	_start_game()


func _start_game() -> void:
	_game = LetterMatchGame.new(LetterMatchGame.DEFAULT_LETTER_COUNT, -1, mode)
	_msg = MODE_MESSAGES[mode]
	_locked = false
	_pending = Callable()
	_elapsed = 0.0
	_modal.visible = false
	set_process(true)
	_build_board()
	_refresh()


func _schedule(delay: float, cb: Callable) -> void:
	_timer = delay
	_pending = cb
	_locked = true


func _on_tile_clicked(view: CardView) -> void:
	if _locked or _game.game_over:
		return
	var pos: int = view.get_meta("pos")
	var result := _game.click(pos)
	if not result.accepted:
		return
	if result.pos2 == -1:
		CCAudio.play_sfx("card_select")
		_refresh()
		return

	if result.matched:
		_msg = "Great match!"
		CCAudio.play_sfx("match")
		_refresh()
		if _game.game_over:
			_locked = true
			_schedule(0.6, _on_complete)
	else:
		_msg = "Not quite — try again!"
		CCAudio.play_sfx("miss")
		_refresh()
		_schedule(RESOLVE_PAUSE, func():
			_msg = MODE_MESSAGES[mode]
			_refresh())


func _on_complete() -> void:
	_msg = "All done! Accuracy: %d%%" % round(_game.accuracy() * 100.0)
	CCAudio.play_sfx("win")
	_modal_label.text = _msg
	_modal.visible = true
	set_process(false)


func _process(delta: float) -> void:
	if not _game.game_over:
		_elapsed += delta
		_time_label.text = "Time: %ds" % int(_elapsed)
	if _pending.is_valid():
		_timer -= delta
		if _timer <= 0.0:
			var cb := _pending
			_pending = Callable()
			_locked = false
			cb.call()


func _refresh() -> void:
	_msg_label.text = _msg
	var color: Color = ThemeData.GAME_COLORS["letter_match"]
	for i in _tiles.size():
		var v := _tiles[i]
		var selected: bool = (i == _game.pending_first())
		if _game.matched.has(i):
			v.accent = ThemeData.SUCCESS
		elif selected:
			v.accent = ThemeData.ACCENT
		else:
			v.accent = color
		v.set_highlighted(selected)
		v.queue_redraw()


func _build_board() -> void:
	for c in _board_host.get_children():
		c.queue_free()
	_tiles.clear()
	var n := _game.board.size()
	var tile := 118.0
	var gap := 16.0
	var grid_w := GRID_COLS * tile + (GRID_COLS - 1) * gap
	var start_x := (ThemeData.WINDOW_SIZE.x - grid_w) * 0.5
	var color: Color = ThemeData.GAME_COLORS["letter_match"]
	for pos in n:
		var t: LetterMatchGame.Tile = _game.board[pos]
		var col := pos % GRID_COLS
		var row := pos / GRID_COLS
		var v := CardView.new()
		v.size = Vector2(tile, tile)
		v.position = Vector2(start_x + col * (tile + gap), row * (tile + gap))
		v.set_meta("pos", pos)
		if t.is_animal:
			v.setup_letter(CardView.Mode.ANIMAL, "", t.letter, color)
		else:
			v.setup_letter(CardView.Mode.LETTER, t.display(), "", color)
		v.clicked.connect(_on_tile_clicked)
		_board_host.add_child(v)
		_tiles.append(v)


func _build_ui() -> void:
	var bg := ColorRect.new()
	bg.color = ThemeData.BACKGROUND
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)

	_title = _mk_label("Letter Match", Vector2(30, 18), 40, ThemeData.TEXT_DARK)
	_time_label = _mk_label("Time: 0s", Vector2(ThemeData.WINDOW_SIZE.x - 260, 34), 28, ThemeData.TEXT_DARK)

	var msg_panel := Panel.new()
	msg_panel.position = Vector2(60, 108)
	msg_panel.size = Vector2(ThemeData.WINDOW_SIZE.x - 120, 66)
	msg_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(msg_panel)
	_msg_label = Label.new()
	_msg_label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_msg_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_msg_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_msg_label.add_theme_font_size_override("font_size", 24)
	_msg_label.add_theme_color_override("font_color", ThemeData.TEXT_DARK)
	msg_panel.add_child(_msg_label)

	_board_host.position = Vector2(0, 196)
	_board_host.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_board_host)

	var menu_btn := Button.new()
	menu_btn.text = "Menu"
	menu_btn.position = Vector2(24, ThemeData.WINDOW_SIZE.y - 52)
	menu_btn.size = Vector2(96, 40)
	menu_btn.focus_mode = Control.FOCUS_NONE
	menu_btn.pressed.connect(func(): CCRouter.goto_menu())
	add_child(menu_btn)

	_modal = Panel.new()
	_modal.size = Vector2(680, 260)
	_modal.position = (Vector2(ThemeData.WINDOW_SIZE) - _modal.size) * 0.5
	_modal.visible = false
	add_child(_modal)
	_modal_label = Label.new()
	_modal_label.position = Vector2(20, 56)
	_modal_label.size = Vector2(640, 60)
	_modal_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_modal_label.add_theme_font_size_override("font_size", 26)
	_modal_label.add_theme_color_override("font_color", ThemeData.TEXT_DARK)
	_modal.add_child(_modal_label)
	var again := Button.new()
	again.text = "Play Again"
	again.size = Vector2(200, ThemeData.MIN_TOUCH_TARGET)
	again.position = Vector2(120, 160)
	again.pressed.connect(_start_game)
	_modal.add_child(again)
	var to_menu := Button.new()
	to_menu.text = "Menu"
	to_menu.size = Vector2(200, ThemeData.MIN_TOUCH_TARGET)
	to_menu.position = Vector2(360, 160)
	to_menu.pressed.connect(func(): CCRouter.goto_menu())
	_modal.add_child(to_menu)


func _mk_label(txt: String, pos: Vector2, px: int, color: Color) -> Label:
	var l := Label.new()
	l.text = txt
	l.position = pos
	l.add_theme_font_size_override("font_size", px)
	l.add_theme_color_override("font_color", color)
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(l)
	return l
