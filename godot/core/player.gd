class_name Player
extends RefCounted
## Player abstraction shared by Go Fish, Old Maid, and Memory.
## Ported from legacy/core/player.py (Player).

var display_name: String = ""
var is_ai: bool = false
var hand: Hand = null
var books: Array[int] = []  ## Go Fish: ranks scored as books (Card.Rank values).
var score: int = 0


func _init(p_name: String = "", p_is_ai: bool = false) -> void:
	display_name = p_name
	is_ai = p_is_ai
	hand = Hand.new()
	books = []
	score = 0
