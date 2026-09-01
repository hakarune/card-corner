extends GameScreen
## Memory screen: human ("You") vs one AI ("Fox"), or solo "Play Alone".
## Ported from legacy/games/memory/screen.py. The screen's own `_visible`
## set is the source of truth for what's face-up, so a match can be staged
## reveal-pause-reveal-pause for readability without desyncing the engine.

const AI_NAME := "Fox"
const HUMAN_NAME := "You"
const AI_TURN_DELAY := 0.7
const REVEAL_GAP := 0.7
const RESOLVE_PAUSE := 0.9
const NUM_PAIRS := 6
const GRID_COLS := 4

@export var difficulty: int = AIStrategy.Difficulty.EASY
@export var solo := false

var _game: MemoryGame
var _theme: CardTheme
var _msg := "Flip two cards to find a match!"
var _elapsed := 0.0
var _moves := 0
var _visible := {}                ## set of board positions the screen shows face-up
var _human_first := -1
var _locked := false
var _timer := 0.0
var _pending := Callable()

var _title: Label
var _subtitle: Label
var _stats_label: Label
var _msg_label: Label
var _board_host := Control.new()
var _tiles: Array[CardView] = []
var _modal: Panel
var _modal_label: Label


func _ready() -> void:
	super._ready()
	var cfg := CCRouter.consume()
	if cfg.get("solo", false):
		solo = true
	elif cfg.has("difficulty"):
		difficulty = cfg["difficulty"]
	_theme = ThemeData.card_theme("memory")
	_build_ui()
	_start_game()


func _start_game() -> void:
	if solo:
		_game = MemoryGame.new([HUMAN_NAME], NUM_PAIRS)
	else:
		_game = MemoryGame.new([HUMAN_NAME, AI_NAME], NUM_PAIRS, {AI_NAME: difficulty})
	_msg = "Flip two cards to find a match!"
	_elapsed = 0.0
	_moves = 0
	_visible.clear()
	_human_first = -1
	_locked = false
	_pending = Callable()
	_modal.visible = false
	set_process(true)
	_build_board()
	_maybe_start_ai_turn()
	_refresh()


func _schedule(delay: float, cb: Callable) -> void:
	_timer = delay
	_pending = cb
	_locked = true


func _maybe_start_ai_turn() -> void:
	if _game.game_over:
		_on_game_over()
		return
	if _game.is_ai_turn():
		_schedule(AI_TURN_DELAY, _run_ai_turn)


var _ai_result: MemoryFlip.Result = null


func _run_ai_turn() -> void:
	_ai_result = _game.take_ai_turn()
	if _ai_result == null:
		_maybe_start_ai_turn()
		return
	_visible[_ai_result.pos1] = true
	CCAudio.play_sfx("card_move")
	_refresh()
	_schedule(REVEAL_GAP, _ai_reveal_second)


func _ai_reveal_second() -> void:
	_visible[_ai_result.pos2] = true
	CCAudio.play_sfx("card_move")
	_refresh()
	_schedule(RESOLVE_PAUSE, _ai_resolve)


func _ai_resolve() -> void:
	if _ai_result.matched:
		_msg = "%s found a match!" % AI_NAME
		CCAudio.play_sfx("match")
	else:
		_visible.erase(_ai_result.pos1)
		_visible.erase(_ai_result.pos2)
		_msg = "%s didn't find a match." % AI_NAME
		CCAudio.play_sfx("miss")
	_maybe_start_ai_turn()
	_refresh()


func _on_tile_clicked(view: CardView) -> void:
	var pos: int = view.get_meta("pos")
	if _locked or _game.game_over or _game.is_ai_turn():
		return
	if _game.matched.has(pos) or _visible.has(pos):
		return

	if _human_first == -1:
		_human_first = pos
		_visible[pos] = true
		CCAudio.play_sfx("card_select")
		_refresh()
		return
	if pos == _human_first:
		return

	var first := _human_first
	_human_first = -1
	_visible[pos] = true
	CCAudio.play_sfx("card_select")
	var result := _game.flip_two(HUMAN_NAME, first, pos)
	if solo:
		_moves += 1
	if result != null and result.matched:
		_msg = "Match! Go again."
		CCAudio.play_sfx("match")
		_refresh()
		_maybe_start_ai_turn()
	else:
		_msg = "No match this time — try again!"
		CCAudio.play_sfx("miss")
		_refresh()
		_schedule(RESOLVE_PAUSE, func():
			_visible.erase(first)
			_visible.erase(pos)
			_msg = "Flip two cards to find a match!"
			_maybe_start_ai_turn()
			_refresh())


func _on_game_over() -> void:
	if solo:
		var mm := int(_elapsed) / 60
		var ss := int(_elapsed) % 60
		_msg = "All pairs found! Time %d:%02d — Moves: %d" % [mm, ss, _moves]
		CCAudio.play_sfx("win")
	else:
		var hs: int = _game.players[HUMAN_NAME].score
		var as_: int = _game.players[AI_NAME].score
		if hs > as_:
			_msg = "You win, %d to %d!" % [hs, as_]
			CCAudio.play_sfx("win")
		elif as_ > hs:
			_msg = "%s wins, %d to %d. Play again?" % [AI_NAME, as_, hs]
			CCAudio.play_sfx("loss")
		else:
			_msg = "It's a tie, %d to %d!" % [hs, as_]
	_modal_label.text = _msg
	_modal.visible = true
	set_process(false)


func _process(delta: float) -> void:
	if solo and not _game.game_over:
		_elapsed += delta
		_refresh_stats()
	if _pending.is_valid():
		_timer -= delta
		if _timer <= 0.0:
			var cb := _pending
			_pending = Callable()
			_locked = false
			cb.call()


func _refresh_stats() -> void:
	if solo:
		_stats_label.text = "Time %d:%02d    Moves %d" % [int(_elapsed) / 60, int(_elapsed) % 60, _moves]
	else:
		_stats_label.text = "You: %d    %s: %d" % [
			_game.players[HUMAN_NAME].score, AI_NAME, _game.players[AI_NAME].score]


func _refresh() -> void:
	_subtitle.text = ("Playing alone — find all the pairs!" if solo
		else "Playing against %s (%s)" % [AI_NAME, AIStrategy.DIFFICULTY_LABELS[difficulty]])
	_msg_label.text = _msg
	_refresh_stats()
	for i in _tiles.size():
		var v := _tiles[i]
		var face_up: bool = _visible.has(i) or _game.matched.has(i)
		v.face_down = not face_up
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
	for pos in n:
		var col := pos % GRID_COLS
		var row := pos / GRID_COLS
		var v := CardView.new()
		v.size = Vector2(tile, tile)
		v.position = Vector2(start_x + col * (tile + gap), row * (tile + gap))
		v.set_meta("pos", pos)
		v.setup(CardView.Mode.ITEM_FACE, _theme, _game.board[pos])
		v.face_down = true
		v.clicked.connect(_on_tile_clicked)
		_board_host.add_child(v)
		_tiles.append(v)


func _build_ui() -> void:
	var bg := ColorRect.new()
	bg.color = ThemeData.BACKGROUND
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)

	_title = _mk_label("Memory", Vector2(30, 18), 40, ThemeData.TEXT_DARK)
	_subtitle = _mk_label("", Vector2(30, 70), 22, ThemeData.TEXT_MUTED)
	_stats_label = _mk_label("", Vector2(ThemeData.WINDOW_SIZE.x - 380, 36), 26, ThemeData.TEXT_DARK)

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
	_modal.size = Vector2(680, 280)
	_modal.position = (Vector2(ThemeData.WINDOW_SIZE) - _modal.size) * 0.5
	_modal.visible = false
	add_child(_modal)
	_modal_label = Label.new()
	_modal_label.position = Vector2(20, 60)
	_modal_label.size = Vector2(640, 80)
	_modal_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_modal_label.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_modal_label.add_theme_font_size_override("font_size", 26)
	_modal_label.add_theme_color_override("font_color", ThemeData.TEXT_DARK)
	_modal.add_child(_modal_label)
	var again := Button.new()
	again.text = "Play Again"
	again.size = Vector2(200, ThemeData.MIN_TOUCH_TARGET)
	again.position = Vector2(120, 180)
	again.pressed.connect(_start_game)
	_modal.add_child(again)
	var to_menu := Button.new()
	to_menu.text = "Menu"
	to_menu.size = Vector2(200, ThemeData.MIN_TOUCH_TARGET)
	to_menu.position = Vector2(360, 180)
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
