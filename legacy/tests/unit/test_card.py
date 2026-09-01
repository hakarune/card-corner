import pytest

from core.card import Card, Rank, Suit, make_odd_card


def test_standard_card_str():
    c = Card(suit=Suit.HEARTS, rank=Rank.ACE)
    assert c.label == "A"
    assert c.symbol == "♥"
    assert str(c) == "A♥"


def test_odd_card_requires_no_suit_or_rank():
    with pytest.raises(ValueError):
        Card(suit=Suit.HEARTS, rank=None, is_odd_one=True)
    with pytest.raises(ValueError):
        Card(suit=None, rank=Rank.QUEEN, is_odd_one=True)


def test_non_odd_card_requires_suit_and_rank():
    with pytest.raises(ValueError):
        Card(suit=None, rank=Rank.ACE)
    with pytest.raises(ValueError):
        Card(suit=Suit.CLUBS, rank=None)


def test_make_odd_card():
    odd = make_odd_card()
    assert odd.is_odd_one
    assert odd.suit is None
    assert odd.rank is None
    assert odd.label == "OM"


def test_matches_rank():
    a = Card(suit=Suit.HEARTS, rank=Rank.SEVEN)
    b = Card(suit=Suit.SPADES, rank=Rank.SEVEN)
    c = Card(suit=Suit.SPADES, rank=Rank.EIGHT)
    assert a.matches_rank(b)
    assert not a.matches_rank(c)


def test_odd_card_never_matches():
    odd = make_odd_card()
    other = Card(suit=Suit.CLUBS, rank=Rank.QUEEN)
    assert not odd.matches_rank(other)
    assert not other.matches_rank(odd)
    assert not odd.matches_rank(odd)


def test_is_red():
    assert Card(suit=Suit.HEARTS, rank=Rank.TWO).is_red
    assert Card(suit=Suit.DIAMONDS, rank=Rank.TWO).is_red
    assert not Card(suit=Suit.CLUBS, rank=Rank.TWO).is_red
    assert not Card(suit=Suit.SPADES, rank=Rank.TWO).is_red
    assert not make_odd_card().is_red


def test_card_equality_and_hash():
    a = Card(suit=Suit.HEARTS, rank=Rank.SEVEN)
    b = Card(suit=Suit.HEARTS, rank=Rank.SEVEN)
    assert a == b
    assert hash(a) == hash(b)
    assert len({a, b}) == 1
