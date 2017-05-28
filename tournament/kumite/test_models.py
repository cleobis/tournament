from django.test import TestCase

from .models import KumiteElim1Bracket, KumiteMatchPerson, KumiteMatch

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
    b = KumiteElim1Bracket()
    b.name = "asdf"
    b.save()
    
    for p in match_person_gen(n):
        b.people.add(p)
    
    b.build()
    
    # for round in range(2,-1,-1):
    #     print("round = {}".format(round))
    #     for m in b.kumitematch_set.filter(round=round):
    #         aka = m.aka.name if m.aka is not None else "?"
    #         shiro = m.shiro.name if m.shiro is not None else "?"
    #         print("{} - {} vs {}".format(m, aka, shiro))

    return b


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
        
        aka = KumiteMatchPerson()
        aka.name = "aka"
        aka.save()
        
        shiro = KumiteMatchPerson()
        shiro.name = "shiro"
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
        b = KumiteElim1Bracket()
        b.save()
        
        final = KumiteMatch()
        final.bracket = b
        final.name = "final"
        final.round = 0
        final.order = 1
        final.save()
        
        consolation = KumiteMatch()
        consolation.bracket = b
        consolation.name = "consolation"
        consolation.round = 0
        consolation.order = 0
        consolation.save()
        
        people = match_person_gen()
        
        m1 = KumiteMatch()
        m1.bracket = b
        m1.name = "KumiteMatch 1"
        m1.round = 1
        m1.order = 0
        m1.winner_match = final
        m1.consolation_match = consolation
        m1.aka = people.__next__()
        m1.shiro = people.__next__()
        m1.save()
        
        m2 = KumiteMatch()
        m2.bracket = b
        m2.name = "KumiteMatch 2"
        m2.round = 1
        m2.order = 1
        m2.winner_match = final
        m2.consolation_match = consolation
        m2.aka = people.__next__()
        m2.shiro = people.__next__()
        m2.save()
        
        self.assertIsNone(final.aka)
        self.assertIsNone(final.shiro)
        self.assertIsNone(consolation.aka)
        self.assertIsNone(consolation.shiro)
        
        m2.aka_won = True
        m2.done = True
        m2.save()
        
        self.assertIsNone(final.aka)
        self.assertEqual(final.shiro.name, "c")
        self.assertIsNone(consolation.aka)
        self.assertEqual(consolation.shiro.name, "d")
        
        m1.aka_won = False
        m1.done = True
        m1.save()
        
        self.assertEqual(final.aka.name, "b")
        self.assertEqual(final.shiro.name, "c")
        self.assertEqual(consolation.aka.name, "a")
        self.assertEqual(consolation.shiro.name, "d")

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
        
        with self.assertRaises(ValueError):
            make_bracket(3)
        
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