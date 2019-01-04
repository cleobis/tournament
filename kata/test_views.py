from django.urls import reverse
from django.test import TestCase

from django_webtest import WebTest

from registration.models import Event, Division, Person, Rank, EventLink
from .views import KataBracketDetails


class KataDetailTestCase(WebTest):
    
    def test_person_form(self):
        e = Event(name="Team kata", format=Event.EventFormat.kata)
        e.save()
        
        white = Rank.get_kyu(9)
        brown = Rank.get_kyu(1)
        bb1 = Rank.get_dan(1)
        bb9 = Rank.get_dan(9)
        d = Division(event=e, gender='MF', start_age=1,  stop_age = 99, start_rank=white, stop_rank=bb9)
        d.save()
        
        p1 = Person(first_name="a", last_name="", gender='M', age=1, rank=Rank.get_kyu(8), instructor="asdf", confirmed=True)
        p1.save()
        el1 = EventLink(person=p1, event=e)
        el1.save()
        
        p2 = Person(first_name="late arrival", last_name="", gender='M', age=1, rank=Rank.get_kyu(8), instructor="asdf", confirmed=False)
        p2.save()
        el2 = EventLink(person=p2, event=e)
        el2.save()
        
        el3 = EventLink(manual_name="m", event=e, division=d)
        el3.save()
        
        d.build_format()
        
        url = d.get_format().get_absolute_url()
        resp = self.app.get(url)
        
        # Submit blank form. Fails
        form = resp.forms['add_form']
        resp = form.submit()
        self.assertFormError(resp, 'add_form', None, "Specify either manual name or select from menu.")
        
        # Submit both manual_name and eventlink. Fails
        form = resp.forms['add_form']
        form['manual_name'] = "asdf"
        form['existing_eventlink'] = el2.id
        resp = form.submit()
        self.assertFormError(resp, 'add_form', None, "Specify only one of manual name or selection from menu.")
        
        # Add manual person to new team
        form = resp.forms['add_form']
        form['manual_name'] = "manual added"
        form['existing_eventlink'] = ""
        resp = form.submit()
        self.assertRedirects(resp, url)
        resp = resp.follow()
        resp.mustcontain("<td>manual added</td>")
        
        # Add late arrival p2 to team 2
        form = resp.forms['add_form']
        form['existing_eventlink'] = el2.id
        resp = form.submit()
        self.assertRedirects(resp, url)
        resp = resp.follow()
        resp.mustcontain("<td>late arrival</td>")
    
    def test_add_team_form(self):
        e = Event(name="Team kata", format=Event.EventFormat.kata, is_team=True)
        e.save()
        
        white = Rank.get_kyu(9)
        brown = Rank.get_kyu(1)
        bb1 = Rank.get_dan(1)
        bb9 = Rank.get_dan(9)
        d = Division(event=e, gender='MF', start_age=1,  stop_age = 99, start_rank=white, stop_rank=bb9)
        d.save()
        
        t1 = EventLink(event=e, division=d, is_team=True)
        t1.save()
        
        p1 = Person(first_name="a", last_name="", gender='M', age=1, rank=Rank.get_kyu(8), instructor="asdf")
        p1.save()
        el1 = EventLink(person=p1, event=e, team=t1)
        el1.save()
        
        p2 = Person(first_name="a", last_name="", gender='M', age=1, rank=Rank.get_kyu(8), instructor="asdf")
        p2.save()
        el2 = EventLink(person=p2, event=e)
        el2.save()
        
        el3 = EventLink(manual_name="m", event=e, division=d)
        el3.save()
        
        d.build_format()
        
        url = d.get_format().get_absolute_url()
        resp = self.app.get(url)
        
        # Submit blank form. Fails
        form = resp.forms['add_form']
        resp = form.submit()
        self.assertFormError(resp, 'add_form', None, "Specify either manual name or select from menu.")
        
        # Submit both manual_name and eventlink. Fails
        form = resp.forms['add_form']
        form['manual_name'] = "asdf "
        form['existing_eventlink'] = el2.id
        resp = form.submit()
        self.assertFormError(resp, 'add_form', None, "Specify only one of manual name or selection from menu.")
        
        # Add manual person to new team
        form = resp.forms['add_form']
        form['manual_name'] = "manual added"
        form['existing_eventlink'] = ""
        resp = form.submit()
        self.assertRedirects(resp, url)
        resp = resp.follow()
        resp.mustcontain("<td>Team manual added</td>")
        t2 = d.get_confirmed_eventlinks().get(eventlink__manual_name="manual added")
        
        # Add late arrival p2 to team 2
        form = resp.forms['add_form']
        form['existing_eventlink'] = el2.id
        form['team'] = t2.id
        resp = form.submit()
        self.assertRedirects(resp, url)
        resp = resp.follow()
        resp.mustcontain("<td>Team a and manual added</td>")
        
        
        