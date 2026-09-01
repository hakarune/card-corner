class_name LetterMatchGame
extends RefCounted
## Letter Match: a solo, non-adversarial mini-game matching uppercase
## letters to their lowercase counterparts. No AI, no win/lose framing.
## Ported from legacy/games/letter_match/game.py.
##
## click() never errors for "silly but plausible" UI input (double-tap,
## re-tapping a matched tile, tapping the pending tile again) -- those just
## return an un-accepted ClickResult. Only a truly out-of-range index
## (a bug, never legit UI) logs an error.

const DEFAULT_LETTER_COUNT := 6
const ANIMAL_MODE_LETTERS := ["B", "C", "D", "F", "L", "O", "P"]
const _UPPERCASE := "ABCDEFGHIJKLMNOPQRSTUVWXYZ"


class Tile extends RefCounted:
	var letter: String       ## always the uppercase identity, e.g. "B"
	var is_upper: bool
	var is_animal: bool

	func _init(p_letter: String, p_is_upper: bool, p_is_animal := false) -> void:
		letter = p_letter
		is_upper = p_is_upper
		is_animal = p_is_animal

	func display() -> String:
		return letter if is_upper else letter.to_lower()


class ClickResult extends RefCounted:
	var accepted: bool
	var pos1: int = -1
	var pos2: int = -1
	var matched: bool = false
	var reason: String = ""

	func _init(p_accepted: bool, p1: int = -1, p2: int = -1, p_matched := false, p_reason := "") -> void:
		accepted = p_accepted
		pos1 = p1
		pos2 = p2
		matched = p_matched
		reason = p_reason


var is_valid := true
var mode := "letters"
var rng: RandomNumberGenerator
var board: Array = []                 ## of Tile
var matched := {}                     ## set of matched positions
var attempts := 0
var correct := 0
var game_over := false

var _pending_first := -1


func _init(letter_count: int = DEFAULT_LETTER_COUNT, seed_val: int = -1, p_mode := "letters") -> void:
	if p_mode != "letters" and p_mode != "animals":
		push_error("LetterMatchGame: mode must be 'letters' or 'animals'")
		is_valid = false
		game_over = true
		return
	mode = p_mode
	var pool: Array = ANIMAL_MODE_LETTERS.duplicate() if mode == "animals" else _letters_pool()
	if letter_count < 1 or letter_count > pool.size():
		push_error("LetterMatchGame: letter_count must be 1..%d for mode=%s" % [pool.size(), mode])
		is_valid = false
		game_over = true
		return

	rng = RandomNumberGenerator.new()
	if seed_val >= 0:
		rng.seed = seed_val
	else:
		rng.randomize()

	var letters := _sample(pool, letter_count)
	for l in letters:
		board.append(Tile.new(l, true))
	for l in letters:
		board.append(Tile.new(l, false, mode == "animals"))
	_shuffle(board)


func unflipped_positions() -> Array:
	var out: Array = []
	for i in board.size():
		if not matched.has(i):
			out.append(i)
	return out


func pending_first() -> int:
	return _pending_first


func accuracy() -> float:
	return float(correct) / attempts if attempts > 0 else 0.0


func click(pos: int) -> ClickResult:
	if pos < 0 or pos >= board.size():
		push_error("LetterMatchGame.click: position out of range: %d" % pos)
		return ClickResult.new(false, -1, -1, false, "out of range")
	if game_over:
		return ClickResult.new(false, -1, -1, false, "game already complete")
	if matched.has(pos):
		return ClickResult.new(false, -1, -1, false, "already matched")

	if _pending_first == -1:
		_pending_first = pos
		return ClickResult.new(true, pos)

	if pos == _pending_first:
		return ClickResult.new(false, -1, -1, false, "same tile as pending pick")

	var first := _pending_first
	_pending_first = -1
	attempts += 1

	var t1: Tile = board[first]
	var t2: Tile = board[pos]
	var is_match := t1.letter == t2.letter and t1.is_upper != t2.is_upper
	if is_match:
		matched[first] = true
		matched[pos] = true
		correct += 1

	if matched.size() == board.size():
		game_over = true
	elif is_match:
		_reshuffle_unmatched()

	return ClickResult.new(true, first, pos, is_match)


## Spec §8: reshuffle the still-unmatched tiles after each success so the
## board isn't position-memorizable; solved slots stay put.
func _reshuffle_unmatched() -> void:
	var positions := unflipped_positions()
	var tiles: Array = positions.map(func(p): return board[p])
	_shuffle(tiles)
	for i in positions.size():
		board[positions[i]] = tiles[i]


func _letters_pool() -> Array:
	var out: Array = []
	for i in _UPPERCASE.length():
		out.append(_UPPERCASE[i])
	return out


## k distinct elements of `pool` (Python random.sample analogue).
func _sample(pool: Array, k: int) -> Array:
	var copy := pool.duplicate()
	_shuffle(copy)
	return copy.slice(0, k)


func _shuffle(arr: Array) -> void:
	for i in range(arr.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var tmp = arr[i]
		arr[i] = arr[j]
		arr[j] = tmp
