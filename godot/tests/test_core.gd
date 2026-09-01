extends SceneTree
## Standalone headless sanity checks for godot/core/*.
## Run: godot --headless --path godot --script res://tests/test_core.gd
## (Replaced by GUT tests in a later phase; this is a fast smoke check.)

var _failures := 0


func _check(cond: bool, msg: String) -> void:
	if cond:
		print("  ok   ", msg)
	else:
		_failures += 1
		printerr("  FAIL ", msg)


func _init() -> void:
	print("== core smoke tests ==")

	# --- Card ---
	var c := Card.new(Card.Suit.HEARTS, Card.Rank.SEVEN)
	_check(c.label() == "7", "seven of hearts label")
	_check(c.symbol() == "♥", "hearts symbol")
	_check(c.is_red(), "hearts is red")
	_check(str(c) == "7♥", "card _to_string")

	var odd := Card.make_odd_card()
	_check(odd.is_odd_one and odd.label() == "OM", "odd card label")
	_check(not odd.is_red(), "odd card not red")
	_check(not odd.matches_rank(c) and not c.matches_rank(odd), "odd never matches")

	var c2 := Card.new(Card.Suit.SPADES, Card.Rank.SEVEN)
	_check(c.matches_rank(c2), "same rank matches across suit")
	_check(c.equals(Card.new(Card.Suit.HEARTS, Card.Rank.SEVEN)), "value equals")
	_check(c != Card.new(Card.Suit.HEARTS, Card.Rank.SEVEN), "== is reference identity")

	# --- Deck ---
	var std := Deck.build_standard_deck()
	_check(std.size() == 52, "standard deck is 52")
	var om := Deck.build_old_maid_deck()
	_check(om.size() == 49, "old maid deck is 49")
	var queens := om.filter(func(x): return x.rank == Card.Rank.QUEEN)
	_check(queens.is_empty(), "old maid deck has no queens")
	_check(om.filter(func(x): return x.is_odd_one).size() == 1, "old maid deck has exactly one odd card")
	var mem := Deck.build_memory_deck(6)
	_check(mem.size() == 12, "memory deck 6 pairs -> 12 cards")
	# invalid input -> safe empty return (legacy raised ValueError)
	_check(Deck.build_memory_deck(0).is_empty(), "build_memory_deck(0) -> []")
	_check(Deck.build_memory_deck(14).is_empty(), "build_memory_deck(14) -> []")
	_check((Deck.deal_all(std, 0) as Array).is_empty(), "deal_all(_, 0) -> []")
	var bad := Deck.deal_count(std, 4, 20)
	_check((bad["hands"] as Array).is_empty(), "deal_count with undersized deck -> empty hands")

	var rng := RandomNumberGenerator.new()
	rng.seed = 12345
	var sh := Deck.shuffled(std, rng)
	_check(sh.size() == 52, "shuffled preserves count")
	_check(std.size() == 52, "shuffled did not mutate source")
	var same_order := true
	for i in std.size():
		if sh[i] != std[i]:
			same_order = false
			break
	_check(not same_order, "shuffled changed order")

	var dealt := Deck.deal_all(om, 3)
	var total := 0
	for h in dealt:
		total += h.size()
	_check(total == 49 and dealt.size() == 3, "deal_all distributes every card")

	var dc := Deck.deal_count(std, 2, 7)
	_check(dc["hands"][0].size() == 7 and dc["hands"][1].size() == 7, "deal_count hand sizes")
	_check(dc["stock"].size() == 52 - 14, "deal_count stock remainder")

	# --- Hand ---
	var hand := Hand.new()
	hand.add(Card.new(Card.Suit.CLUBS, Card.Rank.FIVE))
	hand.add(Card.new(Card.Suit.HEARTS, Card.Rank.FIVE))
	hand.add(Card.new(Card.Suit.SPADES, Card.Rank.KING))
	_check(hand.size() == 3, "hand size")
	_check(hand.count_of_rank(Card.Rank.FIVE) == 2, "count_of_rank")
	_check(hand.has_rank(Card.Rank.KING) and not hand.has_rank(Card.Rank.ACE), "has_rank")
	hand.add(Card.new(Card.Suit.DIAMONDS, Card.Rank.TWO))  # lower rank added last
	_check(hand.ranks_present() == [Card.Rank.TWO, Card.Rank.FIVE, Card.Rank.KING],
		"ranks_present distinct + sorted ascending by rank value")
	hand.remove_all_of_rank(Card.Rank.TWO)
	var pulled := hand.remove_all_of_rank(Card.Rank.FIVE)
	_check(pulled.size() == 2 and hand.size() == 1, "remove_all_of_rank")
	var last := hand.cards[0]
	hand.remove(last)
	_check(hand.is_empty(), "remove by reference empties hand")

	# --- Player ---
	var p := Player.new("Alex", true)
	_check(p.display_name == "Alex" and p.is_ai and p.hand != null and p.score == 0, "player init")

	# --- AIStrategy ---
	var s := AIStrategy.new(AIStrategy.Difficulty.HARD, rng)
	_check(s.label() == "Sneaky Fox", "difficulty label")
	var tally := {"a": 0, "b": 0, "c": 0}
	for _n in 3000:
		tally[s.weighted_choice(["a", "b", "c"], [1.0, 3.0, 0.0])] += 1
	_check(tally["c"] == 0, "zero-weight option never chosen")
	_check(tally["b"] > tally["a"], "higher weight chosen more often (b > a)")

	print("== done: %d failure(s) ==" % _failures)
	quit(1 if _failures > 0 else 0)
