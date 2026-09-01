class_name Card
extends RefCounted
## A single playing card. Ported from legacy/core/card.py.
##
## Immutable by convention: fields are set once in _init() and never mutated.
## Equality is REFERENCE identity (GDScript can't overload ==), so game code
## must thread the same Card instance through hands/piles rather than
## reconstructing one to match. Use equals() for value comparison (tests).

enum Suit { CLUBS, DIAMONDS, HEARTS, SPADES }

## Values match the legacy Python (ACE = 1 .. KING = 13) so rank arithmetic
## and "first N ranks" slicing port directly.
enum Rank {
	ACE = 1, TWO, THREE, FOUR, FIVE, SIX, SEVEN, EIGHT, NINE, TEN, JACK, QUEEN, KING
}

## Sentinel used for the odd card's suit/rank (Python used None).
const NONE := -1

const RANK_LABELS := {
	Rank.ACE: "A", Rank.TWO: "2", Rank.THREE: "3", Rank.FOUR: "4", Rank.FIVE: "5",
	Rank.SIX: "6", Rank.SEVEN: "7", Rank.EIGHT: "8", Rank.NINE: "9", Rank.TEN: "10",
	Rank.JACK: "J", Rank.QUEEN: "Q", Rank.KING: "K",
}

const SUIT_SYMBOLS := {
	Suit.CLUBS: "♣", Suit.DIAMONDS: "♦", Suit.HEARTS: "♥", Suit.SPADES: "♠",
}

const SUIT_NAMES := {
	Suit.CLUBS: "clubs", Suit.DIAMONDS: "diamonds", Suit.HEARTS: "hearts", Suit.SPADES: "spades",
}

const RED_SUITS := [Suit.DIAMONDS, Suit.HEARTS]

## Emoji stand-in art for the "Old Maid" card (legacy used U+1F638).
const ODD_SYMBOL := "\U0001F638"

var suit: int = NONE  ## Card.Suit value, or NONE for the odd card.
var rank: int = NONE  ## Card.Rank value, or NONE for the odd card.
var is_odd_one: bool = false


func _init(p_suit: int = NONE, p_rank: int = NONE, p_is_odd_one: bool = false) -> void:
	suit = p_suit
	rank = p_rank
	is_odd_one = p_is_odd_one
	if is_odd_one:
		assert(suit == NONE and rank == NONE, "the odd card must have suit=NONE and rank=NONE")
	else:
		assert(suit != NONE and rank != NONE, "non-odd cards must have both suit and rank")


## The single unmatched "Old Maid" card.
static func make_odd_card() -> Card:
	return Card.new(NONE, NONE, true)


func label() -> String:
	if is_odd_one:
		return "OM"
	return RANK_LABELS[rank]


func symbol() -> String:
	if is_odd_one:
		return ODD_SYMBOL
	return SUIT_SYMBOLS[suit]


func is_red() -> bool:
	return not is_odd_one and suit in RED_SUITS


## True if both cards share a rank. The odd card never matches anything.
func matches_rank(other: Card) -> bool:
	if is_odd_one or other.is_odd_one:
		return false
	return rank == other.rank


## Value equality (unlike ==, which is reference identity for objects).
func equals(other: Card) -> bool:
	if other == null:
		return false
	return suit == other.suit and rank == other.rank and is_odd_one == other.is_odd_one


func _to_string() -> String:
	return "%s%s" % [label(), symbol()]
