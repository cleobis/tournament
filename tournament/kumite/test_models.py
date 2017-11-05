from django.test import TestCase

from registration.models import Event, EventLink
from .models import KumiteElim1Bracket, KumiteRoundRobinBracket, Kumite2PeopleBracket, KumiteMatchPerson, KumiteMatch

import math

def match_person_gen(n=None):
    """
    Iterator that will return a new KumiteMatchPerson each time called
    
    Args:
        n (optional): Number of people to return.
    
    Yields:
        KumiteMatchPerson: People named "a", "b", etc..
    """
    i = 0
    while n is None or i < n:
        p = KumiteMatchPerson()
        p.name = chr(ord("a") + i)
        i += 1
        p.save()
        yield p


def make_bracket(n):
    
    e = Event(name="test event", format=Event.EventFormat.elim1)
    e.save()
    
    b = e.get_format_class(n)()
    b.name = "asdf"
    b.save()
    
    people = [EventLink(manual_name=chr(ord("a")+i), event=e) for i in range(n)]
    for p in people:
        p.save()
    
    b.build(people)
    
    # for round in range(2,-1,-1):
    #     print("round = {}".format(round))
    #     for m in b.kumitematch_set.filter(round=round):
    #         aka = m.aka.name if m.aka is not None else "?"
    #         shiro = m.shiro.name if m.shiro is not None else "?"
    #         print("{} - {} vs {}".format(m, aka, shiro))

    return b


class KumiteMatchPersonTestCase(TestCase):
    
    def setUp(self):
        pass
    
    
    def test_matchperson(self):
        
        b = make_bracket(4)
        
        p = KumiteMatchPerson.objects.get(eventlink__manual_name="a")
        self.assertEqual(p.kumitematch, b.get_match(1,0))
        p = KumiteMatchPerson.objects.get(eventlink__manual_name="b")
        self.assertEqual(p.kumitematch, b.get_match(1,1))
        p = KumiteMatchPerson.objects.get(eventlink__manual_name="c")
        self.assertEqual(p.kumitematch, b.get_match(1,1))
        p = KumiteMatchPerson.objects.get(eventlink__manual_name="d")
        self.assertEqual(p.kumitematch, b.get_match(1,0))
        
        self.assertEqual(p.name, "d")
        
        b.delete()


class KumiteMatchTestCase(TestCase):
    
    def setUp(self):
        pass
    
    
    def test_cleanup(self):
        """Test linked KumiteMatchPersons are deleted automatically.
        """
        self.assertEquals(len(KumiteMatchPerson.objects.all()), 0)
        
        b = make_bracket(5)
        b.save()
        self.assertEquals(len(KumiteMatchPerson.objects.all()), 5)
        
        b.delete()
        self.assertEquals(len(KumiteMatchPerson.objects.all()), 0)
        
    
    def test_winner_loser(self):
        
        e = Event(name="test event", format=Event.EventFormat.elim1)
        e.save()
        
        el = EventLink(manual_name="aka", event=e)
        el.save()
        aka = KumiteMatchPerson(eventlink=el)
        aka.save()
        
        el = EventLink(manual_name="shiro", event=e)
        el.save()
        shiro = KumiteMatchPerson(eventlink=el)
        shiro.save()
        
        m = KumiteMatch() ;
        m.aka = aka
        m.shiro = shiro
        
        self.assertIsNone(m.winner())
        self.assertIsNone(m.loser())
        
        m.done = True
        m.aka_won = True
        self.assertEqual(m.winner(), aka)
        self.assertEqual(m.loser(), shiro)
        
        shiro.disqualified = True
        self.assertEqual(m.winner(), aka)
        self.assertIsNone(m.loser())
        shiro.disqualified = False
        
        m.aka_won = False
        self.assertEqual(m.winner(), shiro)
        self.assertEqual(m.loser(), aka)
        
        aka.disqualified = True
        self.assertEqual(m.winner(), shiro)
        self.assertIsNone(m.loser())
    
    
    def test_claim(self):
        
        b = make_bracket(4)
        final = b.final_match
        consolation = b.consolation_match
        m1 = b.get_match(1,0)
        m2 = b.get_match(1,1)
        
        # Test initial state
        # a --\_____
        # d --/     \__
        # b --\_____/
        # c --/
        #      _____
        #           \_
        #      _____/
        self.assertTrue(m1.is_editable())
        self.assertTrue(m1.is_ready())
        
        self.assertTrue(m2.is_editable())
        self.assertTrue(m2.is_ready())
        
        self.assertFalse(final.is_editable())
        self.assertFalse(final.is_ready())
        self.assertIsNone(final.aka)
        self.assertIsNone(final.shiro)
        
        self.assertFalse(consolation.is_editable())
        self.assertFalse(consolation.is_ready())
        self.assertIsNone(consolation.aka)
        self.assertIsNone(consolation.shiro)
        
        self.assertEqual(m1, b.get_next_match())
        self.assertEqual(m2, b.get_on_deck_match())
        
        self.assertEqual(b.get_winners(), ((1, None), (2, None), (3, None)))
        
        # Test editing a non-editable match
        final.done = True
        self.assertRaises(ValueError, final.save)
        final = b.final_match
        self.assertFalse(final.done)
        
        # Set second match winner
        # a --\_____
        # d --/     \__
        # b --\__b__/
        # c --/
        #      _____
        #           \_
        #      __c__/
        m2.aka.points = 1
        m2.aka.save()
        m2.done = True
        m2.infer_winner()
        m2.save()
        
        final = b.final_match
        consolation = b.consolation_match
        m1 = b.get_match(1,0)
        m2 = b.get_match(1,1)
        
        self.assertTrue(m1.is_editable())
        self.assertTrue(m1.is_ready())
        
        self.assertTrue(m2.is_editable())
        self.assertFalse(m2.is_ready())
        
        self.assertFalse(final.is_editable())
        self.assertFalse(final.is_ready())
        self.assertIsNone(final.aka)
        self.assertEqual(final.shiro.name, "b")
        
        self.assertFalse(consolation.is_editable())
        self.assertFalse(consolation.is_ready())
        self.assertIsNone(consolation.aka)
        self.assertEqual(consolation.shiro.name, "c")
        
        self.assertEqual(m1, b.get_next_match())
        self.assertEqual(consolation, b.get_on_deck_match())
        
        self.assertEqual(b.get_winners(), ((1, None), (2, None), (3, None)))
        
        # Set first winner
        # a --\__d__
        # d --/     \__
        # b --\__b__/
        # c --/
        #      __a__
        #           \_
        #      __c__/
        m1.shiro.points = 1 ;
        m1.done = True
        m1.infer_winner()
        m1.shiro.save()
        m1.save()
        
        final = b.final_match
        consolation = b.consolation_match
        m1 = b.get_match(1,0)
        m2 = b.get_match(1,1)
        
        self.assertTrue(m1.is_editable())
        self.assertFalse(m1.is_ready())
        
        self.assertTrue(m2.is_editable())
        self.assertFalse(m2.is_ready())
        
        self.assertTrue(final.is_editable())
        self.assertTrue(final.is_ready())
        self.assertEqual(final.aka.name, "d")
        self.assertEqual(final.shiro.name, "b")
        
        self.assertTrue(consolation.is_editable())
        self.assertTrue(consolation.is_ready())
        self.assertEqual(consolation.aka.name, "a")
        self.assertEqual(consolation.shiro.name, "c")
        
        self.assertEqual(b.get_winners(), ((1, None), (2, None), (3, None)))
        
        # Undo first winner
        # a --\_____
        # d --/     \__
        # b --\__b__/
        # c --/
        #      _____
        #           \_
        #      __c__/
        m1.done = False
        m1.save()
        
        final = b.final_match
        consolation = b.consolation_match
        m1 = b.get_match(1,0)
        m2 = b.get_match(1,1)
        
        self.assertTrue(m1.is_editable())
        self.assertTrue(m1.is_ready())
        
        self.assertTrue(m2.is_editable())
        self.assertFalse(m2.is_ready())
        
        self.assertFalse(final.is_editable())
        self.assertFalse(final.is_ready())
        self.assertIsNone(final.aka)
        self.assertEqual(final.shiro.name, "b")
        
        self.assertFalse(consolation.is_editable())
        self.assertFalse(consolation.is_ready())
        self.assertIsNone(consolation.aka)
        self.assertEqual(consolation.shiro.name, "c")
        
        self.assertEqual(b.get_winners(), ((1, None), (2, None), (3, None)))
        
        # Redo first winner
        # a --\__a__
        # d --/     \__
        # b --\__b__/
        # c --/
        #      __d__
        #           \_
        #      __c__/
        m1.aka.points = 4
        m1.done = True
        m1.infer_winner()
        m1.aka.save()
        m1.save()
        
        final = b.final_match
        consolation = b.consolation_match
        m1 = b.get_match(1,0)
        m2 = b.get_match(1,1)
        
        self.assertTrue(m1.is_editable())
        self.assertFalse(m1.is_ready())
        
        self.assertTrue(m2.is_editable())
        self.assertFalse(m2.is_ready())
        
        self.assertTrue(final.is_editable())
        self.assertTrue(final.is_ready())
        self.assertEqual(final.aka.name, "a")
        self.assertEqual(final.shiro.name, "b")
        
        self.assertTrue(consolation.is_editable())
        self.assertTrue(consolation.is_ready())
        self.assertEqual(consolation.aka.name, "d")
        self.assertEqual(consolation.shiro.name, "c")
        
        self.assertEqual(b.get_winners(), ((1, None), (2, None), (3, None)))
        
        # Set consolation first winner
        # a --\__a__
        # d --/     \__
        # b --\__b__/
        # c --/
        #      __d__
        #           \__d__
        #      __c__/
        consolation.aka.points = 1
        consolation.done = True
        consolation.infer_winner()
        consolation.aka.save()
        consolation.save()
        
        final = b.final_match
        consolation = b.consolation_match
        m1 = b.get_match(1,0)
        m2 = b.get_match(1,1)
        
        self.assertFalse(m1.is_editable())
        self.assertFalse(m1.is_ready())
        
        self.assertFalse(m2.is_editable())
        self.assertFalse(m2.is_ready())
        
        self.assertTrue(final.is_editable())
        self.assertTrue(final.is_ready())
        self.assertEqual(final.aka.name, "a")
        self.assertEqual(final.shiro.name, "b")
        
        self.assertTrue(consolation.is_editable())
        self.assertFalse(consolation.is_ready())
        self.assertEqual(consolation.aka.name, "d")
        self.assertEqual(consolation.shiro.name, "c")
        
        self.assertEqual(b.get_winners(), ((1, None), (2, None), (3, EventLink.objects.get(manual_name="d", division=b.division))))
        
        # Try editing locked match
        m1.aka_won = False
        self.assertRaises(ValueError, m1.save)
        
        # Set final winner
        # a --\__a__
        # d --/     \__a__
        # b --\__b__/
        # c --/
        #      __d__
        #           \__d__
        #      __c__/
        final.aka.points = 1
        final.done = True
        final.infer_winner()
        final.aka.save()
        final.save()
        
        final = b.final_match
        consolation = b.consolation_match
        m1 = b.get_match(1,0)
        m2 = b.get_match(1,1)
        
        self.assertFalse(m1.is_editable())
        self.assertFalse(m1.is_ready())
        
        self.assertFalse(m2.is_editable())
        self.assertFalse(m2.is_ready())
        
        self.assertTrue(final.is_editable())
        self.assertFalse(final.is_ready())
        self.assertEqual(final.aka.name, "a")
        self.assertEqual(final.shiro.name, "b")
        
        self.assertTrue(consolation.is_editable())
        self.assertFalse(consolation.is_ready())
        self.assertEqual(consolation.aka.name, "d")
        self.assertEqual(consolation.shiro.name, "c")
        
        self.assertEqual(b.get_winners(), (
            (1, EventLink.objects.get(manual_name="a", division=b.division)),
            (2, EventLink.objects.get(manual_name="b", division=b.division)),
            (3, EventLink.objects.get(manual_name="d", division=b.division))))
    
    
class KumiteElim1BracketTestCase(TestCase):
    
    def setUp(self):
        pass
    
    
    def test_get_seed_order(self):
        b = KumiteElim1Bracket()
        
        order = b.get_seed_order(1)
        self.assertEqual(order, [0, 1])
        
        order = b.get_seed_order(2)
        self.assertEqual(order, [0, 3, 1, 2])
        
        order = b.get_seed_order(3)
        self.assertEqual(order, [0, 7, 3, 4, 1, 6, 2, 5])
        
        with self.assertRaises(TypeError):
            b.get_seed_order("asdf")
        
        with self.assertRaises(ValueError):
            b.get_seed_order(0)
        
        with self.assertRaises(ValueError):
            b.get_seed_order(1.1)
    
    
    def test_build(self):
        """Try building brackets of different sizes and make sure people are assigned correctly."""
        
        def round_matches_list(round):
            matches = b.kumitematch_set.filter(round=round)
            return [(m.order,
                m.aka.name if m.aka is not None else None,
                m.shiro.name if m.shiro is not None else None
                ) for m in matches] 
        
        b = make_bracket(4)
        self.assertEqual(b.rounds, 2)
        self.assertEqual(round_matches_list(1), [
            (0, "a", "d"), (1, "b", "c")])
        self.assertIsNotNone(b.final_match)
        self.assertIsNotNone(b.consolation_match)
        
        b = make_bracket(5)
        self.assertEqual(b.rounds, 3)
        self.assertEqual(round_matches_list(2), [
            (1, "d", "e")])
        self.assertEqual(round_matches_list(1), [
            (0, "a", None), (1, "b", "c")])
        self.assertIsNotNone(b.final_match)
        self.assertIsNotNone(b.consolation_match)
        
        b = make_bracket(6)
        self.assertEqual(b.rounds, 3)
        self.assertEqual(round_matches_list(2), [
            (1, "d", "e"), (3, "c", "f")])
        self.assertEqual(round_matches_list(1), [
            (0, "a", None), (1, "b", None)])
        self.assertIsNotNone(b.final_match)
        self.assertIsNotNone(b.consolation_match)
        
        b = make_bracket(7)
        self.assertEqual(b.rounds, 3)
        self.assertEqual(round_matches_list(2), [
            (1, "d", "e"), (2, "b", "g"), (3, "c", "f")])
        self.assertEqual(round_matches_list(1), [
            (0, "a", None), (1, None, None)])
        self.assertIsNotNone(b.final_match)
        self.assertIsNotNone(b.consolation_match)

        b = make_bracket(8)
        self.assertEqual(b.rounds, 3)
        self.assertEqual(round_matches_list(2), [
            (0, "a", "h"), (1, "d", "e"), (2, "b", "g"), (3, "c", "f")])
        self.assertEqual(round_matches_list(1), [
            (0, None, None), (1, None, None)])
        self.assertIsNotNone(b.final_match)
        self.assertIsNotNone(b.consolation_match)
        
        b = make_bracket(9)
        self.assertEqual(b.rounds, 4)
        self.assertEqual(round_matches_list(3), [
            (1, "h", "i"),])
        self.assertEqual(round_matches_list(2), [
            (0, "a", None), (1, "d", "e"), (2, "b", "g"), (3, "c", "f")])
        self.assertEqual(round_matches_list(1), [
            (0, None, None), (1, None, None)])
        self.assertIsNotNone(b.final_match)
        self.assertIsNotNone(b.consolation_match)
        
        for m in b.kumitematch_set.all():
            if m == b.final_match:
                self.assertTrue(m.is_final())
                self.assertFalse(m.is_consolation())
            elif m == b.consolation_match:
                self.assertFalse(m.is_final())
                self.assertTrue(m.is_consolation())
            else:
                self.assertFalse(m.is_final())
                self.assertFalse(m.is_consolation())
    
    
    def test_get_match(self):
        
        b = make_bracket(5)
        
        round = 2
        valid_matches = [1]
        for i in range(b.get_num_match_in_round(round)):
            m = b.get_match(round, i)
            msg = " with round {}, match {}".format(round, i)
            if i in valid_matches:
                self.assertEqual(m.round, round, msg="round error" + msg)
                self.assertEqual(m.order, i, msg = "order error" + msg)
            else:
                self.assertIsNone(m, msg="None error" + msg)
        with self.assertRaises(ValueError):
            b.get_match(round, -1)
        with self.assertRaises(ValueError):
            b.get_match(round, 4)
        
        round = 1
        valid_matches = [0, 1]
        for i in range(b.get_num_match_in_round(round)):
            m = b.get_match(round, i)
            msg = " with round {}, match {}".format(round, i)
            if i in valid_matches:
                self.assertEqual(m.round, round, msg="round error" + msg)
                self.assertEqual(m.order, i, msg = "order error" + msg)
            else:
                self.assertIsNone(m, msg="None error" + msg)
        with self.assertRaises(ValueError):
            b.get_match(round, -1)
        with self.assertRaises(ValueError):
            b.get_match(round, 2)
        
        round = 0
        valid_matches = [-1, 0]
        m = b.get_match(0,0)
        self.assertEqual(m, b.final_match)
        m = b.get_match(0, -1)
        self.assertEqual(m, b.consolation_match)
        with self.assertRaises(ValueError):
            b.get_match(round, -2)
        with self.assertRaises(ValueError):
            b.get_match(round, 1)
    
    
    def test_swap(self):
        
        #       a ---\___
        #  d --\_____/    \____
        #  e --/          /
        #       b ---\___/
        #       c ---/
        
        b = make_bracket(5)
        
        get_matches = lambda: [(
                m.aka.name if m.aka is not None else "",
                m.aka.is_swappable() if m.aka is not None else False,
                m.shiro.name if m.shiro is not None else "",
                m.shiro.is_swappable() if m.shiro is not None else False
            ) for m in b.kumitematch_set.all()]
        get_people = lambda: [p.name for p in b.get_swappable_match_people()] 
        
        self.assertEqual(get_people(), ["a", "d", "e", "b", "c"])
        self.assertEqual(get_matches(), [('d', True, 'e', True), ('a', True, '', False), 
            ('b', True, 'c', True), ('', False, '', False), ('', False, '', False)])
        
        #       a ---\___
        #  d --\_____/    \___
        #  e --/          /
        #       b ---\_b_/
        #       c ---/
        #             -c-\___
        #             ---/
        m = b.get_match(1, 1)
        m.done = True
        m.aka_won = True
        m.save()
        self.assertEqual(get_people(), ["a", "d", "e"])
        self.assertEqual(get_matches(), [('d', True, 'e', True), ('a', True, '', False), 
            ('b', False, 'c', False), ('', False, 'c', False), ('', False, 'b', False)])
        
        #       a ---\___
        #  d --\___e_/    \___
        #  e --/          /
        #       b ---\_b_/
        #       c ---/
        #             ---\___
        #             -c-/
        m = b.get_match(2, 1)
        m.done = True
        m.aka_won = False
        m.save()
        self.assertEqual(get_people(), ["a"])
        self.assertEqual(get_matches(), [('d', False, 'e', False), ('a', True, 'e', False), 
            ('b', False, 'c', False), ('', False, 'c', False), ('', False, 'b', False)])
        
        #       a ---\_a_
        #  d --\___e_/    \___
        #  e --/          /
        #       b ---\_b_/
        #       c ---/
        #             -e-\___
        #             -c-/
        m = b.get_match(1, 0)
        m.done = True
        m.aka_won = True
        m.save()
        self.assertEqual(get_people(), [])
        self.assertEqual(get_matches(), [('d', False, 'e', False), ('a', False, 'e', False), 
            ('b', False, 'c', False), ('e', False, 'c', False), ('a', False, 'b', False)])

class KumiteRoundRobinBracketTestCase(TestCase):
    
    def test_run(self):
        
        b = make_bracket(3)
        self.assertIsInstance(b, KumiteRoundRobinBracket)
        
        # # Test initial state
        # a:? - b:?
        # b:? - c:?
        # c:? - a:?
        self.assertEqual(len(b.kumitematch_set.all()), 3)
        m1 = b.get_match(0, 0)
        m2 = b.get_match(0, 1)
        m3 = b.get_match(0, 2)
        
        self.assertTrue(m1.is_editable())
        self.assertTrue(m1.is_ready())
        self.assertEqual(m1.aka.name, "a")
        self.assertEqual(m1.shiro.name, "b")
        
        self.assertTrue(m2.is_editable())
        self.assertTrue(m2.is_ready())
        self.assertEqual(m2.aka.name, "b")
        self.assertEqual(m2.shiro.name, "c")
        
        self.assertTrue(m3.is_editable())
        self.assertTrue(m3.is_ready())
        self.assertEqual(m3.aka.name, "c")
        self.assertEqual(m3.shiro.name, "a")
        
        self.assertEqual(m1, b.get_next_match())
        
        self.assertEqual(b.get_winners(), ((1, None), (2, None), (3, None)))
        
        # Finish one matches
        # a:1 - b:0
        # b:? - c:?
        # c:? - a:?
        m1.aka.points = 1
        m1.aka.save()
        m1.shiro.points = 0
        m1.shiro.save()
        m1.done = True
        m1.infer_winner()
        m1.save()
        
        self.assertEqual(len(b.kumitematch_set.all()), 3)
        m1 = b.get_match(0, 0)
        m2 = b.get_match(0, 1)
        m3 = b.get_match(0, 2)
        
        self.assertTrue(m1.is_editable())
        self.assertFalse(m1.is_ready())
        self.assertEqual(m1.aka.name, "a")
        self.assertEqual(m1.shiro.name, "b")
        self.assertTrue(m1.aka_won)
        
        self.assertTrue(m2.is_editable())
        self.assertTrue(m2.is_ready())
        self.assertEqual(m2.aka.name, "b")
        self.assertEqual(m2.shiro.name, "c")
        
        self.assertTrue(m3.is_editable())
        self.assertTrue(m3.is_ready())
        self.assertEqual(m3.aka.name, "c")
        self.assertEqual(m3.shiro.name, "a")
        
        self.assertEqual(m2, b.get_next_match())
        
        self.assertEqual(b.get_winners(), ((1, None), (2, None), (3, None)))
        
        # Finish two matches
        # a:1 - b:0
        # b:? - c:?
        # c:9 - a:0
        m3.aka.points = 9
        m3.aka.save()
        m3.shiro.points = 0
        m3.shiro.save()
        m3.done = True
        m3.infer_winner()
        m3.save()
        
        self.assertEqual(len(b.kumitematch_set.all()), 3)
        m1 = b.get_match(0, 0)
        m2 = b.get_match(0, 1)
        m3 = b.get_match(0, 2)
        
        self.assertTrue(m1.is_editable())
        self.assertFalse(m1.is_ready())
        self.assertEqual(m1.aka.name, "a")
        self.assertEqual(m1.shiro.name, "b")
        
        self.assertTrue(m2.is_editable())
        self.assertTrue(m2.is_ready())
        self.assertEqual(m2.aka.name, "b")
        self.assertEqual(m2.shiro.name, "c")
        
        self.assertTrue(m3.is_editable())
        self.assertFalse(m3.is_ready())
        self.assertEqual(m3.aka.name, "c")
        self.assertEqual(m3.shiro.name, "a")
        
        self.assertEqual(m2, b.get_next_match())
        
        self.assertEqual(b.get_winners(), ((1, None), (2, None), (3, None)))
        
        # Finish all matches, winner tie break based on point differential
        # a:1 - b:0
        # b:3 - c:0
        # c:9 - a:0
        m2.aka.points = 3
        m2.aka.save()
        m2.shiro.points = 0
        m2.shiro.save()
        m2.done = True
        m2.infer_winner()
        m2.save()
        
        self.assertEqual(len(b.kumitematch_set.all()), 3)
        m1 = b.get_match(0, 0)
        m2 = b.get_match(0, 1)
        m3 = b.get_match(0, 2)
        
        self.assertTrue(m1.is_editable())
        self.assertFalse(m1.is_ready())
        self.assertEqual(m1.aka.name, "a")
        self.assertEqual(m1.shiro.name, "b")
        
        self.assertTrue(m2.is_editable())
        self.assertFalse(m2.is_ready())
        self.assertEqual(m2.aka.name, "b")
        self.assertEqual(m2.shiro.name, "c")
        
        self.assertTrue(m3.is_editable())
        self.assertFalse(m3.is_ready())
        self.assertEqual(m3.aka.name, "c")
        self.assertEqual(m3.shiro.name, "a")
        
        self.assertEqual(b.get_next_match(), None)
        
        self.assertEqual(b.get_winners(), ((1, m3.aka.eventlink), (2, m2.aka.eventlink), (3, m1.aka.eventlink)))
        
        # Winner by total wins, ignoring points
        # a:1 - b:0
        # b:9 - c:0
        # c:0 - a:1
        m2.aka.points = 9
        m2.aka.save()
        m2.shiro.points = 8
        m2.shiro.save()
        m2.done = True
        m2.infer_winner()
        m2.save()
        
        m3.aka.points = 0
        m3.aka.save()
        m3.shiro.points = 1
        m3.shiro.save()
        m3.done = True
        m3.infer_winner()
        m3.save()
        
        self.assertEqual(len(b.kumitematch_set.all()), 3)
        m1 = b.get_match(0, 0)
        m2 = b.get_match(0, 1)
        m3 = b.get_match(0, 2)
        
        self.assertTrue(m1.is_editable())
        self.assertFalse(m1.is_ready())
        self.assertEqual(m1.aka.name, "a")
        self.assertEqual(m1.shiro.name, "b")
        
        self.assertTrue(m2.is_editable())
        self.assertFalse(m2.is_ready())
        self.assertEqual(m2.aka.name, "b")
        self.assertEqual(m2.shiro.name, "c")
        
        self.assertTrue(m3.is_editable())
        self.assertFalse(m3.is_ready())
        self.assertEqual(m3.aka.name, "c")
        self.assertEqual(m3.shiro.name, "a")
        
        self.assertEqual(b.get_next_match(), None)
        
        self.assertEqual(b.get_winners(), ((1, m1.aka.eventlink), (2, m2.aka.eventlink), (3, m3.aka.eventlink)))
        
        #TODO: NEED TO DEAL WITH TIES!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!

class Kumite2PeopleBracketTestCase(TestCase):
    
    def test_run(self):
        
        b = make_bracket(2)
        self.assertIsInstance(b, Kumite2PeopleBracket)
        
        # Test initial state
        # a:? - b:?
        # b:? - a:?
        self.assertEqual(len(b.kumitematch_set.all()), 2)
        m1 = b.get_match(0, 0)
        m2 = b.get_match(0, 1)
        
        self.assertTrue(m1.is_editable())
        self.assertTrue(m1.is_ready())
        self.assertEqual(m1.aka.name, "a")
        self.assertEqual(m1.shiro.name, "b")
        
        self.assertFalse(m2.is_editable())
        self.assertFalse(m2.is_ready())
        self.assertEqual(m2.aka.name, "b")
        self.assertEqual(m2.shiro.name, "a")
        
        self.assertEqual(m1, b.get_next_match())
        
        self.assertEqual(b.get_winners(), ((1, None), (2, None)))
        
        # Finish one match
        # a:2 - b:1
        # b:? - a:?
        m1.aka.points = 2
        m1.aka.save()
        m1.shiro.points = 1
        m1.shiro.save()
        m1.done = True
        m1.save()
        
        self.assertEqual(len(b.kumitematch_set.all()), 2)
        m1 = b.get_match(0, 0)
        m2 = b.get_match(0, 1)
        
        self.assertTrue(m1.is_editable())
        self.assertFalse(m1.is_ready())
        
        self.assertTrue(m2.is_editable())
        self.assertTrue(m2.is_ready())
        
        self.assertEqual(m2, b.get_next_match())
        
        self.assertEqual(b.get_winners(), ((1, None), (2, None)))
        
        # Finish second match, tie
        # a:2 - b:1
        # b:3 - a:2
        # a:? - b:?
        m2.aka.points = 3
        m2.aka.save()
        m2.shiro.points = 2
        m2.shiro.save()
        m2.done = True
        m2.save()
        
        self.assertEqual(len(b.kumitematch_set.all()), 3)
        m1 = b.get_match(0, 0)
        m2 = b.get_match(0, 1)
        m3 = b.get_match(0, 2)
        
        self.assertFalse(m1.is_editable())
        self.assertFalse(m1.is_ready())
        
        self.assertTrue(m2.is_editable())
        self.assertFalse(m2.is_ready())
        
        self.assertTrue(m3.is_editable())
        self.assertTrue(m3.is_ready())
        self.assertEqual(m3.aka.name, "a")
        self.assertEqual(m3.shiro.name, "b")
        
        self.assertEqual(m3, b.get_next_match())
        
        self.assertEqual(b.get_winners(), ((1, None), (2, None)))
        
        # Tie winner
        # a:2 - b:1
        # b:3 - a:2
        # a:9 - b:0
        m3.aka.points = 9
        m3.aka.save()
        m3.shiro.points = 0
        m3.shiro.save()
        m3.done = True
        m3.save()
        
        self.assertEqual(len(b.kumitematch_set.all()), 3)
        m1 = b.get_match(0, 0)
        m2 = b.get_match(0, 1)
        m3 = b.get_match(0, 2)
        
        self.assertFalse(m1.is_editable())
        self.assertFalse(m1.is_ready())
        
        self.assertFalse(m2.is_editable())
        self.assertFalse(m2.is_ready())
        
        self.assertTrue(m3.is_editable())
        self.assertFalse(m3.is_ready())
        
        self.assertEqual(b.get_next_match(), None)
        
        self.assertEqual(b.get_winners(), ((1, m1.aka.eventlink), (2, m1.shiro.eventlink)))
        
        # Undo Tie
        # a:2 - b:1
        # b:5 - a:2
        m3.done = False
        m3.save()
        
        m2 = b.get_match(0, 1)
        m2.aka.points = 5
        m2.aka.save()
        m2.shiro.points = 2
        m2.shiro.save()
        m2.save()
        
        self.assertEqual(len(b.kumitematch_set.all()), 2)
        m1 = b.get_match(0, 0)
        m2 = b.get_match(0, 1)
        
        self.assertFalse(m1.is_editable())
        self.assertFalse(m1.is_ready())
        
        self.assertTrue(m2.is_editable())
        self.assertFalse(m2.is_ready())
        
        self.assertEqual(b.get_next_match(), None)
        
        self.assertEqual(b.get_winners(), ((1, m1.shiro.eventlink), (2, m1.aka.eventlink)))