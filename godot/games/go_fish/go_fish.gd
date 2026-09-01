extends GameScreen
## Go Fish screen: human ("You") vs one AI ("Fox"). Ported from
## legacy/games/go_fish/screen.py -- same flow (timed, visible/audible
## ask -> handover -> resolve), rebuilt with Godot nodes.

const AI_NAME := "Fox"
const HUMAN_NAME := "You"
const AI_TURN_DELAY := 0.9
const AI_NO_MATCH_RESOLVE_DELAY := 0.6
const HUMAN_ASK_RESOLVE_DELAY := 0.5

const CARD_W := 90.0

@export var difficulty: int = AIStrategy.Difficulty.EASY

var _game: GoFishGame
var _theme: CardTheme
var _msg := ""

# AI-turn / handover / resolve timers (mirror the pygame screen's state)
var _waiting_for_ai := false
var _ai_timer := 0.0
var _pending_ai_ask := -1
var _awaiting_handover := false
var _ai_resolve_timer := 0.0
var _pending_human_ask := -1
var _waiting_for_human_resolve := false
var _human_ask_timer := 0.0

# nodes
var _subtitle: Label
var _ai_count_label: Label
var _ai_pairs_label: Label
var _ai_backs := Control.new()
var _pond_label: Label
var _msg_label: Label
var _msg_panel: Panel
var _your_label: Label
var _hand_host := Control.new()
var _hand_views: Array[CardView] = []
var _modal: Panel
var _modal_label: Label


func configure(p_difficulty: int) -> void:
	difficulty = p_difficulty


func _ready() -> void:
	super._ready()
	_theme = ThemeData.card_theme("go_fish")
	_build_ui()
	_start_game()


func _start_game() -> void:
	_game = GoFishGame.new([HUMAN_NAME, AI_NAME], {AI_NAME: difficulty})
	_msg = "Click a card to ask %s for it!" % AI_NAME
	_waiting_for_ai = false
	_pending_ai_ask = -1
	_awaiting_handover = false
	_ai_resolve_timer = 0.0
	_pending_human_ask = -1
	_waiting_for_human_resolve = false
	_modal.visible = false
	set_process(true)
	CCAudio.play_sfx("card_move")
	_maybe_start_ai_turn()
	_refresh()


# -- flow ---------------------------------------------------------------
func _maybe_start_ai_turn() -> void:
	if _game.game_over:
		_on_game_over()
		return
	if _game.is_ai_turn():
		_waiting_for_ai = true
		_ai_timer = AI_TURN_DELAY


func _ai_decide() -> void:
	var d := _game.decide_ai_ask()
	_pending_ai_ask = d["rank"]
	_waiting_for_ai = false
	_msg = "%s wants your %s! Click one to hand it over." % [AI_NAME, ItemIcons.item_name_plural(_pending_ai_ask)]
	CCAudio.play_sfx("ask")
	if _game.players[HUMAN_NAME].hand.has_rank(_pending_ai_ask):
		_awaiting_handover = true
	else:
		_ai_resolve_timer = AI_NO_MATCH_RESOLVE_DELAY
	_refresh()


func _resolve_ai_ask() -> void:
	var rank := _pending_ai_ask
	_pending_ai_ask = -1
	_awaiting_handover = false
	_ai_resolve_timer = 0.0
	var result := _game.ask(AI_NAME, HUMAN_NAME, rank)
	var item := ItemIcons.item_name(rank)
	if result.cards_transferred > 0:
		_msg = "%s asks for %s — got %d!" % [AI_NAME, item, result.cards_transferred]
		CCAudio.play_sfx("match")
	elif result.asker_drew_matched:
		_msg = "%s asks for %s — Go Fish, but drew one!" % [AI_NAME, item]
		CCAudio.play_sfx("match")
	else:
		_msg = "%s asks for %s — Go Fish!" % [AI_NAME, item]
		CCAudio.play_sfx("miss")
	_maybe_start_ai_turn()
	_refresh()


func _human_ask(rank: int) -> void:
	CCAudio.play_sfx("card_select")
	_msg = "Asking %s for %s..." % [AI_NAME, ItemIcons.item_name(rank)]
	_pending_human_ask = rank
	_waiting_for_human_resolve = true
	_human_ask_timer = HUMAN_ASK_RESOLVE_DELAY
	_refresh()


func _resolve_human_ask() -> void:
	var rank := _pending_human_ask
	_pending_human_ask = -1
	_waiting_for_human_resolve = false
	var result := _game.ask(HUMAN_NAME, AI_NAME, rank)
	var item := ItemIcons.item_name(rank)
	if result.cards_transferred > 0:
		_msg = "Got %d %s! Go again." % [result.cards_transferred, item]
		CCAudio.play_sfx("match")
	elif result.asker_drew_matched:
		_msg = "Go Fish! Drew a %s — go again!" % item
		CCAudio.play_sfx("match")
	else:
		_msg = "Go Fish! Turn over."
		CCAudio.play_sfx("miss")
	_maybe_start_ai_turn()
	_refresh()


func _on_game_over() -> void:
	if _game.winner == HUMAN_NAME:
		_msg = "You win! Most pairs!"
		CCAudio.play_sfx("win")
	elif _game.winner == AI_NAME:
		_msg = "%s wins this time!" % AI_NAME
		CCAudio.play_sfx("loss")
	else:
		_msg = "It's a tie!"
	_modal_label.text = _msg
	_modal.visible = true
	set_process(false)  # all turn-flow timers are inert once the modal is up


# -- input / process --------------------------------------------------
func _on_card_clicked(view: CardView) -> void:
	if _game.game_over:
		return
	var rank: int = view.card.rank
	if _awaiting_handover:
		if rank == _pending_ai_ask:
			_resolve_ai_ask()
		return
	if _waiting_for_ai or _ai_resolve_timer > 0.0 or _waiting_for_human_resolve:
		return
	if _game.is_ai_turn():
		return
	_human_ask(rank)


func _process(delta: float) -> void:
	if _waiting_for_ai:
		_ai_timer -= delta
		if _ai_timer <= 0.0:
			_ai_decide()
	elif _ai_resolve_timer > 0.0:
		_ai_resolve_timer -= delta
		if _ai_resolve_timer <= 0.0:
			_resolve_ai_ask()
	elif _waiting_for_human_resolve:
		_human_ask_timer -= delta
		if _human_ask_timer <= 0.0:
			_resolve_human_ask()


# -- ui build / refresh ---------------------------------------------
func _mk_label(txt: String, pos: Vector2, px: int, color: Color, _bold := false) -> Label:
	# NOTE: `_bold` is accepted for parity with the legacy screen but not
	# yet honoured -- a bundled bold FontVariation lands with the shared
	# theme in Phase 6/7. All headings render regular weight for now.
	var l := Label.new()
	l.text = txt
	l.position = pos
	l.add_theme_font_size_override("font_size", px)
	l.add_theme_color_override("font_color", color)
	add_child(l)
	return l


func _build_ui() -> void:
	var bg := ColorRect.new()
	bg.color = ThemeData.BACKGROUND
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)

	_mk_label("Go Fish", Vector2(30, 18), 40, ThemeData.TEXT_DARK, true)
	_subtitle = _mk_label("", Vector2(30, 70), 22, ThemeData.TEXT_MUTED)

	_ai_count_label = _mk_label("", Vector2(30, 126), 26, ThemeData.TEXT_DARK, true)
	_ai_backs.position = Vector2(30, 168)
	_ai_backs.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_ai_backs)
	_ai_pairs_label = _mk_label("", Vector2(30, 280), 24, ThemeData.TEXT_MUTED)

	_pond_label = _mk_label("", Vector2(ThemeData.WINDOW_SIZE.x * 0.5 - 120, 308), 24, ThemeData.TEXT_MUTED)

	_msg_panel = Panel.new()
	_msg_panel.position = Vector2(60, 350)
	_msg_panel.size = Vector2(ThemeData.WINDOW_SIZE.x - 120, 90)
	_msg_panel.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_msg_panel)
	_msg_label = Label.new()
	_msg_label.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_msg_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_msg_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_msg_label.add_theme_font_size_override("font_size", 26)
	_msg_label.add_theme_color_override("font_color", ThemeData.TEXT_DARK)
	_msg_panel.add_child(_msg_label)

	_your_label = _mk_label("", Vector2(30, 466), 26, ThemeData.TEXT_DARK, true)
	_hand_host.position = Vector2(0, 506)
	_hand_host.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(_hand_host)

	var menu_btn := Button.new()
	menu_btn.text = "Menu"
	menu_btn.position = Vector2(ThemeData.WINDOW_SIZE.x - 120, 16)
	menu_btn.size = Vector2(96, 40)
	menu_btn.pressed.connect(func(): go_to_menu.emit())
	add_child(menu_btn)

	_build_modal()


func _build_modal() -> void:
	_modal = Panel.new()
	_modal.size = Vector2(680, 280)
	_modal.position = (Vector2(ThemeData.WINDOW_SIZE) - _modal.size) * 0.5
	_modal.visible = false
	add_child(_modal)
	_modal_label = Label.new()
	_modal_label.position = Vector2(0, 60)
	_modal_label.size = Vector2(680, 40)
	_modal_label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_modal_label.add_theme_font_size_override("font_size", 28)
	_modal_label.add_theme_color_override("font_color", ThemeData.TEXT_DARK)
	_modal.add_child(_modal_label)

	var again := Button.new()
	again.text = "Play Again"
	again.size = Vector2(200, ThemeData.MIN_TOUCH_TARGET)
	again.position = Vector2(120, 170)
	again.pressed.connect(_start_game)
	_modal.add_child(again)

	var to_menu := Button.new()
	to_menu.text = "Menu"
	to_menu.size = Vector2(200, ThemeData.MIN_TOUCH_TARGET)
	to_menu.position = Vector2(360, 170)
	to_menu.pressed.connect(func(): go_to_menu.emit())
	_modal.add_child(to_menu)


func _refresh() -> void:
	var ai: Player = _game.players[AI_NAME]
	var you: Player = _game.players[HUMAN_NAME]
	_subtitle.text = "Playing against %s (%s)" % [AI_NAME, AIStrategy.DIFFICULTY_LABELS[difficulty]]
	_ai_count_label.text = "%s's hand: %d cards" % [AI_NAME, ai.hand.size()]
	_ai_pairs_label.text = "Pairs: %d" % ai.books.size()
	_pond_label.text = "Pond: %d cards left" % _game.stock.size()
	_msg_label.text = _msg
	_your_label.text = "Your hand   Pairs: %d" % you.books.size()

	_rebuild_backs(ai.hand.size())
	_rebuild_hand(you.hand.cards)


func _rebuild_backs(count: int) -> void:
	for c in _ai_backs.get_children():
		c.queue_free()
	var x := 0.0
	for i in count:
		var v := CardView.new()
		v.size = Vector2(70, 100)
		v.position = Vector2(x, 0)
		v.setup(CardView.Mode.BACK, _theme)
		_ai_backs.add_child(v)
		x += 26.0


func _rebuild_hand(cards: Array) -> void:
	for v in _hand_views:
		v.queue_free()
	_hand_views.clear()

	var margin := 30.0
	var row_gap := 14.0
	var bottom_margin := 20.0
	var gap := float(ThemeData.MIN_TOUCH_TARGET)
	var available_w := ThemeData.WINDOW_SIZE.x - 2.0 * margin
	var per_row: int = max(1, int((available_w - CARD_W) / gap) + 1)
	var rows: int = max(1, ceili(float(cards.size()) / per_row)) if cards.size() > 0 else 1
	var y0 := _hand_host.position.y
	var available_h: float = max(1.0, ThemeData.WINDOW_SIZE.y - y0 - bottom_margin)
	var card_h: float = clampf((available_h - (rows - 1) * row_gap) / rows, 70.0, 130.0)

	var highlight_rank := _pending_ai_ask if _awaiting_handover else -1
	for i in cards.size():
		var card: Card = cards[i]
		var row := i / per_row
		var col := i % per_row
		var v := CardView.new()
		v.size = Vector2(CARD_W, card_h)
		v.position = Vector2(margin + col * gap, row * (card_h + row_gap))
		v.setup(CardView.Mode.ITEM_FACE, _theme, card)
		v.set_highlighted(highlight_rank != -1 and card.rank == highlight_rank)
		v.clicked.connect(_on_card_clicked)
		_hand_host.add_child(v)
		_hand_views.append(v)
