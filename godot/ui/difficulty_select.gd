extends Control
## Difficulty / mode picker. Ports DifficultySelectScreen and
## LetterMatchModeSelectScreen (legacy/ui/launcher.py). Reads the target
## game from CCRouter; Letter Match shows two mode buttons instead of
## difficulties, Memory adds a "Play Alone" option.

const D := AIStrategy.Difficulty

var _game := "go_fish"


func _ready() -> void:
	set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	var cfg := CCRouter.consume()
	_game = cfg.get("game", "go_fish")
	_build()


func _build() -> void:
	var bg := ColorRect.new()
	bg.color = ThemeData.BACKGROUND
	bg.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bg)

	var is_letters := _game == "letter_match"
	var has_solo := _game == "memory"
	var color: Color = ThemeData.GAME_COLORS.get(_game, ThemeData.PRIMARY)

	var header := ""
	if is_letters:
		header = "Letter Match: pick a mode!"
	elif has_solo:
		header = "Memory: play with a friend, or alone!"
	else:
		header = "%s: choose a friend to play with" % _label_for(_game)
	_center_label(header, 140, 40, ThemeData.TEXT_DARK)

	# option list: [ [label, Callable, color], ... ]
	var options: Array = []
	if is_letters:
		options.append(["Letters (Aa)", func(): CCRouter.goto_game("letter_match", {"mode": "letters"}), color])
		options.append(["Animals", func(): CCRouter.goto_game("letter_match", {"mode": "animals"}), color])
	else:
		if has_solo:
			options.append(["Play Alone", func(): CCRouter.goto_game("memory", {"solo": true}), ThemeData.TEXT_MUTED])
		for diff: int in [D.EASY, D.MEDIUM, D.HARD]:
			var d: int = diff
			options.append([AIStrategy.DIFFICULTY_LABELS[d],
				func(): CCRouter.goto_game(_game, {"difficulty": d}), color])

	var cx := ThemeData.WINDOW_SIZE.x * 0.5
	var btn_w := 420.0
	var btn_h := 100.0
	var gap := 30.0
	var start_y := 260.0
	var font_px := 36
	if options.size() > 3:
		btn_h = 82.0
		gap = 22.0
		start_y = 190.0
		font_px = 32

	for i in options.size():
		var opt: Array = options[i]
		var b := _mk_button(opt[0], opt[2], font_px)
		b.position = Vector2(cx - btn_w * 0.5, start_y + i * (btn_h + gap))
		b.size = Vector2(btn_w, btn_h)
		b.pressed.connect(func():
			CCAudio.play_sfx("button")
			opt[1].call())
		add_child(b)

	var back := _mk_button("Back", ThemeData.TEXT_MUTED, 28)
	back.position = Vector2(40, ThemeData.WINDOW_SIZE.y - 100)
	back.size = Vector2(200, ThemeData.MIN_TOUCH_TARGET)
	back.pressed.connect(func():
		CCAudio.play_sfx("button")
		CCRouter.goto_menu())
	add_child(back)


func _mk_button(txt: String, color: Color, px: int) -> Button:
	var b := Button.new()
	b.text = txt
	b.focus_mode = Control.FOCUS_NONE
	b.add_theme_font_size_override("font_size", px)
	var sb := StyleBoxFlat.new()
	sb.bg_color = color
	sb.set_corner_radius_all(18)
	sb.set_border_width_all(3)
	sb.border_color = ThemeData.TEXT_DARK
	for st in ["normal", "hover", "pressed"]:
		b.add_theme_stylebox_override(st, sb)
	b.add_theme_color_override("font_color", ThemeData.TEXT_LIGHT)
	return b


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


func _label_for(key: String) -> String:
	match key:
		"go_fish": return "Go Fish"
		"old_maid": return "Old Maid"
		"memory": return "Memory"
		"letter_match": return "Letter Match"
	return key
