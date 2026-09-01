class_name GoFishStrategy
extends AIStrategy
## Go Fish AI. Ported from legacy/core/ai/go_fish_ai.py.
##
## Only ever looks at (a) its own hand and (b) the shared public ask history
## -- never another player's hand or the stock order (no-cheating rule,
## project spec §4).


## Returns { "target": String, "rank": int } to ask for. `my_hand` must be
## non-empty and there must be at least one opponent.
##
## `same_turn_failed_ranks` (oldest-first) lists ranks this player already
## asked and missed on earlier in this same continuous "go again" turn.
## `books_claimed_by_rank` maps Card.Rank -> count of books of that rank
## claimed by ANY player so far (public info).
func decide_ask(my_hand: Hand, opponent_names: Array, history: Array,
		same_turn_failed_ranks: Array = [], books_claimed_by_rank: Dictionary = {}) -> Dictionary:
	# Hand.ranks_present() is already sorted ascending by rank value, which
	# pins weighted_choice's candidate order for same-seed reproducibility.
	var candidate_ranks: Array = my_hand.ranks_present().duplicate()
	if candidate_ranks.is_empty():
		push_error("GoFishStrategy.decide_ask: empty hand")
		return {}
	if opponent_names.is_empty():
		push_error("GoFishStrategy.decide_ask: no opponents")
		return {}

	var exclude := _same_turn_exclusions(same_turn_failed_ranks)
	var smarter: Array = []
	for r in candidate_ranks:
		if not exclude.has(r):
			smarter.append(r)
	if not smarter.is_empty():
		candidate_ranks = smarter

	var rank_weights := _rank_weights(my_hand, candidate_ranks, opponent_names, history, books_claimed_by_rank)
	var rank: int = weighted_choice(candidate_ranks, rank_weights)

	var opp_weights := _opponent_weights(opponent_names, rank, history)
	var target: String = weighted_choice(opponent_names, opp_weights)
	return { "target": target, "rank": rank }


func _same_turn_exclusions(same_turn_failed_ranks: Array) -> Array:
	if difficulty == Difficulty.EASY:
		return []
	if difficulty == Difficulty.MEDIUM:
		return [same_turn_failed_ranks[-1]] if not same_turn_failed_ranks.is_empty() else []
	# HARD: remembers every miss this turn
	return same_turn_failed_ranks.duplicate()


func _rank_weights(hand: Hand, ranks: Array, opponent_names: Array,
		history: Array, books_claimed_by_rank: Dictionary) -> Array:
	var weights: Array = []
	for rank in ranks:
		var count := hand.count_of_rank(rank)
		var claimed: int = books_claimed_by_rank.get(rank, 0)
		weights.append(_base_weight(count, claimed) * _best_opponent_multiplier(rank, opponent_names, history))
	return weights


func _base_weight(count: int, books_claimed: int) -> float:
	if difficulty == Difficulty.EASY:
		return 1.0
	var remaining_unseen: int = max(0, 4 - count - 2 * books_claimed)
	if difficulty == Difficulty.MEDIUM:
		return 1.0 + remaining_unseen
	return 1.0 + float(remaining_unseen) ** 2  # HARD leans into it harder


func _best_opponent_multiplier(rank: int, opponent_names: Array, history: Array) -> float:
	if difficulty == Difficulty.EASY:
		return 1.0
	var discount := 0.6 if difficulty == Difficulty.MEDIUM else 0.3
	var best := 0.0
	for name in opponent_names:
		var confirmed_absent := false
		for h in history:
			if h.target == name and h.rank == rank:
				confirmed_absent = true
				break
		best = max(best, discount if confirmed_absent else 1.0)
	return best if best > 0.0 else 1.0


func _opponent_weights(opponent_names: Array, rank: int, history: Array) -> Array:
	var weights := {}
	for name in opponent_names:
		weights[name] = 1.0
	if difficulty == Difficulty.EASY:
		return opponent_names.map(func(n): return weights[n])

	var discount := 0.6 if difficulty == Difficulty.MEDIUM else 0.3
	for name in opponent_names:
		var relevant := false
		for h in history:
			if h.target == name and h.rank == rank:
				relevant = true
				break
		if relevant:
			# Most recent public outcome for (name, rank): hit or miss both
			# mean they held zero of that rank at the time -- deprioritize,
			# never rule out (they may have drawn into it since).
			weights[name] *= discount
	return opponent_names.map(func(n): return weights[n])
