from django.test import TestCase
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from .models import Person, Rank, EventLink, Division, Event, import_registrations

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
    
    
    def test_parse(self):
        
        for r in Rank.objects.all():
            r2 = Rank.parse(str(r))
            self.assertEqual(r2,r)
        
        with self.assertRaises(ValueError):
            Rank.parse("asdflaksjdf")


class DivisionTestCase(TestCase):
    
    
    def test_get_eventlinks(self):
        e = Event(name="event", format=Event.EventFormat.kata)
        e.save()
        
        d = Division(event=e, gender='M', start_age=1,  stop_age = 18, start_rank=Rank.get_kyu(9), stop_rank=Rank.get_dan(9))
        d.save()
        
        p_confirmed = Person(first_name="a", last_name="b", age="10", rank=Rank.get_kyu(5), gender='M', confirmed=True)
        p_confirmed.save()
        el = EventLink(event=e, person=p_confirmed)
        el.save()
        
        p_noshow = Person(first_name="c", last_name="d", age="10", rank=Rank.get_kyu(5), gender='M', confirmed=False)
        p_noshow.save()
        el = EventLink(event=e, person=p_noshow)
        el.save()
        
        el_manual = EventLink(event=e, division=d, manual_name="manual")
        el_manual.save()
        
        ppl = d.get_confirmed_eventlinks()
        self.assertTrue(len(ppl) == 2)
        self.assertIn(p_confirmed.eventlink_set.get(), ppl)
        self.assertIn(el_manual, ppl)
        
        ppl = d.get_noshow_eventlinks()
        self.assertIn(p_noshow.eventlink_set.get(), ppl)
        
    
    def test_claim(self):
        e = Event(name="event", format=Event.EventFormat.kata)
        e.save()
        
        # Create some divisions
        white = Rank.get_kyu(9)
        brown = Rank.get_kyu(1)
        bb1 = Rank.get_dan(1)
        bb9 = Rank.get_dan(9)
        Division(event=e, gender='M', start_age=1,  stop_age = 18, start_rank=white, stop_rank=brown).save()
        Division(event=e, gender='M', start_age=19, stop_age = 99, start_rank=white, stop_rank=brown).save() # <= deleted laster
        Division(event=e, gender='F', start_age=1,  stop_age = 18, start_rank=white, stop_rank=brown).save()
        Division(event=e, gender='F', start_age=19, stop_age = 99, start_rank=white, stop_rank=brown).save() # <= merged with deleted
        Division(event=e, gender='M', start_age=1,  stop_age = 18, start_rank=  bb1, stop_rank=  bb9).save()
        Division(event=e, gender='M', start_age=19, stop_age = 99, start_rank=  bb1, stop_rank=  bb9).save()
        Division(event=e, gender='F', start_age=1,  stop_age = 18, start_rank=  bb1, stop_rank=  bb9).save()
        # Create this later: Division(event=e, gender='F', start_age=19, stop_age = 99, start_rank=  bb1, stop_rank=  bb9).save()
        
        def get_divs():
            return Division.objects.filter(event=e).order_by('pk') # Clear sorting so the above order is retained
        
        def div_summary():
            return ([[el.name for el in d.eventlink_set.order_by('pk')] for d in get_divs()],
                [el.name for el in e.get_orphan_links().order_by('pk')])
        
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
        EventLink(event=e, division=get_divs()[1], manual_name="m").save()
        self.assertEqual(div_summary(), ([["a a"], ["b b", "m"], ["c c"], ["d d"], ["e e"], ["f f"], ["g g"]], ["h h"]))
        
        # Force a person to be in the wrong division
        p = Person(first_name="o", last_name="d", gender='F', age=25, rank = Rank.get_kyu(5), instructor="asdf")
        p.save()
        EventLink(person=p, event=e, division=get_divs()[1], locked=True).save()
        self.assertEqual(div_summary(), ([["a a"], ["b b", "m", "o d"], ["c c"], ["d d"], ["e e"], ["f f"], ["g g"]], ["h h"]))
        
        # Force a person to be in no division
        p = Person(first_name="o", last_name="n", gender='F', age=25, rank = Rank.get_kyu(5), instructor="asdf")
        p.save()
        EventLink(person=p, event=e, division=None, locked=True).save()
        self.assertEqual(div_summary(), ([["a a"], ["b b", "m", "o d"], ["c c"], ["d d"], ["e e"], ["f f"], ["g g"]], ["h h", "o n"]))
        
        # Create a Division after Person
        Division(event=e, gender='F', start_age=19, stop_age = 99, start_rank=  bb1, stop_rank=  bb9).save()
        self.assertEqual(div_summary(), ([["a a"], ["b b", "m", "o d"], ["c c"], ["d d"], ["e e"], ["f f"], ["g g"], ["h h"]], ["o n"]))
        
        # Delete a division
        get_divs()[7].delete()
        self.assertEqual(div_summary(), ([["a a"], ["b b", "m", "o d"], ["c c"], ["d d"], ["e e"], ["f f"], ["g g"]], ["h h", "o n"]))
        
        # Delete a division as part of a merge. Manually added "m" will be dropped.
        d = get_divs()[1].delete()
        self.assertEqual(div_summary(), ([["a a"], ["c c"], ["d d"], ["e e"], ["f f"], ["g g"]], ["b b", "h h", "o d", "o n"]))
        
        # Expand a division as part of a merge
        d = get_divs()[2]
        d.gender = 'MF'
        d.save()
        self.assertEqual(div_summary(), ([["a a"], ["c c"], ["b b", "d d"], ["e e"], ["f f"], ["g g"]], ["h h", "o d", "o n"]))


class PersonTestCase(TestCase):
    
    def test_required_parent(self):
        p = Person(first_name="asdf", last_name="qwerty", gender='M', age=10,
            rank=Rank.objects.get(order=1), instructor="Mr. Instructor")
        with self.assertRaises(ValidationError):
            p.full_clean()
        
        p.age = 10
        p.parent = "asdf"
        p.full_clean() # okay
        
        p.age = 17
        p.parent = "asdf"
        p.full_clean() # okay
        
        p.age = 17
        p.parent = ""
        with self.assertRaises(ValidationError):
            p.full_clean()
        
        p.age = 18
        p.parent = ""
        p.full_clean() # okay
        
        p.age = 18
        p.parent = "asdf"
        p.full_clean() # okay


class EventLinkTestCase(TestCase):
    
    def test_manual(self):
        p = Person(first_name="asdf", last_name="qwerty", gender='M', age=20,
            rank=Rank.objects.get(order=1), instructor="Mr. Instructor")
        p.save()
        
        e = Event(name="event", format=Event.EventFormat.kata)
        e.save()
        
        el = EventLink(manual_name='manual', event=e)
        self.assertTrue(el.is_manual)
        self.assertEqual(el.name, 'manual')
        
        el.person = p
        el.save()
        self.assertFalse(el.is_manual)
        self.assertEqual(el.name, "asdf qwerty")
        

class ImportRegistrationTestCase(TestCase):
    
    def test_import_registration(self):
        import io
        
        input = io.StringIO("""Timestamp,First Name,Last Name,Gender,Age,Rank,Instructor,Phone number,Email,Events,Notes,Address,City,Province,Postal Code,Waiver,Email Address,Name of parent or guardian (competitors under 18 years),Address
1/8/2018 18:46:43,Hunter,Pratt,Male,15,Purple (4th kyu),Francisco Salazar,5196853680,,"Kumite",,40 Woolley Street,Cambridge,Ontario,N1R 5J8,I agree,am_pratt@hotmail.com,Ann Pratt,
1/10/2018 14:39:21,Sean,Garcia,Male,30,Nidan (2nd dan black belt),Sandy Rooney/ Kim Dunn/ Tom Okura,9058186599,,"Kata, Kumite",,50 Glen Road,Hamilton,ON,L8S4N3,I agree,seansqgarcia@gmail.com,,""", newline='')
        
        self.assertEqual(len(Person.objects.all()), 0)
        
        kata = Event(name="Kata", format=Event.EventFormat.elim1)
        kata.save()
        kumite = Event(name="Kumite", format=Event.EventFormat.elim1)
        kumite.save()
        white = Rank.get_kyu(9)
        bb9 = Rank.get_dan(9)
        d_kata   = Division(event=kata,   gender='MF', start_age=1,  stop_age = 99, start_rank=white, stop_rank=bb9)
        d_kata.save()
        d_kumite = Division(event=kumite, gender='M',  start_age=1,  stop_age = 99, start_rank=white, stop_rank=bb9)
        d_kumite.save()
        # No female kumite: Division(event=kumite, gender='F',  start_age=1,  stop_age = 99, start_rank=white, stop_rank=bb9).save()
        
        stats = import_registrations(input)
        self.assertEqual(stats, {"added": 2, "skipped": 0})
        
        def person2str(p):
            fields = ('first_name', 'last_name', 'gender', 'age', 'rank', 'instructor', 'phone_number', 'email', 'parent', 'reg_date', 'paid', 'notes', 'eventlink_set')
            str = ""
            for f in fields:
                if f == "eventlink_set":
                    v = ", ".join(el.event.name for el in p.eventlink_set.all())
                elif f == "reg_date":
                    v = p.reg_date.strftime("%Y-%m-%d %H:%M:%S")
                else:
                    v = getattr(p, f)
                str = str + "{} => {}\n".format(f, v)
            return str
        
        people = Person.objects.order_by("reg_date")
        self.assertEqual(len(people), 2)
        # self.maxDiff = None
        self.assertEqual(person2str(people[0]), """first_name => Hunter
last_name => Pratt
gender => M
age => 15
rank => Purple (4th kyu)
instructor => Francisco Salazar
phone_number => 5196853680
email => am_pratt@hotmail.com
parent => Ann Pratt
reg_date => 2018-01-08 18:46:43
paid => False
notes => 
eventlink_set => Kumite
""")
        self.assertEqual(people[0].eventlink_set.get(event=kumite).division, d_kumite) # length checked with person2str()

        self.assertEqual(person2str(people[1]), """first_name => Sean
last_name => Garcia
gender => M
age => 30
rank => Nidan (2nd dan black belt)
instructor => Sandy Rooney/ Kim Dunn/ Tom Okura
phone_number => 9058186599
email => seansqgarcia@gmail.com
parent => 
reg_date => 2018-01-10 14:39:21
paid => False
notes => 
eventlink_set => Kata, Kumite
""")
        self.assertEqual(people[1].eventlink_set.get(event=kumite).division, d_kumite) # length checked with
        self.assertEqual(people[1].eventlink_set.get(event=kata).division, d_kata)

        input = io.StringIO("""Timestamp,First Name,Last Name,Gender,Age,Rank,Instructor,Phone number,Email,Events,Notes,Address,City,Province,Postal Code,Waiver,Email Address,Name of parent or guardian (competitors under 18 years),Address
1/8/2018 18:46:43,Hunter,Pratt,Male,15,Purple (4th kyu),Francisco Salazar,5196853680,,"Kumite",,40 Woolley Street,Cambridge,Ontario,N1R 5J8,I agree,am_pratt@hotmail.com,Ann Pratt,
1/10/2018 14:39:21,Sean,Garcia,Male,30,Nidan (2nd dan black belt),Sandy Rooney/ Kim Dunn/ Tom Okura,9058186599,,"Kata, Kumite",,50 Glen Road,Hamilton,ON,L8S4N3,I agree,seansqgarcia@gmail.com,,
1/11/2018 21:31:54,Charlotte,Robertson,Female,11,Blue (5th kyu),Roney,905 637 8309,,"Kata, Kumite","Hello
there",683 Demaris Crt.,Burlington,Ontario,L7L 5C9,I agree,cg.robertson06@icloud.com,Gordon Robertson,""", newline='')

        people = Person.objects.order_by("reg_date")
        stats = import_registrations(input)
        self.assertEqual(stats, {"added": 1, "skipped": 2})
        
        self.assertEqual(len(people), 3)
        self.maxDiff = None
        self.assertEqual(person2str(people[2]), """first_name => Charlotte
last_name => Robertson
gender => F
age => 11
rank => Blue (5th kyu)
instructor => Roney
phone_number => 905 637 8309
email => cg.robertson06@icloud.com
parent => Gordon Robertson
reg_date => 2018-01-11 21:31:54
paid => False
notes => Hello
there
eventlink_set => Kata, Kumite
""")
        self.assertEqual(people[2].eventlink_set.get(event=kata).division, d_kata)
        self.assertEqual(people[2].eventlink_set.get(event=kumite).division, None)


def create_random_people(n):
    import names
    import random
    
    kata = Event.objects.get(name='Kata')
    kumite = Event.objects.get(name='Kumite')
    
    def rand_rank():
        r = random.randint(-9,4)
        if r >= 0:
            r += 1 # 0 not allowed
        return Rank.objects.get(order=r)
    
    for i in range(n):
        p = Person()
        if random.random() > 0.5:
            p.first_name = names.get_first_name(gender='male')
            p.gender = 'M'
        else:
            p.first_name = names.get_first_name(gender='female')
            p.gender = 'F'
        p.last_name = names.get_last_name()
        p.paid = random.random() > 0.5
        p.age = random.randint(6,30)
        p.rank = rand_rank()
        p.save()
        
        events = random.randint(1,3)
        if events == 1 or events == 3:
            el = EventLink(person=p,event=kata)
            el.save()
        if events == 2 or events == 3:
            el = EventLink(person=p,event=kumite)
            el.save()
        
