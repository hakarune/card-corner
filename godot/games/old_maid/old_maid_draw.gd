class_name OldMaidDraw
extends RefCounted
## Result of one Old Maid blind draw. Ported from DrawResult
## (legacy/games/old_maid/game.py).


class Result extends RefCounted:
	var drawer: String
	var target: String
	var card: Card
	var paired_ranks: Array[int] = []
	var drawer_now_empty := false
	var target_now_empty := false

	func _init(p_drawer: String, p_target: String, p_card: Card) -> void:
		drawer = p_drawer
		target = p_target
		card = p_card
