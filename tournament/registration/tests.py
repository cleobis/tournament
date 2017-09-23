from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist
from .models import Person, Rank, EventLink, Division, Event

# Create your tests here.
class EventTestCase(TestCase):
    
    def test_get_format(self):
        from kumite.models import KumiteElim1Bracket
        e = Event(name="asfd", format=Event.EventFormat.elim1)
        self.assertEqual(e.get_format_class(10), KumiteElim1Bracket)



class RankTestCase(TestCase):
    
    def test_get_kyu(self):
        rank = Rank.get_kyu(8)
        self.assertTrue(rank.name.startswith("Yellow"))
        
        with self.assertRaises(ObjectDoesNotExist):
            rank = Rank.get_kyu(10)
    
    
    def test_get_dan(self):
        rank = Rank.get_dan(2)
        self.assertTrue(rank.name.startswith("Nidan"))
    
        with self.assertRaises(ObjectDoesNotExist):
            rank = Rank.get_dan(0)
    
    
    def test_build_default_fixture(self):
        """Check that default entries have been populated.
        
        The rank fixture should have been automatically loaded by DB migration.
        Check that it is populated and that it matches the generation function 
        and the saved fixture.
        """
        
        from django.core import serializers
        import os
        import io
        
        db = serializers.serialize("json", Rank.objects.all(), indent=4)
        
        filename = os.path.realpath(__file__)
        filename = os.path.join(os.path.dirname(filename), "fixtures", "rank.json")
        with open(filename) as f:
            filename = f.read()
        
        fun = io.StringIO()
        Rank.build_default_fixture(fun)
        fun.seek(0)
        fun = fun.read()
        
        self.assertJSONEqual(db, filename)
        self.assertJSONEqual(db, fun)


class DivisionTestCase(TestCase):
    
    def test_claim(self):
        e = Event(name="event")
        e.save()
        
        # Create some divisions
        white = Rank.get_kyu(8)
        brown = Rank.get_kyu(1)
        bb1 = Rank.get_dan(1)
        bb9 = Rank.get_dan(9)
        Division(event=e, gender='M', start_age=1,  stop_age = 18, start_rank=white, stop_rank=brown).save()
        Division(event=e, gender='M', start_age=19, stop_age = 99, start_rank=white, stop_rank=brown).save()
        Division(event=e, gender='F', start_age=1,  stop_age = 18, start_rank=white, stop_rank=brown).save()
        Division(event=e, gender='F', start_age=19, stop_age = 99, start_rank=white, stop_rank=brown).save()
        Division(event=e, gender='M', start_age=1,  stop_age = 18, start_rank=  bb1, stop_rank=  bb9).save()
        Division(event=e, gender='M', start_age=19, stop_age = 99, start_rank=  bb1, stop_rank=  bb9).save()
        Division(event=e, gender='F', start_age=1,  stop_age = 18, start_rank=  bb1, stop_rank=  bb9).save()
        # Create this later: Division(event=e, gender='F', start_age=19, stop_age = 99, start_rank=  bb1, stop_rank=  bb9).save()
        
        def div_summary():
            return ([[el.name for el in d.eventlink_set.all()] for d in Division.objects.filter(event=e)],
                [el.name for el in e.get_orphan_links()])
        
        self.assertEqual(div_summary(), ([[], [], [], [], [], [], []], []))
        
        # Create some people
        p = Person(first_name="a", last_name="a", gender='M', age=1, rank=Rank.get_kyu(8), instructor="asdf")
        p.save()
        EventLink(person=p, event=e).save()
        
        p = Person(first_name="b", last_name="b", gender='M', age=19, rank=Rank.get_kyu(5), instructor="asdf")
        p.save()
        EventLink(person=p, event=e).save()
        
        p = Person(first_name="c", last_name="c", gender='F', age=18, rank=Rank.get_kyu(3), instructor="asdf")
        p.save()
        EventLink(person=p, event=e).save()
        
        p = Person(first_name="d", last_name="d", gender='F', age=50, rank=Rank.get_kyu(1), instructor="asdf")
        p.save()
        EventLink(person=p, event=e).save()
        
        p = Person(first_name="e", last_name="e", gender='M', age=1, rank=Rank.get_dan(1), instructor="asdf")
        p.save()
        EventLink(person=p, event=e).save()
        
        p = Person(first_name="f", last_name="f", gender='M', age=19, rank=Rank.get_dan(3), instructor="asdf")
        p.save()
        EventLink(person=p, event=e).save()
        
        p = Person(first_name="g", last_name="g", gender='F', age=18, rank=Rank.get_dan(5), instructor="asdf")
        p.save()
        EventLink(person=p, event=e).save()
        
        p = Person(first_name="h", last_name="h", gender='F', age=50, rank=Rank.get_dan(9), instructor="asdf")
        p.save()
        EventLink(person=p, event=e).save()
        
        self.assertEqual(div_summary(), ([["a a"], ["b b"], ["c c"], ["d d"], ["e e"], ["f f"], ["g g"]], ["h h"]))
        
        # Create a manual EventLink
        EventLink(event=e, division=Division.objects.filter(event=e)[1], manual_name="m").save()
        self.assertEqual(div_summary(), ([["a a"], ["b b", "m"], ["c c"], ["d d"], ["e e"], ["f f"], ["g g"]], ["h h"]))
        
        # Create a Division after Person
        Division(event=e, gender='F', start_age=19, stop_age = 99, start_rank=  bb1, stop_rank=  bb9).save()
        self.assertEqual(div_summary(), ([["a a"], ["b b", "m"], ["c c"], ["d d"], ["e e"], ["f f"], ["g g"], ["h h"]], []))
        
        # Delete a division
        Division.objects.filter(event=e)[7].delete()
        self.assertEqual(div_summary(), ([["a a"], ["b b", "m"], ["c c"], ["d d"], ["e e"], ["f f"], ["g g"]], ["h h"]))
        
        # Delete a division as part of a merge. Manually added "m" will be dropped.
        d = Division.objects.filter(event=e)[1].delete()
        self.assertEqual(div_summary(), ([["a a"], ["c c"], ["d d"], ["e e"], ["f f"], ["g g"]], ["b b", "h h"]))
        
        # Expand a division as part of a merge
        d = Division.objects.filter(event=e)[2]
        d.gender = 'MF'
        d.save()
        self.assertEqual(div_summary(), ([["a a"], ["c c"], ["b b", "d d"], ["e e"], ["f f"], ["g g"]], ["h h"]))


class EventLinkTestCase(TestCase):
    
    def test_manual(self):
        p = Person(first_name="asdf", last_name="qwerty", gender='M', age=20,
            rank=Rank.objects.get(order=1), instructor="Mr. Instructor")
        p.save()
        
        e = Event(name="event")
        e.save()
        
        el = EventLink(manual_name='manual', event=e)
        self.assertTrue(el.is_manual)
        self.assertEqual(el.name, 'manual')
        
        el.person = p
        el.save()
        self.assertFalse(el.is_manual)
        self.assertEqual(el.name, "asdf qwerty")
        
        