extends SceneTree
## Headless smoke tests for the remaining screens (Old Maid, Memory solo +
## vs-AI, Letter Match) and the menu / difficulty-select / router wiring.
## Instantiates each scene and drives it, asserting no script errors and
## that games that should end, end.

var _fails := 0


func _init() -> void:
	_run.call_deferred()


func _ok(cond: bool, msg: String) -> void:
	if cond:
		print("  ok   ", msg)
	else:
		_fails += 1
		printerr("  FAIL ", msg)


func _run() -> void:
	Engine.time_scale = 80.0
	await _test_menu_and_difficulty()
	await _test_old_maid()
	await _test_memory(true)
	await _test_memory(false)
	await _test_letter_match("letters")
	await _test_letter_match("animals")
	print("== screens: %d failure(s) ==" % _fails)
	quit(1 if _fails > 0 else 0)


func _fresh(path: String, cfg := {}) -> Node:
	# CCRouter is an autoload -- reach it via the tree, not as a bare
	# identifier (this script compiles before autoloads register).
	root.get_node("CCRouter")._pending = cfg
	var scene: Node = load(path).instantiate()
	root.add_child(scene)
	await process_frame
	await process_frame
	return scene


func _test_menu_and_difficulty() -> void:
	var menu := await _fresh("res://ui/main_menu.tscn")
	_ok(menu.get_child_count() > 4, "main menu builds tiles + labels")
	menu.free()

	var diff := await _fresh("res://ui/difficulty_select.tscn", {"game": "memory"})
	var btn_texts := ""
	for c in diff.get_children():
		if c is Button:
			btn_texts += c.text + "|"
	_ok("Play Alone" in btn_texts and "Sleepy Fox" in btn_texts and "Back" in btn_texts,
		"difficulty select (memory) shows Play Alone + 3 tiers + Back")
	diff.free()

	var lm := await _fresh("res://ui/difficulty_select.tscn", {"game": "letter_match"})
	btn_texts = ""
	for c in lm.get_children():
		if c is Button:
			btn_texts += c.text + "|"
	_ok("Animals" in btn_texts and "Letters (Aa)" in btn_texts, "difficulty select (letter_match) shows the two modes")
	lm.free()


func _test_old_maid() -> void:
	var s := await _fresh("res://games/old_maid/old_maid.tscn", {"difficulty": AIStrategy.Difficulty.MEDIUM})
	var start := Time.get_ticks_msec()
	var draws := 0
	while not s._game.game_over and (Time.get_ticks_msec() - start) < 60000:
		await process_frame
		if not s._game.is_ai_turn() and not s._waiting_for_ai:
			s._human_draw()
			draws += 1
		if draws > 5000:
			break
	_ok(s._game.game_over, "Old Maid vs Fox runs to a loser (%d human draws)" % draws)
	s.free()


func _test_memory(solo: bool) -> void:
	var cfg := {"solo": true} if solo else {"difficulty": AIStrategy.Difficulty.HARD}
	var s := await _fresh("res://games/memory/memory.tscn", cfg)
	var start := Time.get_ticks_msec()
	while not s._game.game_over and (Time.get_ticks_msec() - start) < 90000:
		await process_frame
		if s._locked or s._game.is_ai_turn():
			continue
		# greedy: find two unmatched, unshown positions of equal rank
		var pair := _find_memory_pair(s)
		if pair.is_empty():
			# fall back: any two distinct legal positions
			pair = _any_two(s)
		if pair.is_empty():
			continue
		s._on_tile_clicked(s._tiles[pair[0]])
		await process_frame
		s._on_tile_clicked(s._tiles[pair[1]])
	_ok(s._game.game_over and s._game.matched.size() == s._game.board.size(),
		"Memory %s clears the whole board" % ("solo" if solo else "vs Fox"))
	s.free()


func _find_memory_pair(s) -> Array:
	var by_rank := {}
	for i in s._game.board.size():
		if s._game.matched.has(i) or s._visible.has(i):
			continue
		var r: int = s._game.board[i].rank
		if by_rank.has(r):
			return [by_rank[r], i]
		by_rank[r] = i
	return []


func _any_two(s) -> Array:
	var free: Array = []
	for i in s._game.board.size():
		if not s._game.matched.has(i) and not s._visible.has(i):
			free.append(i)
		if free.size() == 2:
			return free
	return []


func _test_letter_match(mode: String) -> void:
	var s := await _fresh("res://games/letter_match/letter_match.tscn", {"mode": mode})
	var start := Time.get_ticks_msec()
	while not s._game.game_over and (Time.get_ticks_msec() - start) < 60000:
		await process_frame
		if s._locked:
			continue
		var pair := _find_lm_pair(s)
		if pair.is_empty():
			continue
		s._on_tile_clicked(s._tiles[pair[0]])
		s._on_tile_clicked(s._tiles[pair[1]])
	_ok(s._game.game_over and s._game.matched.size() == s._game.board.size(),
		"Letter Match (%s) completes the board" % mode)
	s.free()


func _find_lm_pair(s) -> Array:
	var by_key := {}
	for i in s._game.board.size():
		if s._game.matched.has(i):
			continue
		var t = s._game.board[i]
		var mine: String = t.letter + ("U" if t.is_upper else "L")
		var want: String = t.letter + ("L" if t.is_upper else "U")
		if by_key.has(want):
			return [by_key[want], i]
		by_key[mine] = i
	return []
