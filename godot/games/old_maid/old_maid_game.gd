class_name OldMaidGame
extends RefCounted
## Old Maid engine: deal, pair-discard, blind draws, single-loser end state.
## Ported from legacy/games/old_maid/game.py.

const MAX_TURNS := 400

var is_valid := true
var rng: RandomNumberGenerator
var order: Array = []
var players := {}                 ## name -> Player
var strategies := {}              ## name -> OldMaidStrategy
var turn_index := 0
var turn_count := 0
var game_over := false
var loser := ""                   ## "" = no single loser (tie / stalemate)
var stalemate := false


## On an invalid player list: logs an error, leaves the object half-built
## and game_over -- CALLERS MUST CHECK `is_valid` before use.
func _init(player_names: Array, ai_difficulties: Dictionary = {}, seed_val: int = -1) -> void:
	if player_names.size() < 2 or player_names.size() > 4:
		push_error("OldMaidGame: supports 2-4 players, got %d" % player_names.size())
		is_valid = false
	var uniq := {}
	for n in player_names:
		uniq[n] = true
	if uniq.size() != player_names.size():
		push_error("OldMaidGame: player names must be unique")
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
		strategies[name] = OldMaidStrategy.new(ai_difficulties[name], child)

	var deck := Deck.shuffled(Deck.build_old_maid_deck(), rng)
	var hands := Deck.deal_all(deck, player_names.size())
	for i in player_names.size():
		players[player_names[i]].hand.add_many(hands[i])

	for name in order:
		_discard_pairs(name)
	_advance_to_next_active(true)
	_check_game_over()


func current_player_name() -> String:
	return order[turn_index]


func active_player_names() -> Array:
	return order.filter(func(n): return not players[n].hand.is_empty())


func other_active_names(name: String) -> Array:
	return active_player_names().filter(func(n): return n != name)


func is_ai_turn() -> bool:
	return players[current_player_name()].is_ai


func take_ai_turn() -> OldMaidDraw.Result:
	var name := current_player_name()
	if not strategies.has(name):
		push_error("OldMaidGame.take_ai_turn: %s is not AI-controlled" % name)
		return null
	var opponents := other_active_names(name)
	var sizes := {}
	for n in opponents:
		sizes[n] = players[n].hand.size()
	var target: String = strategies[name].decide_target(sizes)
	if target == "":
		return null
	return draw(name, target)


func draw(drawer_name: String, target_name: String) -> OldMaidDraw.Result:
	if game_over:
		push_error("OldMaidGame.draw: game is already over")
		return null
	if drawer_name != current_player_name():
		push_error("OldMaidGame.draw: not this player's turn")
		return null
	if target_name == drawer_name:
		push_error("OldMaidGame.draw: cannot draw from yourself")
		return null
	if not players.has(target_name):
		push_error("OldMaidGame.draw: unknown target player: %s" % target_name)
		return null
	var target_hand: Hand = players[target_name].hand
	if target_hand.is_empty():
		push_error("OldMaidGame.draw: target has no cards to draw")
		return null

	# Blind draw: a uniformly random face-down position (game RNG, all tiers).
	var index := rng.randi_range(0, target_hand.cards.size() - 1)
	var card: Card = target_hand.cards.pop_at(index)
	var drawer: Player = players[drawer_name]
	drawer.hand.add(card)

	var paired := _discard_pairs(drawer_name)
	var result := OldMaidDraw.Result.new(drawer_name, target_name, card)
	result.paired_ranks = paired
	result.drawer_now_empty = drawer.hand.is_empty()
	result.target_now_empty = target_hand.is_empty()

	turn_count += 1
	_advance_turn()
	_check_game_over()
	return result


## Discard every complete pair currently in this hand (floor division so a
## count of 3-4 is handled), leaving at most one unpaired card of that rank.
func _discard_pairs(name: String) -> Array[int]:
	var player: Player = players[name]
	var cleared: Array[int] = []
	# ranks_present() is pre-sorted ascending by rank value -- load-bearing:
	# leftover odd cards get re-appended in this order and draw() does a
	# positional blind draw, so an unstable order breaks same-seed replay.
	for rank in player.hand.ranks_present():
		var count := player.hand.count_of_rank(rank)
		var pairs := count / 2
		if pairs == 0:
			continue
		var matched := player.hand.remove_all_of_rank(rank)
		var leftover := matched.slice(0, count % 2)
		for c in leftover:
			player.hand.add(c)
		for _i in pairs:
			cleared.append(rank)
			player.books.append(rank)
	return cleared


func _advance_turn() -> void:
	_advance_to_next_active(false)


func _advance_to_next_active(allow_same: bool) -> void:
	var n := order.size()
	var start := 0 if allow_same else 1
	for step in range(start, n + 1):
		var idx := (turn_index + step) % n
		if not players[order[idx]].hand.is_empty():
			turn_index = idx
			return
	# No active players remain; _check_game_over handles it.


func _check_game_over() -> void:
	if game_over:
		return
	var active := active_player_names()
	var stalemate_flag := turn_count >= MAX_TURNS
	if active.size() <= 1 or stalemate_flag:
		game_over = true
		stalemate = stalemate_flag and active.size() > 1
		loser = active[0] if active.size() == 1 else ""


func has_loser() -> bool:
	return loser != ""
