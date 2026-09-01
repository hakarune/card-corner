class_name Deck
extends RefCounted
## Deck construction, shuffling, and dealing. Ported from legacy/core/deck.py.
##
## All randomness is routed through an explicit RandomNumberGenerator passed
## by the caller, so games replay deterministically in tests while staying
## non-deterministic across real playthroughs. NOTE: Godot's RNG and shuffle
## algorithm differ from Python's random.Random, so a given seed does not
## reproduce the legacy Python sequence -- only in-engine determinism holds.

const _ALL_SUITS := [Card.Suit.CLUBS, Card.Suit.DIAMONDS, Card.Suit.HEARTS, Card.Suit.SPADES]


## A standard 52-card deck, unshuffled (suit-major, matching the legacy order).
static func build_standard_deck() -> Array[Card]:
	var out: Array[Card] = []
	for s in _ALL_SUITS:
		for r in range(Card.Rank.ACE, Card.Rank.KING + 1):
			out.append(Card.new(s, r))
	return out


## Standard 52 with all four Queens removed, plus the single permanently
## unmatched "Old Maid" card (49 total).
static func build_old_maid_deck() -> Array[Card]:
	var out: Array[Card] = []
	for c in build_standard_deck():
		if c.rank != Card.Rank.QUEEN:
			out.append(c)
	out.append(Card.make_odd_card())
	return out


## `num_pairs` pairs of same-rank cards (distinguished by suit), 1..13.
## On invalid input: logs an error and returns []. (Legacy raised ValueError;
## GDScript has no exceptions and asserts are stripped from exported builds,
## so a testable + release-safe error path is used instead.)
static func build_memory_deck(num_pairs: int) -> Array[Card]:
	if num_pairs < 1 or num_pairs > 13:
		push_error("build_memory_deck: num_pairs must be between 1 and 13, got %d" % num_pairs)
		return [] as Array[Card]
	var suits := [Card.Suit.HEARTS, Card.Suit.SPADES]
	var out: Array[Card] = []
	for r in range(Card.Rank.ACE, Card.Rank.ACE + num_pairs):
		for s in suits:
			out.append(Card.new(s, r))
	return out


## A new shuffled Array; does not mutate `cards`. Fisher-Yates via `rng`.
static func shuffled(cards: Array[Card], rng: RandomNumberGenerator) -> Array[Card]:
	var out: Array[Card] = cards.duplicate()
	for i in range(out.size() - 1, 0, -1):
		var j := rng.randi_range(0, i)
		var tmp := out[i]
		out[i] = out[j]
		out[j] = tmp
	return out


## Round-robin deal every card into `num_hands` hands (sizes may be uneven).
## Returns an untyped Array whose elements are each Array[Card] (a static
## Array[Array[Card]] return type isn't expressible in GDScript 4.x; a typed
## local needs `.assign()`). On num_hands < 1: logs an error, returns [].
static func deal_all(cards: Array[Card], num_hands: int) -> Array:
	if num_hands < 1:
		push_error("deal_all: num_hands must be at least 1, got %d" % num_hands)
		return []
	var hands: Array = []
	for _i in num_hands:
		var h: Array[Card] = []
		hands.append(h)
	for i in cards.size():
		hands[i % num_hands].append(cards[i])
	return hands


## Deal exactly `count_per_hand` cards to each of `num_hands` hands,
## round-robin. Returns { "hands": Array (of Array[Card]), "stock": Array[Card] }.
## (A typed local for "hands" needs `.assign()`.) On invalid input or an
## under-sized deck: logs an error and returns { "hands": [], "stock": [] }.
static func deal_count(cards: Array[Card], num_hands: int, count_per_hand: int) -> Dictionary:
	if num_hands < 1:
		push_error("deal_count: num_hands must be at least 1, got %d" % num_hands)
		return { "hands": [], "stock": [] as Array[Card] }
	if num_hands * count_per_hand > cards.size():
		push_error("deal_count: not enough cards (%d) to deal %d x %d" % [cards.size(), num_hands, count_per_hand])
		return { "hands": [], "stock": [] as Array[Card] }
	var hands: Array = []
	for _i in num_hands:
		var h: Array[Card] = []
		hands.append(h)
	var idx := 0
	for _round in count_per_hand:
		for hnd in num_hands:
			hands[hnd].append(cards[idx])
			idx += 1
	var stock: Array[Card] = []
	for k in range(idx, cards.size()):
		stock.append(cards[k])
	return { "hands": hands, "stock": stock }
