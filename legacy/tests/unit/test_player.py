from core.card import Card, Rank, Suit
from core.player import Hand, Player


def make_hand(*pairs):
    h = Hand()
    for suit, rank in pairs:
        h.add(Card(suit=suit, rank=rank))
    return h


def test_hand_add_and_len():
    h = Hand()
    assert h.is_empty()
    h.add(Card(suit=Suit.CLUBS, rank=Rank.ACE))
    assert len(h) == 1
    assert not h.is_empty()


def test_hand_remove_all_of_rank():
    h = make_hand(
        (Suit.CLUBS, Rank.SEVEN),
        (Suit.HEARTS, Rank.SEVEN),
        (Suit.SPADES, Rank.SEVEN),
        (Suit.DIAMONDS, Rank.SEVEN),
        (Suit.CLUBS, Rank.TWO),
    )
    matched = h.remove_all_of_rank(Rank.SEVEN)
    assert len(matched) == 4
    assert len(h) == 1
    assert h.cards[0].rank == Rank.TWO


def test_hand_remove_single_card():
    h = make_hand((Suit.CLUBS, Rank.FIVE), (Suit.HEARTS, Rank.FIVE))
    target = h.cards[0]
    h.remove(target)
    assert len(h) == 1
    assert target not in h.cards


def test_hand_count_and_has_rank():
    h = make_hand((Suit.CLUBS, Rank.KING), (Suit.HEARTS, Rank.KING))
    assert h.count_of_rank(Rank.KING) == 2
    assert h.has_rank(Rank.KING)
    assert not h.has_rank(Rank.ACE)


def test_hand_ranks_present_ignores_odd_card():
    from core.card import make_odd_card

    h = make_hand((Suit.CLUBS, Rank.KING))
    h.add(make_odd_card())
    assert h.ranks_present() == {Rank.KING}


def test_player_defaults():
    p = Player(name="Ellie")
    assert p.is_ai is False
    assert p.hand.is_empty()
    assert p.books == []
    assert p.score == 0


def test_player_hands_are_independent_instances():
    a = Player(name="A")
    b = Player(name="B")
    a.hand.add(Card(suit=Suit.CLUBS, rank=Rank.ACE))
    assert b.hand.is_empty()
