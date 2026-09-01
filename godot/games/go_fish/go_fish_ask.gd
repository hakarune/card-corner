class_name GoFishAsk
extends RefCounted
## Value/result types for Go Fish asks. Ported from legacy AskRecord
## (core/ai/go_fish_ai.py) and AskResult (games/go_fish/game.py).


## Public record of one ask. `cards_transferred == 0` means a miss ("go
## fish"); otherwise the target handed over that many cards and is known
## (at that moment) to hold zero of `rank`.
class Record extends RefCounted:
	var asker: String
	var target: String
	var rank: int  ## Card.Rank
	var cards_transferred: int

	func _init(p_asker: String, p_target: String, p_rank: int, p_transferred: int) -> void:
		asker = p_asker
		target = p_target
		rank = p_rank
		cards_transferred = p_transferred


## Mutable outcome of a resolved ask, handed back to the screen.
class Result extends RefCounted:
	var asker: String
	var target: String
	var rank: int
	var cards_transferred: int
	var asker_drew := false
	var asker_drew_matched := false
	var went_again := false
	var books_claimed_by_asker: Array[int] = []

	func _init(p_asker: String, p_target: String, p_rank: int, p_transferred: int) -> void:
		asker = p_asker
		target = p_target
		rank = p_rank
		cards_transferred = p_transferred
