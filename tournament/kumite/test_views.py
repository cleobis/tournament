import os

from django.test import LiveServerTestCase, TestCase

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains

from .test_models import make_bracket


class MatchViewTestCase(LiveServerTestCase):

    def setUp(self):
        super().setUp()
    
    
    def config_driver(self, desired_cap):
        from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
        
        username = os.environ.get('SAUCE_USERNAME')
        password = os.environ.get('SAUCE_ACCESS_KEY')
        if None in (username, password):
            self.selenium = webdriver.Safari()
            self.selenium.implicitly_wait(5)
        else:
            # desired_cap = {
            #     # 'platform': "Mac OS X 10.9",
            #     'browserName': "internet explorer", # safari, chrome, firefox, android, iphone
            #     # 'version': "31",
            # }
            job = os.environ.get('TRAVIS_JOB_NUMBER')
            if job is not None:
                desired_cap['tunnel-identifier'] = job
            build = os.environ.get("TRAVIS_BUILD_NUMBER")
            if build is not None:
                desired_cap['build'] = build
            tag = os.environ.get("TRAVIS_PYTHON_VERSION")
            if tag is not None:
                desired_cap['tags'] = [tag, "CI"]
            self.selenium = webdriver.Remote(
               command_executor='http://' + username + ':' + password + '@ondemand.saucelabs.com:80/wd/hub',
               desired_capabilities=desired_cap)
    
    
    def tearDown(self):
        # self.selenium.quit()
        super().tearDown()
    
    
    def test_manual_match(self):
        
        caps = [
            # {'browserName': "internet explorer", 'version': "8"}, # Renders wrong
            # {'browserName': "internet explorer", 'version': "9"}, # Renders wrong
            # {'browserName': "internet explorer", 'version': "10"}, # Renders wrong
            {'browserName': "internet explorer", 'version': "11"},
            {'browserName': 'MicrosoftEdge'}, # Failed to connect
            {'browserName': 'Chrome'},
            {'browserName': 'firefox'},
            # {'browserName': "Safari", 'version': "7"}, # Renders wrong
            # {'browserName': "Safari", 'version': "8"}, # Fails to connect
            {'browserName': "Safari", 'version': "9"}, # Fails to connect
            {'browserName': "Safari", 'version': "10"},
            {'browserName': "Safari", 'platformVersion': "11"},
            {'browserName': "Safari", 'platformVersion': "10.3"},
            {'browserName': "Safari", 'platformVersion': "9.3"},
            {'browserName': "Android", 'platformVersion': "4.4"},
            {'browserName': "Android", 'platformVersion': "5.1"},
            {'browserName': "Android", 'platformVersion': "6.0"},
            ]
        if os.environ.get('SAUCE_USERNAME') is None:
            caps = [{}]
        
        for c in caps:
            with self.subTest(cap=c):
                self.config_driver(c)
                try:
                    self.helper()
                finally:
                    self.selenium.quit()
        
    def helper(self):
        selenium = self.selenium
        selenium.get(self.live_server_url + '/kumite/match/manual/edit/')
        
        # Aka points = 1. Checks + and - buttons
        buttonp = selenium.find_element_by_css_selector('.aka .points button:nth-last-child(2)')
        buttonm = selenium.find_element_by_css_selector('.aka .points button:nth-last-child(1)')
        buttonp.click()
        buttonp.click()
        buttonm.click()
        
        # Aka warnings = 2. Checks clip to zero
        buttonp = selenium.find_element_by_css_selector('.aka .warnings button:nth-last-child(2)')
        buttonm = selenium.find_element_by_css_selector('.aka .warnings button:nth-last-child(1)')
        buttonm.click()
        buttonp.click()
        buttonp.click()
        
        # Shiro points = 3
        buttonp = selenium.find_element_by_css_selector('.shiro .points button:nth-last-child(2)')
        buttonm = selenium.find_element_by_css_selector('.shiro .points button:nth-last-child(1)')
        buttonp.click()
        buttonp.click()
        buttonm.click()
        buttonp.click()
        buttonp.click()
        
        # Shiro warnings = 0
        buttonp = selenium.find_element_by_css_selector('.shiro .warnings button:nth-last-child(2)')
        buttonm = selenium.find_element_by_css_selector('.shiro .warnings button:nth-last-child(1)')
        buttonp.click()
        buttonp.click()
        buttonm.click()
        buttonm.click()
        buttonp.click()
        buttonm.click()
        
        # Check values
        input = selenium.find_element_by_css_selector('.aka .points input')
        self.assertEqual(input.get_attribute("value"), "1")
        input = selenium.find_element_by_css_selector('.aka .warnings input')
        self.assertEqual(input.get_attribute("value"), "2")
        input = selenium.find_element_by_css_selector('.shiro .points input')
        self.assertEqual(input.get_attribute("value"), "3")
        input = selenium.find_element_by_css_selector('.shiro .warnings input')
        self.assertEqual(input.get_attribute("value"), "0")
        
        # Check Clear
        buttonp.click() # Make shiro warnings non-zero
        button = selenium.find_element_by_id('clear')
        button.click()
        input = selenium.find_element_by_css_selector('.aka .points input')
        self.assertEqual(input.get_attribute("value"), "0")
        input = selenium.find_element_by_css_selector('.aka .warnings input')
        self.assertEqual(input.get_attribute("value"), "0")
        input = selenium.find_element_by_css_selector('.shiro .points input')
        self.assertEqual(input.get_attribute("value"), "0")
        input = selenium.find_element_by_css_selector('.shiro .warnings input')
        self.assertEqual(input.get_attribute("value"), "0")
        
        
        # TODO: Test timer, manually editing field, data saved to model correctly


# HTML5 drag and drop doesn't work with Selenium.
# class KumiteMatchPersonSwapViewTestCase(LiveServerTestCase):
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
#     def test_swap(self):
#
#         caps = [
#             # {'browserName': "internet explorer", 'version': "8"}, # Renders wrong
#             # {'browserName': "internet explorer", 'version': "9"}, # Renders wrong
#             # {'browserName': "internet explorer", 'version': "10"}, # Renders wrong
#             # {'browserName': "internet explorer", 'version': "11"}, # Drag works.
#             # {'browserName': 'MicrosoftEdge'}, # Failed to connect, Drag works.
#             # {'browserName': 'Chrome'}, # Drag works.
#             # {'browserName': 'firefox'}, # Drag not supported
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
#     def helper(self):
#
#
#         b = make_bracket(5)
#
#         selenium = self.selenium
#         # selenium.get(self.live_server_url + b.get_absolute_url())
#         selenium.get('http://chiron.afraid.org:8000/kumite/bracket-n/30/')
#
#
#         src = selenium.find_element(By.XPATH, '//td[contains(text(), "a")]')
#         tgt = selenium.find_element(By.XPATH, '//td[contains(text(), "d")]')
#         src.click()
#         ActionChains(selenium).drag_and_drop(src, tgt).perform()
#         src.click()
#         time.sleep(4)
#
#         return
#
#         # Aka points = 1. Checks + and - buttons
#         buttonp = selenium.find_element_by_css_selector('.aka .points button:nth-last-child(2)')
#         buttonm = selenium.find_element_by_css_selector('.aka .points button:nth-last-child(1)')
#         buttonp.click()
#         buttonp.click()
#         buttonm.click()
#
#         # Aka warnings = 2. Checks clip to zero
#         buttonp = selenium.find_element_by_css_selector('.aka .warnings button:nth-last-child(2)')
#         buttonm = selenium.find_element_by_css_selector('.aka .warnings button:nth-last-child(1)')
#         buttonm.click()
#         buttonp.click()
#         buttonp.click()
#
#         # Shiro points = 3
#         buttonp = selenium.find_element_by_css_selector('.shiro .points button:nth-last-child(2)')
#         buttonm = selenium.find_element_by_css_selector('.shiro .points button:nth-last-child(1)')
#         buttonp.click()
#         buttonp.click()
#         buttonm.click()
#         buttonp.click()
#         buttonp.click()
#
#         # Shiro warnings = 0
#         buttonp = selenium.find_element_by_css_selector('.shiro .warnings button:nth-last-child(2)')
#         buttonm = selenium.find_element_by_css_selector('.shiro .warnings button:nth-last-child(1)')
#         buttonp.click()
#         buttonp.click()
#         buttonm.click()
#         buttonm.click()
#         buttonp.click()
#         buttonm.click()
#
#         # Check values
#         input = selenium.find_element_by_css_selector('.aka .points input')
#         self.assertEqual(input.get_attribute("value"), "1")
#         input = selenium.find_element_by_css_selector('.aka .warnings input')
#         self.assertEqual(input.get_attribute("value"), "2")
#         input = selenium.find_element_by_css_selector('.shiro .points input')
#         self.assertEqual(input.get_attribute("value"), "3")
#         input = selenium.find_element_by_css_selector('.shiro .warnings input')
#         self.assertEqual(input.get_attribute("value"), "0")
#
#         # Check Clear
#         buttonp.click() # Make shiro warnings non-zero
#         button = selenium.find_element_by_id('clear')
#         button.click()
#         input = selenium.find_element_by_css_selector('.aka .points input')
#         self.assertEqual(input.get_attribute("value"), "0")
#         input = selenium.find_element_by_css_selector('.aka .warnings input')
#         self.assertEqual(input.get_attribute("value"), "0")
#         input = selenium.find_element_by_css_selector('.shiro .points input')
#         self.assertEqual(input.get_attribute("value"), "0")
#         input = selenium.find_element_by_css_selector('.shiro .warnings input')
#         self.assertEqual(input.get_attribute("value"), "0")
#