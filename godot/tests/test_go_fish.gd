extends "res://tests/test_case.gd"
## Ported from legacy/tests/unit/test_go_fish.py (representative subset +
## full AI-vs-AI card-conservation runs).

const D := AIStrategy.Difficulty
const S := Card.Suit
const RK := Card.Rank


func _make_game(seed_val := 7) -> GoFishGame:
	return GoFishGame.new(["Ellie", "Fox"], {"Fox": D.EASY}, seed_val)


func _cards_accounted_for(game: GoFishGame) -> bool:
	var live: Array = game.stock.duplicate()
	for p in game.players.values():
		live.append_array(p.hand.cards)
	# uniqueness by reference identity
	for i in live.size():
		for j in range(i + 1, live.size()):
			if live[i] == live[j]:
				return false
	var books_total := 0
	for p in game.players.values():
		books_total += p.books.size()
	return live.size() + 2 * books_total == 52


func _set_hand(game: GoFishGame, who: String, cards: Array) -> void:
	game.players[who].hand.cards.assign(cards)


func _init() -> void:
	# --- deal accounting ---
	check(_cards_accounted_for(_make_game()), "2-player deal: all 52 cards accounted for")

	# --- guard rails (legacy raised ValueError; port logs + returns null) ---
	var g := _make_game()
	var not_current: String = g.order.filter(func(n): return n != g.current_player_name())[0]
	check(g.ask(not_current, g.current_player_name(), RK.ACE) == null, "cannot ask out of turn")
	var me := g.current_player_name()
	check(g.ask(me, me, g.legal_ranks(me)[0]) == null, "cannot ask yourself")
	var held := g.legal_ranks(me)
	var missing := RK.ACE
	for r in range(RK.ACE, RK.KING + 1):
		if not held.has(r):
			missing = r
			break
	check(g.ask(me, g.other_player_names(me)[0], missing) == null, "cannot ask for a rank not held")
	check(g.ask(me, "Nobody", held[0]) == null, "cannot ask an unknown player")

	# --- successful ask: transfer all, auto-claim the pair, go again ---
	g = _make_game()
	var p1: String = g.order[0]
	var p2: String = g.order[1]
	_set_hand(g, p1, [Card.new(S.HEARTS, RK.SEVEN), Card.new(S.CLUBS, RK.TWO)])
	_set_hand(g, p2, [Card.new(S.SPADES, RK.SEVEN), Card.new(S.DIAMONDS, RK.SEVEN), Card.new(S.CLUBS, RK.KING)])
	g.turn_index = g.order.find(p1)
	g.stock.clear()
	var r := g.ask(p1, p2, RK.SEVEN)
	check(r.cards_transferred == 2, "successful ask transferred 2")
	check(r.went_again, "successful ask -> go again")
	check(g.current_player_name() == p1, "turn stays with asker")
	check_eq(r.books_claimed_by_asker, [RK.SEVEN], "one book claimed")
	check(g.players[p1].hand.count_of_rank(RK.SEVEN) == 1, "one seven left in hand")
	check(not g.players[p2].hand.has_rank(RK.SEVEN), "target has no sevens left")

	# --- failed ask: draw non-match, turn passes ---
	g = _make_game()
	p1 = g.order[0]; p2 = g.order[1]
	_set_hand(g, p1, [Card.new(S.HEARTS, RK.SEVEN)])
	_set_hand(g, p2, [Card.new(S.CLUBS, RK.KING)])
	g.stock.assign([Card.new(S.SPADES, RK.TWO)])
	g.turn_index = g.order.find(p1)
	r = g.ask(p1, p2, RK.SEVEN)
	check(r.cards_transferred == 0 and r.asker_drew and not r.asker_drew_matched, "miss: drew a non-match")
	check(not r.went_again and g.current_player_name() == p2, "miss: turn passes")
	check(g.players[p1].hand.has_rank(RK.TWO), "miss: drew the 2 into hand")

	# --- failed ask: draw the matching rank, go again (hand not emptied) ---
	g = _make_game()
	p1 = g.order[0]; p2 = g.order[1]
	_set_hand(g, p1, [Card.new(S.HEARTS, RK.SEVEN), Card.new(S.CLUBS, RK.TWO)])
	_set_hand(g, p2, [Card.new(S.CLUBS, RK.KING)])
	g.stock.assign([Card.new(S.SPADES, RK.SEVEN)])
	g.turn_index = g.order.find(p1)
	r = g.ask(p1, p2, RK.SEVEN)
	check(r.asker_drew_matched, "go fish then drew the match")
	check_eq(r.books_claimed_by_asker, [RK.SEVEN], "drew-match claims the book")
	check(r.went_again, "drew-match keeps the turn (hand not empty)")

	# --- draw match that empties hand with empty stock -> turn ends ---
	g = _make_game()
	p1 = g.order[0]; p2 = g.order[1]
	_set_hand(g, p1, [Card.new(S.HEARTS, RK.SEVEN)])
	_set_hand(g, p2, [Card.new(S.CLUBS, RK.KING)])
	g.stock.assign([Card.new(S.SPADES, RK.SEVEN)])
	g.turn_index = g.order.find(p1)
	r = g.ask(p1, p2, RK.SEVEN)
	check(r.asker_drew_matched and g.players[p1].hand.is_empty(), "drew match, hand emptied")
	check(not r.went_again and g.current_player_name() == p2, "no redraw available -> turn ends")

	# --- four copies at once -> two books ---
	# (reset books/score first: a different PRNG means the initial deal may
	# already have auto-claimed a seven-book for this player, unlike the
	# legacy Python seed. Testing the mechanic in isolation.)
	g = _make_game()
	p1 = g.order[0]; p2 = g.order[1]
	g.players[p1].books.clear()
	g.players[p1].score = 0
	var score_before: int = g.players[p1].score
	_set_hand(g, p1, [Card.new(S.HEARTS, RK.SEVEN), Card.new(S.CLUBS, RK.SEVEN), Card.new(S.DIAMONDS, RK.SEVEN)])
	_set_hand(g, p2, [Card.new(S.SPADES, RK.SEVEN)])
	g.turn_index = g.order.find(p1)
	g.stock.clear()
	r = g.ask(p1, p2, RK.SEVEN)
	check_eq(r.books_claimed_by_asker, [RK.SEVEN, RK.SEVEN], "4 copies -> 2 books at once")
	check(g.players[p1].books.count(RK.SEVEN) == 2 and g.players[p1].score == score_before + 2, "score +2")

	# --- empty hand gets a free draw at turn start ---
	g = _make_game()
	p1 = g.order[0]; p2 = g.order[1]
	_set_hand(g, p1, [])
	_set_hand(g, p2, [Card.new(S.CLUBS, RK.KING)])
	g.stock.assign([Card.new(S.SPADES, RK.TWO)])
	g.turn_index = g.order.find(p1)
	g._ensure_current_player_can_act()
	check(not g.players[p1].hand.is_empty(), "empty hand -> free draw at turn start")

	# --- game over: all 26 books ---
	g = _make_game()
	for name in g.order:
		g.players[name].hand.cards.clear()
		g.players[name].books.clear()
	var all_ranks: Array[int] = []
	for _twice in 2:
		for rr in range(RK.ACE, RK.KING + 1):
			all_ranks.append(rr)
	for i in all_ranks.size():
		g.players[g.order[i % 2]].books.append(all_ranks[i])
	g.game_over = false
	g._check_game_over()
	check(g.game_over, "game ends when all 26 books are claimed")

	# --- game over: stalemate at turn cap ---
	g = _make_game()
	g.turn_count = GoFishGame.MAX_TURNS
	g._check_game_over()
	check(g.game_over, "game ends (stalemate) at the turn cap")

	# --- full AI vs AI, 2 players, no card duplication, terminates ---
	var g2 := GoFishGame.new(["Fox1", "Fox2"], {"Fox1": D.HARD, "Fox2": D.EASY}, 123)
	var turns := 0
	var conserved := true
	while not g2.game_over and turns < GoFishGame.MAX_TURNS + 5:
		if not _cards_accounted_for(g2):
			conserved = false
			break
		g2.take_ai_turn()
		turns += 1
	check(conserved and g2.game_over and _cards_accounted_for(g2), "full 2p HARD-vs-EASY game conserves cards and ends")

	# --- full AI game, 3 and 4 players ---
	for np in [3, 4]:
		var names := ["Fox1", "Fox2", "Fox3", "Fox4"].slice(0, np)
		var diffs := [D.EASY, D.MEDIUM, D.HARD, D.EASY]
		var ai := {}
		for i in np:
			ai[names[i]] = diffs[i]
		var gN := GoFishGame.new(names, ai, 42)
		var t := 0
		var ok := true
		while not gN.game_over and t < GoFishGame.MAX_TURNS + 5:
			if not _cards_accounted_for(gN):
				ok = false
				break
			gN.take_ai_turn()
			t += 1
		check(ok and gN.game_over and _cards_accounted_for(gN), "full %d-player game conserves cards and ends" % np)

	# --- adversarial disjoint-hands stalemate runs to the cap without hanging ---
	var gs := GoFishGame.new(["Fox1", "Fox2"], {"Fox1": D.EASY, "Fox2": D.EASY}, 1)
	gs.players["Fox1"].hand.cards.assign([Card.new(S.HEARTS, RK.TWO), Card.new(S.CLUBS, RK.TWO)])
	gs.players["Fox2"].hand.cards.assign([Card.new(S.HEARTS, RK.THREE), Card.new(S.CLUBS, RK.THREE)])
	gs.stock.clear()
	gs.turn_index = gs.order.find("Fox1")
	gs.game_over = false
	var st := 0
	while not gs.game_over and st < GoFishGame.MAX_TURNS + 5:
		gs.take_ai_turn()
		st += 1
	check(gs.game_over, "disjoint-hands stalemate terminates at the cap")

	# --- hit that empties the hand triggers a free redraw, keeps the turn ---
	g = _make_game()
	p1 = g.order[0]; p2 = g.order[1]
	g.players[p1].books.clear(); g.players[p1].score = 0
	_set_hand(g, p1, [Card.new(S.HEARTS, RK.SEVEN), Card.new(S.CLUBS, RK.SEVEN), Card.new(S.DIAMONDS, RK.SEVEN)])
	_set_hand(g, p2, [Card.new(S.SPADES, RK.SEVEN)])
	g.stock.assign([Card.new(S.CLUBS, RK.NINE)])
	g.turn_index = g.order.find(p1)
	r = g.ask(p1, p2, RK.SEVEN)
	check(r.books_claimed_by_asker.size() == 2 and r.asker_drew, "double-book empties hand -> free redraw")
	check(r.went_again and g.players[p1].hand.has_rank(RK.NINE), "redrew the NINE, turn continues")

	# --- same, but empty stock -> turn ends ---
	g = _make_game()
	p1 = g.order[0]; p2 = g.order[1]
	g.players[p1].books.clear()
	_set_hand(g, p1, [Card.new(S.HEARTS, RK.SEVEN), Card.new(S.CLUBS, RK.SEVEN), Card.new(S.DIAMONDS, RK.SEVEN)])
	_set_hand(g, p2, [Card.new(S.SPADES, RK.SEVEN)])
	g.stock.clear()
	g.turn_index = g.order.find(p1)
	r = g.ask(p1, p2, RK.SEVEN)
	check(g.players[p1].hand.is_empty() and not r.went_again and g.current_player_name() == p2,
		"double-book empties hand, no stock -> turn ends")

	# --- _turn_failed_ranks accumulate within a turn, reset when it ends ---
	g = _make_game()
	p1 = g.order[0]; p2 = g.order[1]
	_set_hand(g, p1, [Card.new(S.HEARTS, RK.SEVEN), Card.new(S.CLUBS, RK.EIGHT)])
	_set_hand(g, p2, [Card.new(S.SPADES, RK.KING)])
	g.stock.assign([Card.new(S.DIAMONDS, RK.SEVEN), Card.new(S.HEARTS, RK.TWO)])  # top = TWO
	g.turn_index = g.order.find(p1)
	g.ask(p1, p2, RK.SEVEN)  # miss, draw TWO (top), turn ends
	check(g._turn_failed_ranks.is_empty(), "_turn_failed_ranks reset once the turn ends")

	# --- decide_ai_ask is a pure query: no mutation, repeatable ---
	g = _make_game()
	# make it the AI's turn
	if not g.is_ai_turn():
		g.turn_index = (g.turn_index + 1) % g.order.size()
	var ai_name := g.current_player_name()
	var cards_before: int = g.players[ai_name].hand.cards.size()
	var turn_before := g.current_player_name()
	var q1 := g.decide_ai_ask()
	var q2 := g.decide_ai_ask()
	check(g.players[ai_name].hand.cards.size() == cards_before and g.current_player_name() == turn_before,
		"decide_ai_ask does not mutate hand or advance the turn")
	check(not q1.is_empty() and not q2.is_empty(), "decide_ai_ask returns a decision both times")

	# --- determinism: same seed -> same game outcome ---
	var a := GoFishGame.new(["A", "B"], {"A": D.HARD, "B": D.MEDIUM}, 999)
	var b := GoFishGame.new(["A", "B"], {"A": D.HARD, "B": D.MEDIUM}, 999)
	while not a.game_over:
		a.take_ai_turn()
	while not b.game_over:
		b.take_ai_turn()
	check(a.winner == b.winner and a.turn_count == b.turn_count, "same seed -> identical outcome")

	finish("go_fish")
