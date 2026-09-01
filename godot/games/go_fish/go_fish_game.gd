class_name GoFishGame
extends RefCounted
## Go Fish engine: rules, turn order, book (pair) scoring.
## Ported from legacy/games/go_fish/game.py.
##
## A "book" is a PAIR (2 of a rank), not 4-of-a-kind -- a simplified variant
## for this age group. 13 ranks x up to 2 pairs = 26 books using all 52 cards.
## Supports 2-4 players; any subset may be AI via `ai_difficulties`.

const MAX_TURNS := 400
const TOTAL_BOOKS := 26

var is_valid := true
var rng: RandomNumberGenerator
var order: Array = []                 ## player names, turn order
var players := {}                     ## name -> Player
var strategies := {}                  ## name -> GoFishStrategy (AI players only)
var stock: Array[Card] = []
var history: Array = []               ## of GoFishAsk.Record
var turn_index := 0
var turn_count := 0
var game_over := false
var winner := ""                      ## "" = no single winner (tie / not decided)
var stalemate := false

var _turn_failed_ranks: Array[int] = []


## `ai_difficulties`: name -> AIStrategy.Difficulty. `seed_val < 0` -> random.
## On an invalid player list this logs an error and leaves the object in a
## half-built, game_over state -- CALLERS MUST CHECK `is_valid` before use.
func _init(player_names: Array, ai_difficulties: Dictionary = {}, seed_val: int = -1) -> void:
	if player_names.size() < 2 or player_names.size() > 4:
		push_error("GoFishGame: supports 2-4 players, got %d" % player_names.size())
		is_valid = false
	var uniq := {}
	for n in player_names:
		uniq[n] = true
	if uniq.size() != player_names.size():
		push_error("GoFishGame: player names must be unique")
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
	# Each AI gets its own independent RNG, seeded from this game's RNG.
	for name in ai_difficulties:
		var child := RandomNumberGenerator.new()
		child.seed = rng.randi()
		strategies[name] = GoFishStrategy.new(ai_difficulties[name], child)

	var count_per_hand := 7 if player_names.size() == 2 else 5
	var deck := Deck.shuffled(Deck.build_standard_deck(), rng)
	var dealt := Deck.deal_count(deck, player_names.size(), count_per_hand)
	for i in player_names.size():
		players[player_names[i]].hand.add_many(dealt["hands"][i])
	stock.assign(dealt["stock"])

	for name in order:
		_claim_books(name)
	_ensure_current_player_can_act()
	_check_game_over()


func current_player_name() -> String:
	return order[turn_index]


func other_player_names(name: String) -> Array:
	return order.filter(func(n): return n != name)


func legal_ranks(name: String) -> Array:
	return players[name].hand.ranks_present()


func is_ai_turn() -> bool:
	return players[current_player_name()].is_ai


## rank -> count of books of that rank claimed by any player (public info).
func books_claimed_by_rank() -> Dictionary:
	var counts := {}
	for player in players.values():
		for rank in player.books:
			counts[rank] = counts.get(rank, 0) + 1
	return counts


## What the current AI would ask, without executing. { "target", "rank" }.
func decide_ai_ask() -> Dictionary:
	var name := current_player_name()
	if not strategies.has(name):
		push_error("GoFishGame.decide_ai_ask: %s is not AI-controlled" % name)
		return {}
	return strategies[name].decide_ask(
		players[name].hand,
		other_player_names(name),
		history,
		_turn_failed_ranks.duplicate(),
		books_claimed_by_rank(),
	)


func take_ai_turn() -> GoFishAsk.Result:
	var name := current_player_name()
	var d := decide_ai_ask()
	if d.is_empty():
		return null
	return ask(name, d["target"], d["rank"])


func ask(asker_name: String, target_name: String, rank: int) -> GoFishAsk.Result:
	if game_over:
		push_error("GoFishGame.ask: game is already over")
		return null
	if asker_name != current_player_name():
		push_error("GoFishGame.ask: not this player's turn")
		return null
	if target_name == asker_name:
		push_error("GoFishGame.ask: cannot ask yourself")
		return null
	if not players.has(target_name):
		push_error("GoFishGame.ask: unknown target player: %s" % target_name)
		return null
	var asker: Player = players[asker_name]
	var target: Player = players[target_name]
	if not asker.hand.has_rank(rank):
		push_error("GoFishGame.ask: can only ask for a rank you hold yourself")
		return null

	var transferred := target.hand.remove_all_of_rank(rank)
	var result := GoFishAsk.Result.new(asker_name, target_name, rank, transferred.size())
	history.append(GoFishAsk.Record.new(asker_name, target_name, rank, transferred.size()))

	var hit := false
	if not transferred.is_empty():
		asker.hand.add_many(transferred)
		result.books_claimed_by_asker = _claim_books(asker_name)
		hit = true
	else:
		_turn_failed_ranks.append(rank)
		var drawn := _draw(asker_name)
		if drawn != null:
			result.asker_drew = true
			if drawn.rank == rank:
				result.asker_drew_matched = true
			result.books_claimed_by_asker = _claim_books(asker_name)
			hit = result.asker_drew_matched

	if hit:
		# A pair claims a book the instant it forms, which can empty a
		# small hand right on the hit -- give a free redraw so a "go again"
		# turn always has a card to act with.
		if asker.hand.is_empty() and not stock.is_empty():
			_draw(asker_name)
			result.asker_drew = true
			result.books_claimed_by_asker.append_array(_claim_books(asker_name))
		result.went_again = not asker.hand.is_empty()

	turn_count += 1
	if not result.went_again:
		_turn_failed_ranks = []
		_advance_turn()
	_check_game_over()
	return result


func _draw(name: String) -> Card:
	if stock.is_empty():
		return null
	var card: Card = stock.pop_back()
	players[name].hand.add(card)
	return card


## Claims every complete pair in this hand (floor division, so a rank at
## count 3-4 claims 1-2 books at once), leaving at most one unpaired card.
func _claim_books(name: String) -> Array[int]:
	var player: Player = players[name]
	var claimed: Array[int] = []
	# ranks_present() is pre-sorted ascending by rank value (legacy sorted
	# it here explicitly for cross-run determinism).
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
			player.books.append(rank)
			claimed.append(rank)
		player.score += pairs
	return claimed


func _advance_turn() -> void:
	turn_index = (turn_index + 1) % order.size()
	_ensure_current_player_can_act()


## If the current player's hand is empty, give one free draw; if the stock
## is also empty, skip to the next player who can act.
func _ensure_current_player_can_act() -> void:
	var attempts := 0
	while attempts < order.size():
		var player: Player = players[current_player_name()]
		if not player.hand.is_empty():
			return
		if not stock.is_empty():
			_draw(current_player_name())
			_claim_books(current_player_name())
			if not player.hand.is_empty():
				return
		turn_index = (turn_index + 1) % order.size()
		attempts += 1


func _check_game_over() -> void:
	if game_over:
		return
	var total_books := 0
	var all_hands_empty := true
	for p in players.values():
		total_books += p.books.size()
		if not p.hand.is_empty():
			all_hands_empty = false
	var stalemate_flag := turn_count >= MAX_TURNS
	var deck_exhausted := stock.is_empty() and all_hands_empty

	if total_books == TOTAL_BOOKS or deck_exhausted or stalemate_flag:
		game_over = true
		stalemate = stalemate_flag and total_books != TOTAL_BOOKS and not deck_exhausted
		var best_count := 0
		for p in players.values():
			best_count = max(best_count, p.books.size())
		var tied: Array = []
		for p in players.values():
			if p.books.size() == best_count:
				tied.append(p.display_name)
		winner = tied[0] if tied.size() == 1 else ""


func has_winner() -> bool:
	return winner != ""
