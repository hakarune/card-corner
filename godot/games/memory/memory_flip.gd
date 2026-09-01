class_name MemoryFlip
extends RefCounted
## Result of one Memory two-card flip. Ported from FlipResult
## (legacy/games/memory/game.py). All fields set at construction.


class Result extends RefCounted:
	var player: String
	var pos1: int
	var pos2: int
	var rank1: int
	var rank2: int
	var matched: bool
	var went_again: bool

	func _init(p_player: String, p1: int, p2: int, r1: int, r2: int, p_matched: bool) -> void:
		player = p_player
		pos1 = p1
		pos2 = p2
		rank1 = r1
		rank2 = r2
		matched = p_matched
		went_again = p_matched
