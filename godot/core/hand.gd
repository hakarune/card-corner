class_name Hand
extends RefCounted
## A player's hand of cards. Ported from legacy/core/player.py (Hand).
##
## erase()/remove() use reference identity -- pass the exact Card instance
## held by this hand, not a reconstructed equal.

var cards: Array[Card] = []


func add(card: Card) -> void:
	cards.append(card)


func add_many(new_cards: Array) -> void:
	cards.append_array(new_cards)


## Removes the given instance (reference identity). Legacy list.remove()
## raised on an absent card; here that's a debug-only assert, then a no-op.
func remove(card: Card) -> void:
	assert(card in cards, "Hand.remove(): card not in hand (wrong instance?)")
	cards.erase(card)


## Remove and return every card of `rank` in this hand.
func remove_all_of_rank(rank: int) -> Array[Card]:
	var matched: Array[Card] = []
	for c in cards:
		if not c.is_odd_one and c.rank == rank:
			matched.append(c)
	for c in matched:
		cards.erase(c)
	return matched


## Distinct ranks held (odd card excluded), sorted ascending by rank value.
## Legacy returned an unordered set[Rank]; every caller that needs cross-run
## determinism (go_fish_ai.decide_ask, old_maid._discard_pairs) sorted it by
## rank value, so this returns it pre-sorted to remove that footgun.
func ranks_present() -> Array[int]:
	var seen := {}
	for c in cards:
		if not c.is_odd_one:
			seen[c.rank] = true
	var out: Array[int] = []
	out.assign(seen.keys())
	out.sort()
	return out


func count_of_rank(rank: int) -> int:
	var n := 0
	for c in cards:
		if not c.is_odd_one and c.rank == rank:
			n += 1
	return n


func has_rank(rank: int) -> bool:
	return count_of_rank(rank) > 0


func is_empty() -> bool:
	return cards.is_empty()


func size() -> int:
	return cards.size()
