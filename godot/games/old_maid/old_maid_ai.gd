class_name OldMaidStrategy
extends AIStrategy
## Old Maid AI. Ported from legacy/core/ai/old_maid_ai.py.
##
## The only decision is WHO to blind-draw from among still-active opponents.
## Which card comes out is the engine's own randomness, not a strategy call.
## Sees only public info: each active opponent's current hand SIZE.


## `opponent_hand_sizes`: name -> current hand size (active opponents only).
## Returns the chosen opponent's name, or "" on no opponents.
func decide_target(opponent_hand_sizes: Dictionary) -> String:
	if opponent_hand_sizes.is_empty():
		push_error("OldMaidStrategy.decide_target: no opponents to draw from")
		return ""
	var names := opponent_hand_sizes.keys()
	var weights := _weights(opponent_hand_sizes, names)
	return weighted_choice(names, weights)


func _weights(opponent_hand_sizes: Dictionary, names: Array) -> Array:
	if difficulty == Difficulty.EASY:
		return names.map(func(_n): return 1.0)
	var exponent := 1.0 if difficulty == Difficulty.MEDIUM else 1.8
	# Bigger hands get proportionally more weight -- a mild, non-cheating
	# heuristic (hand size is public), not a guarantee.
	return names.map(func(n): return pow(float(max(opponent_hand_sizes[n], 1)), exponent))
