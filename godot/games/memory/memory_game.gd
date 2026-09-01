class_name MemoryGame
extends RefCounted
## Memory/Concentration engine: face-down board, two-flip turns, shared
## public reveal history. Ported from legacy/games/memory/game.py.
## Supports 1-4 players (1 = solo, no AI).

const MAX_TURNS := 500

var is_valid := true
var rng: RandomNumberGenerator
var order: Array = []
var players := {}                    ## name -> Player
var strategies := {}                 ## name -> MemoryStrategy
var board: Array[Card] = []
var matched := {}                    ## set of matched board positions (pos -> true)
var known_positions := {}            ## pos -> Card.Rank (public reveal history)
var turn_index := 0
var turn_count := 0
var game_over := false
var stalemate := false


## On an invalid player list: logs an error, leaves the object half-built
## and game_over -- CALLERS MUST CHECK `is_valid` before use.
func _init(player_names: Array, num_pairs: int = 8,
		ai_difficulties: Dictionary = {}, seed_val: int = -1) -> void:
	if player_names.size() < 1 or player_names.size() > 4:
		push_error("MemoryGame: supports 1-4 players, got %d" % player_names.size())
		is_valid = false
	var uniq := {}
	for n in player_names:
		uniq[n] = true
	if uniq.size() != player_names.size():
		push_error("MemoryGame: player names must be unique")
		is_valid = false
	if not is_valid:
		game_over = true
		return

	rng = RandomNumberGenerator.new()
	if seed_val >= 0:
		rng.seed = seed_val
	else:
		rng.randomize()

	order = player_names.duplicate()
	for name in player_names:
		players[name] = Player.new(name, ai_difficulties.has(name))
	for name in ai_difficulties:
		var child := RandomNumberGenerator.new()
		child.seed = rng.randi()
		strategies[name] = MemoryStrategy.new(ai_difficulties[name], child)

	board = Deck.shuffled(Deck.build_memory_deck(num_pairs), rng)


func current_player_name() -> String:
	return order[turn_index]


func unflipped_positions() -> Array:
	var out: Array = []
	for i in board.size():
		if not matched.has(i):
			out.append(i)
	return out


func is_ai_turn() -> bool:
	return players[current_player_name()].is_ai


func take_ai_turn() -> MemoryFlip.Result:
	var name := current_player_name()
	if not strategies.has(name):
		push_error("MemoryGame.take_ai_turn: %s is not AI-controlled" % name)
		return null
	var d: Dictionary = strategies[name].decide_flips(known_positions, unflipped_positions())
	if d.is_empty():
		return null
	return flip_two(name, d["pos1"], d["pos2"])


func flip_two(player_name: String, pos1: int, pos2: int) -> MemoryFlip.Result:
	if game_over:
		push_error("MemoryGame.flip_two: game is already over")
		return null
	if player_name != current_player_name():
		push_error("MemoryGame.flip_two: not this player's turn")
		return null
	if pos1 == pos2:
		push_error("MemoryGame.flip_two: must flip two different positions")
		return null
	for pos in [pos1, pos2]:
		if pos < 0 or pos >= board.size():
			push_error("MemoryGame.flip_two: position out of range: %d" % pos)
			return null
		if matched.has(pos):
			push_error("MemoryGame.flip_two: position already matched: %d" % pos)
			return null

	var card1 := board[pos1]
	var card2 := board[pos2]
	known_positions[pos1] = card1.rank
	known_positions[pos2] = card2.rank

	var is_match := card1.matches_rank(card2)
	if is_match:
		matched[pos1] = true
		matched[pos2] = true
		var player: Player = players[player_name]
		player.books.append(card1.rank)
		player.score += 1

	var result := MemoryFlip.Result.new(player_name, pos1, pos2, card1.rank, card2.rank, is_match)

	turn_count += 1
	if not is_match:
		turn_index = (turn_index + 1) % order.size()
	_check_game_over()
	return result


func _check_game_over() -> void:
	if game_over:
		return
	var all_matched := matched.size() == board.size()
	var stalemate_flag := turn_count >= MAX_TURNS
	if all_matched or stalemate_flag:
		game_over = true
		stalemate = stalemate_flag and not all_matched
