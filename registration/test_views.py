import os
import time

from django.urls import reverse
from django.test import LiveServerTestCase, TestCase
from django.contrib.auth import get_user_model

from django_webtest import WebTest

from parameterized import parameterized_class

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from .models import Event, Division, Person, Rank, EventLink
from .views import IndexView
from accounts.models import RightsSupport
import common.selenium

class PersonListTestCase(WebTest):
    
    def setUp(self):
        
        e_kumite = Event.objects.create(name="Kumite", format=Event.EventFormat.elim1)
        e_team_kata = Event.objects.create(name="Team kata", format=Event.EventFormat.kata, is_team=True)
        
        p = Person.objects.create(first_name="aaa", last_name="last1", gender='M', age=22, rank=Rank.get_kyu(8), instructor="asdf", paid=False, confirmed=False)
        EventLink.objects.create(person=p, event=e_kumite)
        
        p = Person.objects.create(first_name="bbb", last_name="last1", gender='F', age=22, rank=Rank.get_kyu(8), instructor="asdf", paid=False, confirmed=True)
        EventLink.objects.create(person=p, event=e_team_kata)
        
        p = Person.objects.create(first_name="ccc", last_name="ddd", gender='M', age=30, rank=Rank.get_kyu(8), instructor="asdf", paid=True, confirmed=False)
        EventLink.objects.create(person=p, event=e_kumite)
        
        p = Person.objects.create(first_name="eee", last_name="fff", gender='M', age=30, rank=Rank.get_kyu(8), instructor="asdf", paid=True, confirmed=True)
        EventLink.objects.create(person=p, event=e_kumite)
        EventLink.objects.create(person=p, event=e_team_kata)
        
        User = get_user_model()
        user = User.objects.create_user('temporary', 'temporary@gmail.com', 'temporary', is_staff=True, is_superuser=True)
        user.save()
        self.app.set_user("temporary")
    
    
    def test_person_paid_form(self):
        url = reverse('registration:index')
        resp = self.app.get(url)
        
        # Mark person as paid
        # WebTest runs without JavaScript so this doesn't test the inline replacing of table rows.
        p = Person.objects.get(first_name="aaa")
        form = resp.forms['form_paid_' + str(p.id)]
        resp = form.submit()
        
        self.assertRedirects(resp, url)
        resp = resp.follow()
        
        p.refresh_from_db()
        self.assertEqual(p.paid, True)
        self.assertEqual(p.confirmed, False) # No change
        self.assertNotIn('form_paid_' + str(p.id), resp.forms)
        self.assertEqual(resp.context['object_list'].count(), 4)
    
    
    def test_person_paid_inline(self):
        url = reverse('registration:index')
        resp = self.app.get(url)
        
        p = Person.objects.get(first_name="aaa")
        
        # Mark person as paid
        # Manually force the form to hit the endpoint used by the inline row replace.
        form = resp.forms['form_paid_' + str(p.id)]
        form.action = form.action + "?inline"
        resp = form.submit()
        
        self.assertRedirects(resp, reverse('registration:index-table-row', args=[p.id,]))
        resp = resp.follow()
        self.assertTrue(resp.text.startswith("<td>")) # Returns just table row
        p.refresh_from_db()
        self.assertEqual(p.paid, True)
        self.assertEqual(p.confirmed, False) # No change
        self.assertNotIn('form_paid_' + str(p.id), resp.forms)
    
    
    def test_person_confirmed_form(self):
        url = reverse('registration:index')
        resp = self.app.get(url)
        
        # Mark person as confirmed
        # WebTest runs without JavaScript so this doesn't test the inline replacing of table rows.
        p = Person.objects.get(first_name="aaa")
        form = resp.forms['form_confirmed_' + str(p.id)]
        resp = form.submit()
        
        self.assertRedirects(resp, url)
        resp = resp.follow()
        
        p.refresh_from_db()
        self.assertEqual(p.paid, False) # No change
        self.assertEqual(p.confirmed, True)
        self.assertNotIn('form_confirmed_' + str(p.id), resp.forms)
        self.assertEqual(resp.context['object_list'].count(), 4)
    
    
    def test_person_confirmed_inline(self):
        url = reverse('registration:index')
        resp = self.app.get(url)
        
        p = Person.objects.get(first_name="aaa")
        
        # Mark person as paid
        # Manually force the form to hit the endpoint used by the inline row replace.
        form = resp.forms['form_confirmed_' + str(p.id)]
        form.action = form.action + "?inline"
        resp = form.submit()
        
        self.assertRedirects(resp, reverse('registration:index-table-row', args=[p.id,]))
        resp = resp.follow()
        self.assertTrue(resp.text.startswith("<td>")) # Returns just table row
        p.refresh_from_db()
        self.assertEqual(p.paid, False) # No change
        self.assertEqual(p.confirmed, True)
        self.assertNotIn('form_confirmed_' + str(p.id), resp.forms)
    
    
    def test_person_filter(self):
        url = reverse('registration:index')
        resp = self.app.get(url)
        
        def names_summary(resp):
            return [x.first_name for x in resp.context['object_list']]
        
        self.assertEqual(names_summary(resp), ["ccc", "eee", "aaa", "bbb"])
        
        # Filter by last name
        form = resp.forms['filter_table']
        form['name'] = "last1"
        resp = form.submit()
        
        self.assertEqual(names_summary(resp), ["aaa", "bbb"])
        
        # Filter by name and confirmed
        form = resp.forms['filter_table']
        form['confirmed'] = True
        resp = form.submit()
        
        self.assertEqual(names_summary(resp), ["bbb"])
        
        # Filter by confirmed and paid, clear name
        form = resp.forms['filter_table']
        form['name'] = ""
        form['confirmed'] = False
        form['paid'] = True
        resp = form.submit()
        
        self.assertEqual(names_summary(resp), ["ccc"])
        
    
class DivisionDetailTestCase(WebTest):
    
    def setUp(self):
        self.app.set_user(RightsSupport.create_edit_user())
    
    
    def test_manual_eventlink(self):
        for is_team in [False, True]:
            e = Event(name="Team kata", format=Event.EventFormat.kata, is_team=is_team)
            e.save()
        
            white = Rank.get_kyu(9)
            brown = Rank.get_kyu(1)
            bb1 = Rank.get_dan(1)
            bb9 = Rank.get_dan(9)
            d = Division(event=e, gender='MF', start_age=1,  stop_age = 99, start_rank=white, stop_rank=bb9)
            d.save()
        
            p1 = Person(first_name="a", last_name="", gender='M', age=1, rank=Rank.get_kyu(8), instructor="asdf")
            p1.save()
            el1 = EventLink(person=p1, event=e)
            el1.save()
            
            url = d.get_absolute_url()
            resp = self.app.get(url)
            form = resp.forms['add_form']
            
            # Add manual
            form['manual_name'] = "asdf"
            resp = form.submit()
            
            self.assertRedirects(resp, url)
            el = d.eventlink_set.latest('pk')
            self.assertEqual(el.manual_name, "asdf")
            self.assertEqual(el.is_manual, True)
            self.assertEqual(d.eventlink_set.count(), 2)
            
            # Add empty name. Fails
            resp = resp.follow()
            form = resp.forms['add_form']
            form['manual_name'] = ""
            resp = form.submit()
            
            self.assertFormError(resp, 'add_form', 'manual_name', "Name cannot be empty.")
    
    def test_assign_team_form(self):
        e = Event(name="Team kata", format=Event.EventFormat.kata, is_team=True)
        e.save()
        
        white = Rank.get_kyu(9)
        brown = Rank.get_kyu(1)
        bb1 = Rank.get_dan(1)
        bb9 = Rank.get_dan(9)
        d = Division(event=e, gender='MF', start_age=1,  stop_age = 99, start_rank=white, stop_rank=bb9)
        d.save()
        
        p1 = Person(first_name="a", last_name="", gender='M', age=1, rank=Rank.get_kyu(8), instructor="asdf")
        p1.save()
        el1 = EventLink(person=p1, event=e)
        el1.save()
        
        p2 = Person(first_name="b", last_name="", gender='M', age=1, rank=Rank.get_kyu(8), instructor="asdf")
        p2.save()
        el2 = EventLink(person=p2, event=e)
        el2.save()
        
        el3 = EventLink(manual_name="m", event=e, division=d)
        el3.save()
        
        url = d.get_absolute_url()
        resp = self.app.get(url)
        form = resp.forms['team_assign_form']
        
        # Add a to a new team
        # t1 (a), unassigned (b, m)
        form['assign-src'] = el1.id
        resp = form.submit()
        self.assertRedirects(resp, url)
        
        self.assertEqual(d.eventlink_set.count(), 4)
        t1 = d.eventlink_set.latest('pk')
        self.assertEqual(t1.is_team, True)
        self.assertIn(el1, t1.eventlink_set.all())
        self.assertEqual(t1.eventlink_set.count(), 1)
        
        # Assign second person to same team
        # t1 (a, m), unassigned (b)
        resp = resp.follow()
        form = resp.forms['team_assign_form']
        form['assign-src'] = el3.id
        form['assign-tgt'] = t1.id
        resp = form.submit()
        self.assertRedirects(resp, url)
        
        self.assertEqual(d.eventlink_set.count(), 4)
        self.assertIn(el1, t1.eventlink_set.all())
        self.assertIn(el3, t1.eventlink_set.all())
        self.assertEqual(t1.eventlink_set.count(), 2)
        
        # Move one to a new team with unassigned person
        # t1 (m), t2 (a, b)
        resp = resp.follow()
        form = resp.forms['team_assign_form']
        form['assign-src'] = el1.id
        form['assign-tgt'] = el2.id
        resp = form.submit()
        self.assertRedirects(resp, url)
        
        self.assertEqual(d.eventlink_set.count(), 5)
        t1.refresh_from_db()
        t2 = d.eventlink_set.latest('pk')
        self.assertEqual(t1.is_team, True)
        self.assertIn(el3, t1.eventlink_set.all())
        self.assertEqual(t1.eventlink_set.count(), 1)
        self.assertEqual(t2.is_team, True)
        self.assertIn(el1, t2.eventlink_set.all())
        self.assertIn(el2, t2.eventlink_set.all())
        self.assertEqual(t2.eventlink_set.count(), 2)
        
        # Try moving a person to a person that is already in a team. Fails.
        resp = resp.follow()
        form = resp.forms['team_assign_form']
        form['assign-src'] = el3.id
        form['assign-tgt'] = el2.id
        resp = form.submit()
        self.assertFormError(resp, 'team_assign_form', 'tgt', "Select a valid choice. That choice is not one of the available choices.")
        
        # Try moving a team. Fails.
        form = resp.forms['team_assign_form']
        form['assign-src'] = t1.id
        form['assign-tgt'] = ""
        resp = form.submit()
        self.assertFormError(resp, 'team_assign_form', 'src', "Select a valid choice. That choice is not one of the available choices.")
        
        # Move last person from first team to second team. First team should be deleted.
        # t2 (a, b, m)
        form = resp.forms['team_assign_form']
        form['assign-src'] = el3.id
        form['assign-tgt'] = t2.id
        resp = form.submit()
        
        self.assertEqual(d.eventlink_set.count(), 4)
        self.assertEqual(d.eventlink_set.filter(pk=t1.id).count(), 0) # is deleted
        t2.refresh_from_db()
        self.assertEqual(t2.is_team, True)
        self.assertIn(el1, t2.eventlink_set.all())
        self.assertIn(el2, t2.eventlink_set.all())
        self.assertIn(el3, t2.eventlink_set.all())
        self.assertEqual(t2.eventlink_set.count(), 3)
        
        # Try assigning an EventLink from another division. Fails
        d2 = Division(event=e, gender='MF', start_age=99,  stop_age = 99, start_rank=bb9, stop_rank=bb9)
        d2.save()
        
        el4 = EventLink(manual_name="other", event=e, division=d2)
        el4.save() ;
        
        resp = resp.follow()
        form = resp.forms['team_assign_form']
        form['assign-src'] = el4.id
        form['assign-tgt'] = t2.id
        resp = form.submit()
        self.assertFormError(resp, 'team_assign_form', 'src', "Select a valid choice. That choice is not one of the available choices.")
        
        # Try assigning an EventLink to another division
        form = resp.forms['team_assign_form']
        form['assign-src'] = el2.id
        form['assign-tgt'] = el4.id
        resp = form.submit()
        self.assertFormError(resp, 'team_assign_form', 'tgt', "Select a valid choice. That choice is not one of the available choices.")


@parameterized_class(common.selenium.Env(include="Chrome").parameterized_class())
class ConsoleTestCase(common.selenium.SeleniumTestCaseHelper):
    
    def test_console(self):
        
        selenium = self.selenium
        selenium.get(self.live_server_url)
        
        self.assert_selenium_logs()
    
# Disabled because the events don't work properly with Selenium.
# class IndexViewTestCase(LiveServerTestCase):
#
#     def setUp(self):
#         super().setUp()
#
#
#     def config_driver(self, desired_cap):
#         from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
#
#         username = os.environ.get('SAUCE_USERNAME')
#         password = os.environ.get('SAUCE_ACCESS_KEY')
#         if None in (username, password):
#             self.selenium = webdriver.Safari()
#             self.selenium.implicitly_wait(5)
#         else:
#             # desired_cap = {
#             #     # 'platform': "Mac OS X 10.9",
#             #     'browserName': "internet explorer", # safari, chrome, firefox, android, iphone
#             #     # 'version': "31",
#             # }
#             job = os.environ.get('TRAVIS_JOB_NUMBER')
#             if job is not None:
#                 desired_cap['tunnel-identifier'] = job
#             build = os.environ.get("TRAVIS_BUILD_NUMBER")
#             if build is not None:
#                 desired_cap['build'] = build
#             tag = os.environ.get("TRAVIS_PYTHON_VERSION")
#             if tag is not None:
#                 desired_cap['tags'] = [tag, "CI"]
#             self.selenium = webdriver.Remote(
#                command_executor='http://' + username + ':' + password + '@ondemand.saucelabs.com:80/wd/hub',
#                desired_capabilities=desired_cap)
#
#
#     def tearDown(self):
#         # self.selenium.quit()
#         super().tearDown()
#
#
#     def test_run(self):
#
#         caps = [
#             # {'browserName': "internet explorer", 'version': "8"}, # Renders wrong
#             # {'browserName': "internet explorer", 'version': "9"}, # Renders wrong
#             # {'browserName': "internet explorer", 'version': "10"}, # Renders wrong
#             {'browserName': "internet explorer", 'version': "11"},
#             {'browserName': 'MicrosoftEdge'}, # Failed to connect
#             {'browserName': 'Chrome'},
#             {'browserName': 'firefox'},
#             # {'browserName': "Safari", 'version': "7"}, # Renders wrong
#             # {'browserName': "Safari", 'version': "8"}, # Fails to connect
#             {'browserName': "Safari", 'version': "9"}, # Fails to connect
#             {'browserName': "Safari", 'version': "10"},
#             {'browserName': "Safari", 'platformVersion': "11"},
#             {'browserName': "Safari", 'platformVersion': "10.3"},
#             {'browserName': "Safari", 'platformVersion': "9.3"},
#             {'browserName': "Android", 'platformVersion': "4.4"},
#             {'browserName': "Android", 'platformVersion': "5.1"},
#             {'browserName': "Android", 'platformVersion': "6.0"},
#             ]
#         if os.environ.get('SAUCE_USERNAME') is None:
#             caps = [{}]
#
#         for c in caps:
#             with self.subTest(cap=c):
#                 self.config_driver(c)
#                 try:
#                     self.helper()
#                 finally:
#                     self.selenium.quit()
#
#
#     def get_table_people(self):
#         tds = self.selenium.find_elements_by_css_selector('#person_table tr td:first-child')
#         return [x.text.strip() for x in tds]
#
#
#     def helper(self):
#
#         ekata = Event(name='kata', format=Event.EventFormat.kata)
#         ekata.save()
#         ekumite = Event(name='kumite', format=Event.EventFormat.elim1)
#         ekumite.save()
#
#         def make_person(events=None, **kwargs):
#             if 'age' not in kwargs:
#                 kwargs['age'] = 30
#             if 'rank' not in kwargs:
#                 print("Hi")
#                 for r in Rank.objects.all():
#                     print(r)
#                 print("bye")
#                 kwargs['rank'] = Rank.objects.get(order=1)
#             p = Person(**kwargs)
#             p.save(p)
#             for e_name in events:
#                 el = EventLink(person=p, event=Event.objects.get(name=e_name))
#                 el.save()
#
#         make_person(first_name="Mark", last_name="Patterson", events=("kata",), paid=True)
#         make_person(first_name="Aaaa", last_name="bbbb", events=("kata", "kumite"), paid=True)
#         make_person(first_name="Cccc", last_name="Bbbb", events=("kumite",), paid=False)
#         make_person(first_name="Dddd", last_name="Eeee", events=("kata", "kumite"), paid=False)
#
#         selenium = self.selenium
#         selenium.get(self.live_server_url + reverse('registration:index'))
#         input_name = selenium.find_element_by_id('id_name')
#         input_paid = selenium.find_element_by_id('id_paid')
#
#         people = self.get_table_people()
#         self.assertEqual(people, ["Mark Patterson", "Aaaa bbbb", "Cccc Bbbb", "Dddd Eeee"])
#
#         # input_name.send_keys('k Patt')
#         # print(self.get_table_people())
#         # time.sleep(1)
#         # print(self.get_table_people())
#         time.sleep(1)
#         selenium.execute_script("$('#id_name').val('k Patt').keyup()")
#         # selenium.execute_script("document.getElementById('id_name').keyup();")
#         time.sleep(1)
#         print(self.get_table_people())
#
#
#         time.sleep(5)
#
#
#