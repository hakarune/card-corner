extends "res://tests/test_case.gd"
## Ported from legacy/tests/unit/test_go_fish_ai.py -- pins each AI branch
## (full-game tests can't tell EASY from HARD or catch a wrong constant).

const D := AIStrategy.Difficulty
const S := Card.Suit
const RK := Card.Rank


func _hand_of(ranks: Array) -> Hand:
	var h := Hand.new()
	for r in ranks:
		h.add(Card.new(S.CLUBS, r))
	return h


func _seeded(s: int) -> RandomNumberGenerator:
	var rng := RandomNumberGenerator.new()
	rng.seed = s
	return rng


func _rec(target: String, rank: int) -> GoFishAsk.Record:
	return GoFishAsk.Record.new("Someone", target, rank, 0)


func _init() -> void:
	# --- only offers ranks actually held ---
	var strat := GoFishStrategy.new(D.EASY, _seeded(1))
	var hand := _hand_of([RK.THREE, RK.NINE])
	var ok := true
	for _n in 60:
		var d := strat.decide_ask(hand, ["Bob"], [])
		if d["rank"] != RK.THREE and d["rank"] != RK.NINE:
			ok = false
	check(ok, "decide_ask only offers ranks actually held")

	# --- degenerate inputs return {} ---
	check(GoFishStrategy.new(D.EASY, _seeded(1)).decide_ask(Hand.new(), ["Bob"], []).is_empty(),
		"empty hand -> {}")
	check(GoFishStrategy.new(D.EASY, _seeded(1)).decide_ask(_hand_of([RK.THREE]), [], []).is_empty(),
		"no opponents -> {}")

	# --- targets only known opponents ---
	strat = GoFishStrategy.new(D.HARD, _seeded(1))
	hand = _hand_of([RK.THREE])
	ok = true
	for _n in 60:
		var t: String = strat.decide_ask(hand, ["Bob", "Sue"], [])["target"]
		if t != "Bob" and t != "Sue":
			ok = false
	check(ok, "decide_ask targets only known opponents")

	# --- non-determinism across seeds ---
	hand = _hand_of([RK.TWO, RK.FIVE, RK.NINE])
	var seen := {}
	for seed in range(100):
		var d := GoFishStrategy.new(D.EASY, _seeded(seed)).decide_ask(hand, ["Bob", "Sue"], [])
		seen["%s/%d" % [d["target"], d["rank"]]] = true
	check(seen.size() > 1, "varied seeds surface more than one outcome")

	# --- HARD deprioritizes (but doesn't forbid) a confirmed-absent rank ---
	hand = _hand_of([RK.SEVEN])
	var history := [_rec("Bob", RK.SEVEN)]
	var cnt := {"Bob": 0, "Sue": 0}
	for seed in range(500):
		var t: String = GoFishStrategy.new(D.HARD, _seeded(seed)).decide_ask(hand, ["Bob", "Sue"], history)["target"]
		cnt[t] += 1
	check(cnt["Bob"] > 0 and cnt["Bob"] < cnt["Sue"], "HARD: confirmed-absent target asked less, never zero")

	# --- HARD favors ranks with more unseen copies ---
	hand = Hand.new()
	hand.add(Card.new(S.CLUBS, RK.KING))
	hand.add(Card.new(S.CLUBS, RK.TWO)); hand.add(Card.new(S.HEARTS, RK.TWO)); hand.add(Card.new(S.SPADES, RK.TWO))
	cnt = {RK.KING: 0, RK.TWO: 0}
	for seed in range(500):
		var r: int = GoFishStrategy.new(D.HARD, _seeded(seed)).decide_ask(hand, ["Bob"], [])["rank"]
		cnt[r] += 1
	check(cnt[RK.KING] > cnt[RK.TWO] and cnt[RK.TWO] > 0, "HARD favors KING (3 unseen) over TWO (1 unseen), TWO still occurs")

	# --- HARD favors ranks with no book claimed yet ---
	hand = _hand_of([RK.KING, RK.TWO])
	var books_claimed := {RK.TWO: 1}
	cnt = {RK.KING: 0, RK.TWO: 0}
	for seed in range(500):
		var r: int = GoFishStrategy.new(D.HARD, _seeded(seed)).decide_ask(hand, ["Bob"], [], [], books_claimed)["rank"]
		cnt[r] += 1
	check(cnt[RK.KING] > cnt[RK.TWO] and cnt[RK.TWO] > 0, "HARD favors KING (no book) over TWO (one book claimed)")

	# --- books_claimed default is no-signal / no crash ---
	var d := GoFishStrategy.new(D.HARD, _seeded(1)).decide_ask(_hand_of([RK.KING]), ["Bob"], [])
	check(d["rank"] == RK.KING, "omitting books_claimed_by_rank is safe")

	# --- MEDIUM forgets all but the most recent same-turn miss ---
	hand = _hand_of([RK.TWO, RK.FIVE])
	seen = {}
	for seed in range(60):
		var r: int = GoFishStrategy.new(D.MEDIUM, _seeded(seed)).decide_ask(hand, ["Bob"], [], [RK.TWO, RK.FIVE])["rank"]
		seen[r] = true
	check(seen.size() == 1 and seen.has(RK.TWO), "MEDIUM excludes only the last same-turn miss (FIVE), keeps TWO")

	# --- HARD excludes every same-turn miss ---
	hand = _hand_of([RK.TWO, RK.FIVE, RK.NINE])
	seen = {}
	for seed in range(60):
		var r: int = GoFishStrategy.new(D.HARD, _seeded(seed)).decide_ask(hand, ["Bob"], [], [RK.TWO, RK.FIVE])["rank"]
		seen[r] = true
	check(seen.size() == 1 and seen.has(RK.NINE), "HARD excludes TWO and FIVE, leaves NINE")

	# --- exclusion never leaves zero candidates ---
	var r2: int = GoFishStrategy.new(D.HARD, _seeded(1)).decide_ask(
		_hand_of([RK.TWO, RK.FIVE]), ["Bob"], [], [RK.TWO, RK.FIVE])["rank"]
	check(r2 == RK.TWO or r2 == RK.FIVE, "all-ranks-failed -> exclusion backs off")

	# --- EASY roughly uniform over ranks (ignores count) ---
	hand = Hand.new()
	hand.add(Card.new(S.CLUBS, RK.TWO)); hand.add(Card.new(S.HEARTS, RK.TWO)); hand.add(Card.new(S.SPADES, RK.TWO))
	hand.add(Card.new(S.CLUBS, RK.KING))
	cnt = {RK.KING: 0, RK.TWO: 0}
	for seed in range(1000):
		var r: int = GoFishStrategy.new(D.EASY, _seeded(seed)).decide_ask(hand, ["Bob"], [])["rank"]
		cnt[r] += 1
	var ratio: float = float(cnt[RK.TWO]) / max(cnt[RK.KING], 1)
	check(ratio > 0.7 and ratio < 1.4, "EASY is ~uniform over ranks regardless of count")

	finish("go_fish_ai")
