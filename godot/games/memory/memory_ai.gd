class_name MemoryStrategy
extends AIStrategy
## Memory/Concentration AI. Ported from legacy/core/ai/memory_ai.py.
##
## Difficulty is expressed ENTIRELY through recall reliability -- never
## cheating. `known_positions` is the shared public reveal history (every
## position any player has ever flipped face-up); each tier applies its own
## recall probability on top of that public info.

const RECALL_CHANCE := {
	AIStrategy.Difficulty.EASY: 0.15,
	AIStrategy.Difficulty.MEDIUM: 0.5,
	AIStrategy.Difficulty.HARD: 0.85,
}


## Choose two distinct positions to flip. If recall turns up two remembered
## positions sharing a rank, flip exactly those; else fall back to random
## for whatever memory didn't supply. Returns { "pos1": int, "pos2": int }.
func decide_flips(known_positions: Dictionary, unflipped: Array) -> Dictionary:
	if unflipped.size() < 2:
		push_error("MemoryStrategy.decide_flips: need at least two unflipped positions")
		return {}

	var unflipped_set := {}
	for p in unflipped:
		unflipped_set[p] = true

	var remembered := _recalled(known_positions, unflipped_set)
	var by_rank := {}
	for pos in remembered:
		var rank: int = remembered[pos]
		if not by_rank.has(rank):
			by_rank[rank] = []
		by_rank[rank].append(pos)
	for rank in by_rank:
		var positions: Array = by_rank[rank]
		if positions.size() >= 2:
			return { "pos1": positions[0], "pos2": positions[1] }

	var first: int = unflipped[rng.randi_range(0, unflipped.size() - 1)]
	var remaining: Array = unflipped.filter(func(p): return p != first)
	var second: int = remaining[rng.randi_range(0, remaining.size() - 1)]
	return { "pos1": first, "pos2": second }


func _recalled(known_positions: Dictionary, unflipped_set: Dictionary) -> Dictionary:
	var chance: float = RECALL_CHANCE[difficulty]
	var out := {}
	for pos in known_positions:
		if unflipped_set.has(pos) and rng.randf() < chance:
			out[pos] = known_positions[pos]
	return out
