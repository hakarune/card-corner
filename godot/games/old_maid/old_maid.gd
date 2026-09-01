extends GameScreen
## Old Maid screen: human ("You") vs one AI ("Fox"). The loser is framed
## lightly and positively. Ported from legacy/games/old_maid/screen.py.

const AI_NAME := "Fox"
const HUMAN_NAME := "You"
const AI_TURN_DELAY := 0.9

@export var difficulty: int = AIStrategy.Difficulty.EASY

var _game: OldMaidGame
var _theme: CardTheme
var _msg := ""
var _waiting_for_ai := false
var _ai_timer := 0.0

var _title: Label
var _subtitle: Label
var _ai_count_label: Label
var _ai_pairs_label: Label
var _ai_backs := Control.new()
var _msg_label: Label
var _your_label: Label
var _hand_host := Control.new()
var _hand_views: Array[CardView] = []
var _draw_btn: Button
var _modal: Panel
var _modal_label: Label


func _ready() -> void:
	super._ready()
	var cfg := CCRouter.consume()
	if cfg.has("difficulty"):
		difficulty = cfg["difficulty"]
	_theme = ThemeData.card_theme("old_maid")
	_build_ui()
	_start_game()


func _start_game() -> void:
	_game = OldMaidGame.new([HUMAN_NAME, AI_NAME], {AI_NAME: difficulty})
	_msg = "Draw a card from %s's hand — click the pile!" % AI_NAME
	_waiting_for_ai = false
	_modal.visible = false
	set_process(true)
	CCAudio.play_sfx("card_move")
	_maybe_start_ai_turn()
	_refresh()


func _maybe_start_ai_turn() -> void:
	if _game.game_over:
		_on_game_over()
		return
	if _game.is_ai_turn():
		_waiting_for_ai = true
		_ai_timer = AI_TURN_DELAY
		_msg = "%s is picking a card from your hand..." % AI_NAME


func _run_ai_turn() -> void:
	var result := _game.draw(AI_NAME, HUMAN_NAME)
	_waiting_for_ai = false
	CCAudio.play_sfx("card_move")
	if result != null and not result.paired_ranks.is_empty():
		_msg = "%s drew a match! Pair set aside." % AI_NAME
		CCAudio.play_sfx("match")
	else:
		_msg = "%s drew a card — no match yet." % AI_NAME
		CCAudio.play_sfx("miss")
	_maybe_start_ai_turn()
	_refresh()


func _human_draw() -> void:
	if _game.game_over or _game.is_ai_turn() or _waiting_for_ai:
		return
	if _game.players[AI_NAME].hand.is_empty():
		return
	CCAudio.play_sfx("card_select")
	var result := _game.draw(HUMAN_NAME, AI_NAME)
	if result != null and not result.paired_ranks.is_empty():
		_msg = "You got a match! Nicely done."
		CCAudio.play_sfx("match")
	else:
		_msg = "No match this time — your turn is over."
		CCAudio.play_sfx("miss")
	_maybe_start_ai_turn()
	_refresh()


func _on_game_over() -> void:
	if _game.loser == HUMAN_NAME:
		_msg = "You lost this round — %s got away with it! Try again?" % AI_NAME
		CCAudio.play_sfx("loss")
	elif _game.loser == AI_NAME:
		_msg = "You win! %s got stuck with the Old Maid!" % AI_NAME
		CCAudio.play_sfx("win")
	else:
		_msg = "Good game!"
	_modal_label.text = _msg
	_modal.visible = true
	set_process(false)


func _process(delta: float) -> void:
	if _waiting_for_ai:
		_ai_timer -= delta
		if _ai_timer <= 0.0:
			_run_ai_turn()


func _refresh() -> void:
	var ai: Player = _game.players[AI_NAME]
	var you: Player = _game.players[HUMAN_NAME]
	var can_draw: bool = not _game.game_over and not _game.is_ai_turn() and not _waiting_for_ai and not ai.hand.is_empty()
	_subtitle.text = "Playing against %s (%s)" % [AI_NAME, AIStrategy.DIFFICULTY_LABELS[difficulty]]
	_ai_count_label.text = "%s's hand: %d cards" % [AI_NAME, ai.hand.size()]
	_ai_pairs_label.text = "Pairs found: %d" % ai.books.size()
	_msg_label.text = _msg
	_your_label.text = "Your hand — pairs found: %d" % you.books.size()
	_draw_btn.disabled = not can_draw
	_draw_btn.text = "Draw from %s" % AI_NAME if can_draw else "Wait…"

	for c in _ai_backs.get_children():
		c.queue_free()
	var count := ai.hand.size()
	var gap: float = clampf((ThemeData.WINDOW_SIZE.x - 60.0 - 70.0) / max(count, 1), 30.0, 50.0)
	for i in count:
		var v := CardView.new()
		v.size = Vector2(70, 100)
		v.position = Vector2(i * gap, 0)
		v.setup(CardView.Mode.BACK, _theme)
		v.set_highlighted(can_draw)
		v.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_ai_backs.add_child(v)

	for v in _hand_views:
		v.queue_free()
	_hand_views.clear()
	var cards := you.hand.cards
	var hgap: float = clampf((ThemeData.WINDOW_SIZE.x - 60.0 - 90.0) / max(cards.size(), 1), 20.0, 70.0)
	for i in cards.size():
		var card: Card = cards[i]
		var v := CardView.new()
		v.size = Vector2(90, 130)
		v.position = Vector2(30 + i * hgap, 0)
		if card.is_odd_one:
			v.setup(CardView.Mode.OLD_MAID, _theme, card)
		else:
			v.setup(CardView.Mode.PIP_FACE, _theme, card)
		v.mouse_filter = Control.MOUSE_FILTER_IGNORE
		_hand_host.add_child(v)
		_hand_views.append(v)


func _build_ui() -> void:
	var bg := ColorRect.new()
	bg.color = ThemeData.BACKGROUND
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)

	_title = _mk_label("Old Maid", Vector2(30, 18), 40, ThemeData.TEXT_DARK)
	_subtitle = _mk_label("", Vector2(30, 70), 22, ThemeData.TEXT_MUTED)
	_ai_count_label = _mk_label("", Vector2(30, 126), 26, ThemeData.TEXT_DARK)
	_ai_backs.position = Vector2(30, 168)
	_ai_backs.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_ai_backs)
	_ai_pairs_label = _mk_label("", Vector2(30, 280), 24, ThemeData.TEXT_MUTED)

	var msg_panel := Panel.new()
	msg_panel.position = Vector2(60, 320)
	msg_panel.size = Vector2(ThemeData.WINDOW_SIZE.x - 120, 80)
	msg_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(msg_panel)
	_msg_label = Label.new()
	_msg_label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_msg_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_msg_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_msg_label.add_theme_font_size_override("font_size", 26)
	_msg_label.add_theme_color_override("font_color", ThemeData.TEXT_DARK)
	msg_panel.add_child(_msg_label)

	_draw_btn = Button.new()
	_draw_btn.position = Vector2(ThemeData.WINDOW_SIZE.x * 0.5 - 140, 418)
	_draw_btn.size = Vector2(280, ThemeData.MIN_TOUCH_TARGET)
	_draw_btn.focus_mode = Control.FOCUS_NONE
	_draw_btn.pressed.connect(_human_draw)
	add_child(_draw_btn)

	_your_label = _mk_label("", Vector2(30, 470), 26, ThemeData.TEXT_DARK)
	_hand_host.position = Vector2(0, 520)
	_hand_host.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_hand_host)

	var menu_btn := Button.new()
	menu_btn.text = "Menu"
	menu_btn.position = Vector2(ThemeData.WINDOW_SIZE.x - 120, 16)
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
	_modal_label.position = Vector2(0, 60)
	_modal_label.size = Vector2(680, 80)
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
