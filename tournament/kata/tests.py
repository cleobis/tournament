from django.test import TestCase

from registration.models import Event, Division, EventLink
from .models import KataBracket

import math


import logging
log = logging.getLogger()

def make_bracket(n):
    
    e = Event(name="test event", format=Event.EventFormat.kata)
    e.save()
    
    b = e.get_format_class(n)()
    b.name = "asdf"
    b.save()
    
    
    people = [EventLink(manual_name=chr(ord("a")+i), event=e) for i in range(n)]
    for p in people:
        p.save()
    
    b.build(people)
    
    return b


def get_person(bracket, name):
    return bracket.get_people().get(manual_name=name)


# Create your tests here.
class TestKataBracket(TestCase):
    
    def test_two(self):
        
        b = make_bracket(2)
        self.assertIsInstance(b, KataBracket)
        
        # Initial state
        rounds = b.kataround_set.all()
        self.assertEqual(len(rounds), 1)
        self.assertEqual(b.n_round, 1)
        
        winners = b.get_winners()
        self.assertEqual(winners, [(1, None), (2, None)])
        
        # First Score
        # a - 5 6 7 8 9
        # b - ?
        m = b.get_next_match()
        m.scores = (5, 6, 7, 8, 9)
        m.save()
        
        winners = b.get_winners()
        self.assertEqual(winners, [(1, get_person(b, "a")), (2, None)])
        
        # Second Score
        # a - 5 6 7 8 9
        # b - 5 7 8 9 10 
        m = b.get_next_match()
        m.scores = (5, 7, 8, 9, 10)
        m.save()
        
        winners = b.get_winners()
        self.assertEqual(winners, [(1, get_person(b, "b")), (2, get_person(b, "a"))])
        
        
        # Change a so it wins by tie break
        # a - 6 7 8 9 10
        # b - 5 7 8 9 10 
        m = b.rounds[0].matches.get(eventlink__manual_name="a")
        m.scores = (6, 7, 8, 9, 10)
        m.save()
        
        winners = b.get_winners()
        self.assertEqual(winners, [(1, get_person(b, "a")), (2, get_person(b, "b"))])
        
        # Tie break
        # a - 6 7 8 9 10
        # b - 7 7 8 9 9
        # ---
        # a - ?
        # b - ?
        m = b.rounds[0].matches.get(eventlink__manual_name="b")
        m.scores = (7, 7, 8, 9, 9)
        m.save()
        
        self.assertEqual(b.n_round, 2)
        
        winners = b.get_winners()
        self.assertEqual(winners, [(1, get_person(b, "a")), (1, get_person(b, "b"))])
        
        # Second round
        # # a - 6 7 8 9 10
        # b - 7 7 8 9 9
        # ---
        # a - 8 9 9 9 9
        # b - ?
        
        m = b.get_next_match()
        self.assertEqual(m.round.round, 1)
        self.assertEqual(m.eventlink.manual_name, "a")
        
        m.scores = (8, 9, 9, 9, 9)
        m.save()
        
        winners = b.get_winners()
        self.assertEqual(winners, [(1, get_person(b, "a")), (2, get_person(b, "b"))])
        
        # Second round
        # # a - 6 7 8 9 10
        # b - 7 7 8 9 9
        # ---
        # a - 8 9 9 9 9
        # b - 9 9 9 9 9
        
        m = b.get_next_match()
        self.assertEqual(m.round.round, 1)
        self.assertEqual(m.eventlink.manual_name, "b")
        
        m.scores = (9, 9, 9, 9, 9)
        m.save()
        
        winners = b.get_winners()
        self.assertEqual(winners, [(1, get_person(b, "b")), (2, get_person(b, "a"))])
    
    
    def test_six(self):
        
        b = make_bracket(6)
        self.assertIsInstance(b, KataBracket)
        
        # Initial state
        rounds = b.kataround_set.all()
        self.assertEqual(len(rounds), 1)
        self.assertEqual(b.n_round, 1)
        
        winners = b.get_winners()
        self.assertEqual(winners, [(1, None), (2, None), (3, None)])
        
        # First round
        # a - 9 9 9 9 9 - 1
        # b - 8 8 8 8 8 - 3
        # c - 9 9 9 9 9 - 1
        # d - 8 8 8 8 8 - 3
        # e - 5 5 5 5 5 - 6
        # f - 8 8 8 8 8 - 3
        
        # a
        m = b.get_next_match()
        self.assertEqual(m.round.round, 0)
        self.assertEqual(m.eventlink.manual_name, "a")
        m.scores = (9, 9, 9, 9, 9)
        m.save()
        
        winners = b.get_winners()
        self.assertEqual(winners, [(1, get_person(b, "a")), (2, None), (3, None)])
        
        # b
        m = b.get_next_match()
        self.assertEqual(m.round.round, 0)
        self.assertEqual(m.eventlink.manual_name, "b")
        m.scores = (8, 8, 8, 8, 8)
        m.save()
        
        winners = b.get_winners()
        self.assertEqual(winners, [(1, get_person(b, "a")), (2, get_person(b, "b")), (3, None)])
        
        # c
        m = b.get_next_match()
        self.assertEqual(m.round.round, 0)
        self.assertEqual(m.eventlink.manual_name, "c")
        m.scores = (9, 9, 9, 9, 9)
        m.save()
        
        winners = b.get_winners()
        self.assertEqual(winners, [(1, get_person(b, "a")), (1, get_person(b, "c")), (3, get_person(b, "b"))])
        
        # d
        m = b.get_next_match()
        self.assertEqual(m.round.round, 0)
        self.assertEqual(m.eventlink.manual_name, "d")
        m.scores = (8, 8, 8, 8, 8)
        m.save()
        
        winners = b.get_winners()
        self.assertEqual(winners, [(1, get_person(b, "a")), (1, get_person(b, "c")), 
            (3, get_person(b, "b")), (3, get_person(b, "d"))])
        
        # e
        m = b.get_next_match()
        self.assertEqual(m.round.round, 0)
        self.assertEqual(m.eventlink.manual_name, "e")
        m.scores = (5, 5, 5, 5, 5)
        m.save()
        
        winners = b.get_winners()
        self.assertEqual(winners, [(1, get_person(b, "a")), (1, get_person(b, "c")), 
            (3, get_person(b, "b")), (3, get_person(b, "d"))])
        
        # f
        m = b.get_next_match()
        self.assertEqual(m.round.round, 0)
        self.assertEqual(m.eventlink.manual_name, "f")
        m.scores = (8, 8, 8, 8, 8)
        m.save()
        winners = b.get_winners()
        self.assertEqual(winners, [(1, get_person(b, "a")), (1, get_person(b, "c")), 
            (3, get_person(b, "b")), (3, get_person(b, "d")), (3, get_person(b, "f"))])
        
        # second round
        # a - 9 9 9 9 9 - 1
        # b - 8 8 8 8 8 - 3
        # c - 9 9 9 9 9 - 1
        # d - 8 8 8 8 8 - 3
        # e - 5 5 5 5 5 - 6
        # f - 8 8 8 8 8 - 3
        # ---
        # b - 9 9 9 9 9 - 3
        # d - 9 9 9 9 9 - 3
        # f - 5 5 5 5 5 - 5
        # ---
        # a - 1 1 0 1 1 - 2
        # c - 1 1 1 1 1 - 1
        
        # b
        m = b.get_next_match()
        self.assertEqual(m.round.round, 1)
        self.assertEqual(m.eventlink.manual_name, "b")
        m.scores = (9, 9, 9, 9, 9)
        m.save()
        
        winners = b.get_winners()
        self.assertEqual(winners, [(1, get_person(b, "a")), (1, get_person(b, "c")), (3, get_person(b, "b"))])
        
        # d
        m = b.get_next_match()
        self.assertEqual(m.round.round, 1)
        self.assertEqual(m.eventlink.manual_name, "d")
        m.scores = (9, 9, 9, 9, 9)
        m.save()
        
        winners = b.get_winners()
        self.assertEqual(winners, [(1, get_person(b, "a")), (1, get_person(b, "c"))
            , (3, get_person(b, "b")), (3, get_person(b, "d"))])
        
        # f
        m = b.get_next_match()
        self.assertEqual(m.round.round, 1)
        self.assertEqual(m.eventlink.manual_name, "f")
        m.scores = (5, 5, 5, 5, 5)
        m.save()
        
        winners = b.get_winners()
        self.assertEqual(winners, [(1, get_person(b, "a")), (1, get_person(b, "c")),
            (3, get_person(b, "b")), (3, get_person(b, "d"))])
        
        # a
        m = b.get_next_match()
        self.assertEqual(m.round.round, 1)
        self.assertEqual(m.round.order, 0)
        self.assertEqual(m.eventlink.manual_name, "a")
        m.scores = (1, 1, 0, 1, 1)
        m.save()
        
        winners = b.get_winners()
        self.assertEqual(winners, [(1, get_person(b, "a")), (2, get_person(b, "c")), 
            (3, get_person(b, "b")), (3, get_person(b, "d"))])
        
        # c
        m = b.get_next_match()
        self.assertEqual(m.round.round, 1)
        self.assertEqual(m.round.order, 0)
        self.assertEqual(m.eventlink.manual_name, "c")
        m.scores = (1, 1, 1, 1, 1)
        m.save()
        
        winners = b.get_winners()
        self.assertEqual(winners, [(1, get_person(b, "c")), (2, get_person(b, "a")), 
            (3, get_person(b, "b")), (3, get_person(b, "d"))])
        
        # third round
        # a - 9 9 9 9 9 - 1
        # b - 8 8 8 8 8 - 3
        # c - 9 9 9 9 9 - 1
        # d - 8 8 8 8 8 - 3
        # e - 5 5 5 5 5 - 6
        # f - 8 8 8 8 8 - 3
        # ====
        # b - 9 9 9 9 9 - 3
        # d - 9 9 9 9 9 - 3
        # f - 5 5 5 5 5 - 5
        # ---
        # a - 1 1 0 1 1 - 2
        # c - 1 1 1 1 1 - 1
        # ===
        # b - 1 2 3 4 5 - 4
        # d - 4 5 6 7 8 - 3
        
        # b
        m = b.get_next_match()
        self.assertEqual(m.round.round, 2)
        self.assertEqual(m.round.order, 0)
        self.assertEqual(m.eventlink.manual_name, "b")
        m.scores = (1, 2, 3, 4, 5)
        m.save()
        
        winners = b.get_winners()
        self.assertEqual(winners, [(1, get_person(b, "c")), (2, get_person(b, "a")), 
            (3, get_person(b, "b"))])
        
        # d
        m = b.get_next_match()
        self.assertEqual(m.round.round, 2)
        self.assertEqual(m.round.order, 0)
        self.assertEqual(m.eventlink.manual_name, "d")
        m.scores = (4, 5, 6, 7, 8)
        m.save()
        
        winners = b.get_winners()
        self.assertEqual(winners, [(1, get_person(b, "c")), (2, get_person(b, "a")), 
            (3, get_person(b, "d"))])
        
        self.assertEqual(b.get_next_match(), None)
        