extends "res://tests/test_case.gd"
## Ported from legacy/tests/unit/test_memory.py.

const D := AIStrategy.Difficulty


func _make_game(seed_val := 7) -> MemoryGame:
	return MemoryGame.new(["Ellie", "Fox"], 8, {"Fox": D.EASY}, seed_val)


func _find_pair(game: MemoryGame) -> Array:
	var r1: int = game.board[0].rank
	for i in range(1, game.board.size()):
		if game.board[i].rank == r1:
			return [0, i]
	return [0, 1]


func _init() -> void:
	# --- board size, nothing pre-matched ---
	var g := _make_game()
	check(g.board.size() == 16, "8 pairs -> 16-tile board")
	check(g.matched.is_empty() and g.unflipped_positions().size() == 16, "nothing pre-matched")

	# --- guards ---
	g = _make_game()
	var me := g.current_player_name()
	var other: String = g.order.filter(func(n): return n != me)[0]
	check(g.flip_two(other, 0, 1) == null, "cannot flip out of turn")
	check(g.flip_two(me, 3, 3) == null, "cannot flip the same position twice")
	check(g.flip_two(me, 0, 999) == null, "cannot flip an out-of-range position")

	# --- matching flip scores + goes again ---
	g = _make_game()
	me = g.current_player_name()
	var pair := _find_pair(g)
	var r1: int = g.board[pair[0]].rank
	var res := g.flip_two(me, pair[0], pair[1])
	check(res.matched and res.went_again, "match -> went again")
	check(g.current_player_name() == me, "matcher keeps the turn")
	check(g.players[me].score == 1 and g.players[me].books.has(r1), "score + book recorded")
	check(g.matched.has(pair[0]) and g.matched.has(pair[1]), "both positions marked matched")
	check(g.flip_two(g.current_player_name(), pair[0], (pair[0] + 1 if pair[0] + 1 != pair[1] else pair[0] + 2)) == null,
		"cannot flip an already-matched position")

	# --- non-matching flip passes turn + still records public memory ---
	g = _make_game()
	me = g.current_player_name()
	# pick two positions of different rank
	var a := 0
	var b := -1
	for i in range(1, g.board.size()):
		if g.board[i].rank != g.board[a].rank:
			b = i
			break
	res = g.flip_two(me, a, b)
	check(not res.matched and not res.went_again, "non-match -> turn ends")
	check(g.current_player_name() != me, "turn passed to the other player")
	check(not g.matched.has(a) and not g.matched.has(b), "non-matched positions stay unmatched")
	check(g.known_positions[a] == res.rank1 and g.known_positions[b] == res.rank2, "public reveal history recorded")

	# --- stalemate at the turn cap ---
	g = _make_game()
	g.turn_count = MemoryGame.MAX_TURNS
	g._check_game_over()
	check(g.game_over and g.stalemate, "stalemate at the turn cap")

	# --- full AI vs AI (2p, 10 pairs) ---
	var g2 := MemoryGame.new(["Fox1", "Fox2"], 10, {"Fox1": D.HARD, "Fox2": D.EASY}, 17)
	var t := 0
	while not g2.game_over and t < MemoryGame.MAX_TURNS + 5:
		g2.take_ai_turn()
		t += 1
	check(g2.game_over and not g2.stalemate and g2.matched.size() == g2.board.size(), "full 2p game clears the board")
	var pairs_found := 0
	for p in g2.players.values():
		pairs_found += p.books.size()
	check(pairs_found == 10, "all 10 pairs found across players")

	# --- 1 (solo), 3, 4 players ---
	for np in [1, 3, 4]:
		var names := ["Fox1", "Fox2", "Fox3", "Fox4"].slice(0, np)
		var diffs := [D.EASY, D.MEDIUM, D.HARD, D.EASY]
		var ai := {}
		for i in np:
			ai[names[i]] = diffs[i]
		var gN := MemoryGame.new(names, 6, ai, 88)
		var tn := 0
		while not gN.game_over and tn < MemoryGame.MAX_TURNS + 5:
			gN.take_ai_turn()
			tn += 1
		check(gN.game_over and gN.matched.size() == gN.board.size(), "full %d-player game clears the board" % np)

	# --- determinism ---
	var x := MemoryGame.new(["A", "B"], 8, {"A": D.HARD, "B": D.MEDIUM}, 321)
	var y := MemoryGame.new(["A", "B"], 8, {"A": D.HARD, "B": D.MEDIUM}, 321)
	while not x.game_over:
		x.take_ai_turn()
	while not y.game_over:
		y.take_ai_turn()
	check(x.turn_count == y.turn_count and x.players["A"].score == y.players["A"].score, "same seed -> identical outcome")

	finish("memory")
