extends "res://tests/test_case.gd"
## Ported from legacy/tests/unit/test_old_maid.py (+ old_maid_ai.py).

const D := AIStrategy.Difficulty
const S := Card.Suit
const RK := Card.Rank


func _make_game(seed_val := 7, names := ["Ellie", "Fox"]) -> OldMaidGame:
	var ai := {}
	for n in names:
		if n != names[0]:
			ai[n] = D.EASY
	return OldMaidGame.new(names, ai, seed_val)


func _accounted(game: OldMaidGame) -> bool:
	var live: Array = []
	for p in game.players.values():
		live.append_array(p.hand.cards)
	for i in live.size():
		for j in range(i + 1, live.size()):
			if live[i] == live[j]:
				return false
	var books := 0
	for p in game.players.values():
		books += p.books.size()
	return live.size() + 2 * books == 49


func _odd_holders(game: OldMaidGame) -> int:
	var n := 0
	for p in game.players.values():
		for c in p.hand.cards:
			if c.is_odd_one:
				n += 1
	return n


func _set_hand(game: OldMaidGame, who: String, cards: Array) -> void:
	game.players[who].hand.cards.assign(cards)


func _init() -> void:
	# --- deal + initial pairing conserves all 49 ---
	check(_accounted(_make_game()), "deal + initial pairing: all 49 cards accounted for")

	# --- exactly one odd-card holder, never paired off ---
	check(_odd_holders(_make_game()) == 1, "exactly one player holds the odd card")

	# --- guards ---
	var g := _make_game()
	var not_cur: String = g.order.filter(func(n): return n != g.current_player_name())[0]
	check(g.draw(not_cur, g.current_player_name()) == null, "cannot draw out of turn")
	check(g.draw(g.current_player_name(), g.current_player_name()) == null, "cannot draw from self")
	check(g.draw(g.current_player_name(), "Nobody") == null, "cannot draw from unknown player")
	g = _make_game()
	_set_hand(g, g.order[1], [])
	g.turn_index = g.order.find(g.order[0])
	check(g.draw(g.order[0], g.order[1]) == null, "cannot draw from an empty-handed player")

	# --- drawing a matching rank pairs + discards ---
	g = _make_game()
	var p1: String = g.order[0]
	var p2: String = g.order[1]
	_set_hand(g, p1, [Card.new(S.HEARTS, RK.FIVE)])
	_set_hand(g, p2, [Card.new(S.CLUBS, RK.FIVE)])
	g.turn_index = g.order.find(p1)
	var r := g.draw(p1, p2)
	check_eq(r.paired_ranks, [RK.FIVE], "matching draw -> pair")
	check(g.players[p1].hand.is_empty() and g.players[p1].books.has(RK.FIVE), "pair discarded to books")

	# --- non-matching draw keeps both ---
	g = _make_game()
	p1 = g.order[0]; p2 = g.order[1]
	_set_hand(g, p1, [Card.new(S.HEARTS, RK.FIVE)])
	_set_hand(g, p2, [Card.new(S.CLUBS, RK.NINE)])
	g.turn_index = g.order.find(p1)
	r = g.draw(p1, p2)
	check_eq(r.paired_ranks, [], "non-match -> no pair")
	check(g.players[p1].hand.size() == 2, "non-match keeps both cards")

	# --- 3 of a rank -> one pair discarded, one left ---
	g = _make_game()
	p1 = g.order[0]; p2 = g.order[1]
	_set_hand(g, p1, [Card.new(S.HEARTS, RK.FIVE), Card.new(S.CLUBS, RK.FIVE)])
	_set_hand(g, p2, [Card.new(S.SPADES, RK.FIVE)])
	g.turn_index = g.order.find(p1)
	r = g.draw(p1, p2)
	check_eq(r.paired_ranks, [RK.FIVE], "3 of a rank -> exactly one pair discarded")
	check(g.players[p1].hand.size() == 1 and g.players[p1].hand.has_rank(RK.FIVE), "one five left over")

	# --- turn skips empty-handed players (3p) ---
	g = _make_game(7, ["A", "B", "C"])
	_set_hand(g, "B", [])
	_set_hand(g, "A", [Card.new(S.HEARTS, RK.TWO), Card.new(S.CLUBS, RK.KING)])
	_set_hand(g, "C", [Card.new(S.SPADES, RK.TWO), Card.new(S.DIAMONDS, RK.KING)])
	g.turn_index = g.order.find("A")
	g.game_over = false
	r = g.draw("A", "C")
	check(g.current_player_name() == "C", "turn skips empty-handed B, goes A -> C")

	# --- loser recorded as the last player still holding cards ---
	g = _make_game()
	p1 = g.order[0]; p2 = g.order[1]
	_set_hand(g, p1, [Card.make_odd_card()])
	_set_hand(g, p2, [])
	g.game_over = false
	g._check_game_over()
	check(g.game_over and g.loser == p1, "player left holding cards is the loser")

	# --- stalemate at the turn cap ---
	g = _make_game()
	g.turn_count = OldMaidGame.MAX_TURNS
	g._check_game_over()
	check(g.game_over, "game ends (stalemate) at the turn cap")

	# --- four of a kind on the initial deal -> both pairs discarded ---
	g = _make_game()
	p1 = g.order[0]
	g.players[p1].books.clear()
	_set_hand(g, p1, [
		Card.new(S.HEARTS, RK.EIGHT), Card.new(S.CLUBS, RK.EIGHT),
		Card.new(S.SPADES, RK.EIGHT), Card.new(S.DIAMONDS, RK.EIGHT),
	])
	var cleared := g._discard_pairs(p1)
	check_eq(cleared, [RK.EIGHT, RK.EIGHT], "four of a kind -> two pairs at once")
	check(g.players[p1].hand.is_empty(), "hand emptied by the double discard")

	# --- full AI vs AI (2p), card conservation + termination ---
	var g2 := OldMaidGame.new(["Fox1", "Fox2"], {"Fox1": D.HARD, "Fox2": D.EASY}, 123)
	var turns := 0
	var ok := true
	while not g2.game_over and turns < OldMaidGame.MAX_TURNS + 5:
		if not _accounted(g2):
			ok = false
			break
		g2.take_ai_turn()
		turns += 1
	check(ok and g2.game_over and _accounted(g2) and _odd_holders(g2) == 1,
		"full 2p game conserves 49 cards, ends, odd card still held once")

	# --- 3 and 4 player full games ---
	for np in [3, 4]:
		var names := ["Fox1", "Fox2", "Fox3", "Fox4"].slice(0, np)
		var diffs := [D.EASY, D.MEDIUM, D.HARD, D.EASY]
		var ai := {}
		for i in np:
			ai[names[i]] = diffs[i]
		var gN := OldMaidGame.new(names, ai, 42)
		var t := 0
		var good := true
		while not gN.game_over and t < OldMaidGame.MAX_TURNS + 5:
			if not _accounted(gN):
				good = false
				break
			gN.take_ai_turn()
			t += 1
		check(good and gN.game_over and _accounted(gN), "full %d-player game conserves cards and ends" % np)

	# --- 3p: one draw empties two hands at once -> sole survivor loses ---
	g = _make_game(7, ["A", "B", "C"])
	_set_hand(g, "A", [Card.new(S.HEARTS, RK.FOUR)])          # A draws C's 4 -> A pairs -> A empty
	_set_hand(g, "B", [Card.make_odd_card()])                 # B stuck with the odd card
	_set_hand(g, "C", [Card.new(S.CLUBS, RK.FOUR)])           # C loses its only card to A
	g.turn_index = g.order.find("A")
	g.game_over = false
	g.draw("A", "C")
	check(g.game_over and g.loser == "B", "3p simultaneous double-empty leaves the odd-card holder as loser")

	# --- stalemate reached through real play without hanging ---
	var gs := OldMaidGame.new(["Fox1", "Fox2"], {"Fox1": D.EASY, "Fox2": D.EASY}, 1)
	gs.players["Fox1"].hand.cards.assign([Card.new(S.HEARTS, RK.TWO), Card.make_odd_card()])
	gs.players["Fox2"].hand.cards.assign([Card.new(S.CLUBS, RK.THREE), Card.new(S.SPADES, RK.THREE)])
	# Fox2 has a pair -> discards on its first turn; then both hold 1 disjoint card forever.
	gs.turn_index = gs.order.find("Fox1")
	gs.game_over = false
	var st := 0
	while not gs.game_over and st < OldMaidGame.MAX_TURNS + 5:
		gs.take_ai_turn()
		st += 1
	check(gs.game_over, "disjoint-hands stalemate terminates at the turn cap via real draws")

	# --- determinism ---
	var a := OldMaidGame.new(["A", "B"], {"A": D.HARD, "B": D.MEDIUM}, 555)
	var b := OldMaidGame.new(["A", "B"], {"A": D.HARD, "B": D.MEDIUM}, 555)
	while not a.game_over:
		a.take_ai_turn()
	while not b.game_over:
		b.take_ai_turn()
	check(a.loser == b.loser and a.turn_count == b.turn_count, "same seed -> identical outcome")

	# --- AI: HARD favours larger hands more than MEDIUM ---
	var sizes := {"small": 2, "big": 10}
	var med := OldMaidStrategy.new(D.MEDIUM, _seeded(1))
	var hard := OldMaidStrategy.new(D.HARD, _seeded(1))
	var med_big := 0
	var hard_big := 0
	for _n in 4000:
		if med.decide_target(sizes) == "big":
			med_big += 1
		if hard.decide_target(sizes) == "big":
			hard_big += 1
	check(hard_big > med_big and med_big > 2000, "HARD favours the big hand more than MEDIUM (both above chance)")

	# --- AI: EASY roughly uniform regardless of hand size ---
	var easy := OldMaidStrategy.new(D.EASY, _seeded(2))
	var easy_big := 0
	for _n in 4000:
		if easy.decide_target(sizes) == "big":
			easy_big += 1
	check(easy_big > 1700 and easy_big < 2300, "EASY ignores hand size (~50/50)")

	finish("old_maid")


func _seeded(s: int) -> RandomNumberGenerator:
	var rng := RandomNumberGenerator.new()
	rng.seed = s
	return rng
