extends "res://tests/test_case.gd"
## Ported from legacy/tests/unit/test_letter_match.py.


func _solve(game: LetterMatchGame, max_clicks := 4000) -> int:
	# Greedy solver: pair up whatever's left by matching letters.
	var clicks := 0
	while not game.game_over and clicks < max_clicks:
		var unflipped := game.unflipped_positions()
		var by_letter := {}
		var target_a := -1
		var target_b := -1
		for p in unflipped:
			var key: String = game.board[p].letter + ("U" if game.board[p].is_upper else "L")
			var other: String = game.board[p].letter + ("L" if game.board[p].is_upper else "U")
			if by_letter.has(other):
				target_a = by_letter[other]
				target_b = p
				break
			by_letter[key] = p
		if target_a == -1:
			break
		game.click(target_a)
		game.click(target_b)
		clicks += 2
	return clicks


func _init() -> void:
	# --- tile display reflects case ---
	var upper := LetterMatchGame.Tile.new("B", true)
	var lower := LetterMatchGame.Tile.new("B", false)
	check(upper.display() == "B" and lower.display() == "b", "Tile.display reflects case")

	# --- board: one upper + one lower per letter ---
	var g := LetterMatchGame.new(6, 1)
	check(g.board.size() == 12, "6 letters -> 12 tiles")
	var per := {}
	for t in g.board:
		var k: String = t.letter + ("U" if t.is_upper else "L")
		per[k] = per.get(k, 0) + 1
	var all_one := true
	for k in per:
		if per[k] != 1:
			all_one = false
	check(all_one and per.size() == 12, "exactly one upper and one lower tile per letter")

	# --- letter_count boundaries ---
	check(LetterMatchGame.new(26, 1).board.size() == 52, "letters mode allows 26")
	check(not LetterMatchGame.new(27, 1).is_valid, "letters mode rejects 27")
	check(not LetterMatchGame.new(0, 1).is_valid, "rejects letter_count 0")

	# --- out-of-range click -> not accepted ---
	g = LetterMatchGame.new(4, 1)
	var r := g.click(999)
	check(not r.accepted, "out-of-range click is not accepted")

	# --- matching pair recorded + counted ---
	g = LetterMatchGame.new(4, 1)
	# find an upper and its lower
	var up := -1
	var lo := -1
	for i in g.board.size():
		if g.board[i].is_upper and up == -1:
			up = i
			var lt: String = g.board[i].letter
			for j in g.board.size():
				if not g.board[j].is_upper and g.board[j].letter == lt:
					lo = j
			break
	g.click(up)
	r = g.click(lo)
	check(r.accepted and r.matched, "matching pair -> matched result")
	check(g.correct == 1 and g.attempts == 1, "one correct in one attempt")
	check(g.matched.has(up) and g.matched.has(lo), "both tiles marked matched")

	# --- reclicking the pending tile is gently ignored ---
	g = LetterMatchGame.new(4, 1)
	g.click(0)
	r = g.click(0)
	check(not r.accepted and not g.game_over, "re-clicking the pending tile is a no-op, not an error")

	# --- reclicking an already-matched tile is gently ignored ---
	g = LetterMatchGame.new(4, 1)
	# match tiles 0 and its partner
	var partner := -1
	for j in range(1, g.board.size()):
		if g.board[j].letter == g.board[0].letter:
			partner = j
			break
	g.click(0)
	g.click(partner)
	r = g.click(0)
	check(not r.accepted and r.reason == "already matched", "re-clicking a matched tile is gently ignored")

	# --- clicking after game over is gently ignored ---
	g = LetterMatchGame.new(2, 1)
	_solve(g)
	check(g.game_over, "2-letter game completes")
	r = g.click(0)
	check(not r.accepted, "clicking after completion is gently ignored")

	# --- accuracy = correct / attempts ---
	g = LetterMatchGame.new(4, 1)
	# force one miss: two uppers
	var u1 := -1
	var u2 := -1
	for i in g.board.size():
		if g.board[i].is_upper:
			if u1 == -1:
				u1 = i
			elif u2 == -1:
				u2 = i
	g.click(u1)
	g.click(u2)
	check(g.attempts == 1 and g.correct == 0 and is_equal_approx(g.accuracy(), 0.0), "a miss counts as an attempt")

	# --- full games complete, all modes / sizes ---
	for lc in [1, 4, 12, 26]:
		var gg := LetterMatchGame.new(lc, 5)
		_solve(gg)
		check(gg.game_over and gg.matched.size() == gg.board.size(), "letters mode, %d letters: completes" % lc)

	# --- animals mode ---
	g = LetterMatchGame.new(7, 9, "animals")
	check(g.is_valid and g.board.size() == 14, "animals mode: 7 letters -> 14 tiles")
	var has_animal_lower := false
	for t in g.board:
		if not t.is_upper and t.is_animal:
			has_animal_lower = true
	check(has_animal_lower, "animals mode: lowercase tiles are animal tiles")
	check(not LetterMatchGame.new(8, 1, "animals").is_valid, "animals mode caps at 7 letters")
	check(not LetterMatchGame.new(4, 1, "bogus").is_valid, "invalid mode rejected")
	_solve(g)
	check(g.game_over, "animals mode game completes")

	# --- animal mode letters stay in sync with ItemIcons.ANIMAL_ICONS ---
	var in_sync := true
	for l in LetterMatchGame.ANIMAL_MODE_LETTERS:
		if not ItemIcons.ANIMAL_ICONS.has(l):
			in_sync = false
	check(in_sync and ItemIcons.ANIMAL_ICONS.size() == LetterMatchGame.ANIMAL_MODE_LETTERS.size(),
		"ANIMAL_MODE_LETTERS matches ItemIcons.ANIMAL_ICONS keys")

	# --- a miss does not reshuffle; a match does ---
	g = LetterMatchGame.new(6, 3)
	var before := g.board.duplicate()
	# a miss (two uppers)
	var ua := -1
	var ub := -1
	for i in g.board.size():
		if g.board[i].is_upper:
			if ua == -1: ua = i
			elif ub == -1: ub = i
	g.click(ua)
	g.click(ub)
	var unchanged := true
	for i in g.board.size():
		if g.board[i] != before[i]:
			unchanged = false
	check(unchanged, "a miss does not reshuffle the board")

	# --- determinism ---
	var a := LetterMatchGame.new(8, 4242)
	var b := LetterMatchGame.new(8, 4242)
	var sig_a := ""
	var sig_b := ""
	for i in a.board.size():
		sig_a += a.board[i].letter + ("U" if a.board[i].is_upper else "L")
		sig_b += b.board[i].letter + ("U" if b.board[i].is_upper else "L")
	check(sig_a == sig_b, "same seed -> identical starting board")

	finish("letter_match")
