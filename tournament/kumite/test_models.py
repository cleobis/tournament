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


class KumiteMatchPersonTestCase(TestCase):
    
    def setUp(self):
        pass
    
    
    def test_matchperson(self):
        
        b = make_bracket(4)
        
        p = KumiteMatchPerson.objects.get(name="a")
        self.assertEqual(p.kumitematch, b.get_match(1,0))
        p = KumiteMatchPerson.objects.get(name="b")
        self.assertEqual(p.kumitematch, b.get_match(1,1))
        p = KumiteMatchPerson.objects.get(name="c")
        self.assertEqual(p.kumitematch, b.get_match(1,1))
        p = KumiteMatchPerson.objects.get(name="d")
        self.assertEqual(p.kumitematch, b.get_match(1,0))
        
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
        m2.aka_won = True
        m2.done = True
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
        
        # Set first winner
        # a --\__d__
        # d --/     \__
        # b --\__b__/
        # c --/
        #      __a__
        #           \_
        #      __c__/
        m1.aka_won = False
        m1.done = True
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

        # Undo first winner
        # a --\_____
        # d --/     \__
        # b --\__b__/
        # c --/
        #      _____
        #           \_
        #      __c__/
        m1.aka_won = True
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
        
        # Redo first winner
        # a --\__a__
        # d --/     \__
        # b --\__b__/
        # c --/
        #      __d__
        #           \_
        #      __c__/
        m1.aka_won = True
        m1.done = True
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
        
        # Set consolation first winner
        # a --\__a__
        # d --/     \__
        # b --\__b__/
        # c --/
        #      __d__
        #           \__d__
        #      __c__/
        consolation.aka_won = True
        consolation.done = True
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
        
        # Try editing locked match
        m1.aka_won = False
        self.assertRaises(ValueError, m1.save)

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
