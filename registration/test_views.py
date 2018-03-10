import os
import time

from django.core.urlresolvers import reverse
from django.test import LiveServerTestCase, TestCase

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from .models import Event, Division, Person, Rank, EventLink
from .views import IndexView

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