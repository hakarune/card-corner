class_name AIStrategy
extends RefCounted
## Shared AI difficulty tiers and the base per-game strategy.
## Ported from legacy/core/ai/base.py.
##
## Design rules (project spec §4):
##  * No hidden-information cheating -- a strategy may only reason over
##    information a real opponent would have.
##  * Non-determinism at every tier -- decisions go through weighted random
##    selection, never a fixed greedy rule; each strategy owns its own RNG.
##  * Difficulty tunes how good the weighting is, not whether randomness
##    exists -- Hard wins more than Easy over many games, but is never
##    unbeatable.

enum Difficulty { EASY, MEDIUM, HARD }

const DIFFICULTY_LABELS := {
	Difficulty.EASY: "Sleepy Fox",
	Difficulty.MEDIUM: "Clever Fox",
	Difficulty.HARD: "Sneaky Fox",
}

const DIFFICULTY_IDS := {
	Difficulty.EASY: "easy",
	Difficulty.MEDIUM: "medium",
	Difficulty.HARD: "hard",
}

var difficulty: Difficulty = Difficulty.EASY
var rng: RandomNumberGenerator = null


func _init(p_difficulty: int, p_rng: RandomNumberGenerator = null) -> void:
	difficulty = p_difficulty
	if p_rng != null:
		rng = p_rng
	else:
		rng = RandomNumberGenerator.new()
		rng.randomize()


func label() -> String:
	return DIFFICULTY_LABELS[difficulty]


## Pick one of `options` using `weights` via this strategy's own RNG.
## Mirrors Python's random.choices(options, weights=weights, k=1)[0]
## (cumulative-weight sampling: first index whose running sum exceeds
## randf()*total). Python raises on non-positive total; here that's a
## deliberate GDScript-side uniform fallback -- believed unreachable given
## current callers (all weights are strictly positive), kept defensive.
func weighted_choice(options: Array, weights: Array) -> Variant:
	if options.is_empty() or options.size() != weights.size():
		push_error("weighted_choice: need matching non-empty options/weights")
		return null
	var total := 0.0
	for w in weights:
		total += w
	if total <= 0.0:
		return options[rng.randi_range(0, options.size() - 1)]
	var pick := rng.randf() * total
	var acc := 0.0
	for i in options.size():
		acc += weights[i]
		if pick < acc:
			return options[i]
	return options[options.size() - 1]
