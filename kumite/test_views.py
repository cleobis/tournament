import os
from time import sleep

from django.test import LiveServerTestCase, TestCase
from django_webtest import WebTest
from django.contrib.staticfiles.testing import StaticLiveServerTestCase

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
import selenium.webdriver.support.expected_conditions as EC

from .test_models import make_bracket
from accounts.models import RightsSupport

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
        else:
            self.skipTest("Selenium not available.")
        
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


class TestSwap(WebTest):
    
    def setUp(self):
        self.app.set_user(RightsSupport.create_edit_user())
    
    
    def test_swap(self):
        
        b = make_bracket(2)
        m = b.get_next_match()
        mp1 = m.aka
        mp2 = m.shiro
        
        resp = self.app.get(m.get_absolute_url())
        
        html = resp.html
        self.assertEqual(html.select(".aka h2")[0].string, "Aka: " + mp1.eventlink.name)
        self.assertEqual(html.select(".shiro h2")[0].string, "Ao: " + mp2.eventlink.name)
        
        # Fill out the form and click the submit button
        resp.form['aka-points'] = 1
        resp.form['aka-warnings'] = 2
        resp.form['shiro-points'] = 3
        resp.form['shiro-warnings'] = 4
        resp = resp.form.submit('btn_swap').follow()
        
        # Check that the fields are swapped
        html = resp.html
        self.assertEqual(html.select(".aka h2")[0].string, "Aka: " + mp2.eventlink.name)
        self.assertEqual(html.select(".shiro h2")[0].string, "Ao: " + mp1.eventlink.name)
        self.assertEqual(resp.form['aka-points'].value, "3")
        self.assertEqual(resp.form['aka-warnings'].value, "4")
        self.assertEqual(resp.form['shiro-points'].value, "1")
        self.assertEqual(resp.form['shiro-warnings'].value, "2")
        
        # Set winner. Make sure it is the right person
        resp.form['shiro-points'] = 10
        resp.form.submit('btn_done')
        m.refresh_from_db()
        self.assertTrue(m.done)
        self.assertTrue(m.aka_won)
        self.assertEqual(m.winner(), mp1.eventlink)
        self.assertEqual(m.loser(), mp2.eventlink)


class SlaveTestCase(StaticLiveServerTestCase):

    def setUp(self):
        super().setUp()
        self.config_driver()
        
        
    def tearDown(self):
        self.selenium.quit()
    
    
    def config_driver(self, desired_cap=None):
        from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
        
        username = os.environ.get('SAUCE_USERNAME')
        password = os.environ.get('SAUCE_ACCESS_KEY')
        if None in (username, password):
            self.selenium = webdriver.Chrome() # Safari doesn't work. Blocks inter-tab communication.
            self.selenium.implicitly_wait(5)
        else:
            # desired_cap = {
            #     # 'platform': "Mac OS X 10.9",
            #     'browserName': "internet explorer", # safari, chrome, firefox, android, iphone
            #     # 'version': "31",
            # }
            self.skipTest("Selenium not available.")
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
    
    
    def slave_helper(self, url):
        """Common tests between test_slave_manual() and test_slave_automatic.
        
        Tests the scores, warnings, time, and DQ work correctly on a manual match.
        
        Args:
            url: None to test manual kumit, a url to test a bracket match.
        Returns:
            (master_window, slave_window, iframe) selenium references.
        
        """
        
        selenium = self.selenium
        selenium.get(self.live_server_url)
        
        master_window = selenium.current_window_handle
        
        # Launch slave
        link = selenium.find_element_by_partial_link_text("2nd Display")
        link.click()
        WebDriverWait(selenium, 5).until(EC.number_of_windows_to_be(2))
        slave_window = selenium.window_handles
        slave_window = slave_window[1 if master_window == slave_window[0] else 0]
        self.assertNotEqual(slave_window, master_window)
        
        selenium.switch_to_window(slave_window)
        self.assertEqual(selenium.current_url, self.live_server_url + "/kumite/slave/")
        iframe = selenium.find_element_by_id("frame")
        self.assertEqual(iframe.get_attribute("src"), self.live_server_url + "/kumite/slave/waiting/")
        
        # Switch to Kumite Match
        selenium.switch_to_window(master_window)
        is_manual = url is None
        if is_manual:
            # Manual match
            link = selenium.find_element_by_link_text("Manual Kumite")
            link.click()
            url = self.live_server_url + "/kumite/match/manual/edit/?slave=true"
        else:
            # Bracket match
            selenium.get(url)
            url += "?slave=true"
        
        # selenium.switch_to_window(slave_window)
        selenium.switch_to_window(slave_window)
        sleep(.2)
        self.assertEqual(iframe.get_attribute("src"), url)
        
        # Click some buttons
        selenium.switch_to_window(master_window)
        # Shiro points = +5 - 1 = 4
        button = selenium.find_element_by_css_selector(".shiro .points button:first-of-type")
        for i in range(5):
            button.click()
        button = selenium.find_element_by_css_selector(".shiro .points button:last-of-type")
        button.click()
        # Shiro warnings = +4 - 1 = 3
        button = selenium.find_element_by_css_selector(".shiro .warnings button:first-of-type")
        for i in range(4):
            button.click()
        button = selenium.find_element_by_css_selector(".shiro .warnings button:last-of-type")
        button.click()
        # DQ shiro
        selenium.find_element_by_css_selector(".shiro .disqualified label").click()
        # Aka points = +3 - 1 = 2
        button = selenium.find_element_by_css_selector(".aka .points button:first-of-type")
        for i in range(3):
            button.click()
        button = selenium.find_element_by_css_selector(".aka .points button:last-of-type")
        button.click()
        # Aka warnings = +2 - 1 = 1
        button = selenium.find_element_by_css_selector(".aka .warnings button:first-of-type")
        for i in range(2):
            button.click()
        button = selenium.find_element_by_css_selector(".aka .warnings button:last-of-type")
        button.click()
        # Timer
        button = selenium.find_element_by_id("minus")
        button.click()
        time = selenium.find_element_by_id("time").text
        
        selenium.switch_to_window(slave_window)
        selenium.switch_to_frame(iframe)
        self.assertEqual(selenium.find_element_by_id("id_shiro-points").get_attribute("value"), "4")
        self.assertEqual(selenium.find_element_by_id("id_shiro-warnings").get_attribute("value"), "3")
        self.assertEqual(selenium.find_element_by_css_selector(".shiro .disqualified input").is_selected(), True)
        self.assertEqual(selenium.find_element_by_id("id_aka-points").get_attribute("value"), "2")
        self.assertEqual(selenium.find_element_by_id("id_aka-warnings").get_attribute("value"), "1")
        self.assertEqual(selenium.find_element_by_id("time").text, time)
        self.assertEqual(selenium.find_element_by_css_selector(".aka .disqualified input").is_selected(), False)
        
        # Reset time
        selenium.switch_to_window(master_window)
        selenium.find_element_by_id("reset").click()
        # Toggle DQs
        selenium.find_element_by_css_selector(".shiro .disqualified label").click()
        selenium.find_element_by_css_selector(".aka .disqualified label").click()
        
        selenium.switch_to_window(slave_window)
        selenium.switch_to_frame(iframe)
        self.assertEqual(selenium.find_element_by_id("time").text, "02:00")
        self.assertEqual(selenium.find_element_by_css_selector(".shiro .disqualified input").is_selected(), False)
        self.assertEqual(selenium.find_element_by_css_selector(".aka .disqualified input").is_selected(), True)
        
        # Timer countdown
        selenium.switch_to_window(master_window)
        selenium.find_element_by_id("start").click()
        sleep(1.1)
        selenium.find_element_by_id("stop").click()
        time = selenium.find_element_by_id("time").text
        self.assertEqual(time, "01:59")
        
        selenium.switch_to_window(slave_window)
        selenium.switch_to_frame(iframe)
        self.assertEqual(selenium.find_element_by_id("time").text, time)
        
        # Leave page
        selenium.switch_to_window(master_window)
        if is_manual:
            selenium.find_element_by_link_text("<").click()
        else:
            selenium.find_element_by_id("submit").click()
        
        selenium.switch_to_window(slave_window)
        iframe = selenium.find_element_by_id("frame")
        sleep(.2)
        self.assertEqual(iframe.get_attribute("src"), self.live_server_url + "/kumite/slave/waiting/")
        
        return (master_window, slave_window, iframe)
    
    
    def test_slave_manual(self):
        """Tests slave functionality for manual matches."""
        
        self.slave_helper(None)
    
    
    def test_slave_bracket(self):
        """Tests slave functionality for bracket matches.
        
        In addition to the tests from slave_helper, also tests swap functionality.
        """
        
        b = make_bracket(2)
        m = b.get_next_match()
        mp1 = m.aka
        mp2 = m.shiro
        
        selenium = self.selenium
        selenium.get(self.live_server_url)
        
        # Login
        selenium.find_element_by_link_text("Login").click()
        user = RightsSupport.create_edit_user()
        selenium.find_element_by_id("id_username").send_keys("edit")
        selenium.find_element_by_id("id_password").send_keys("edit" + Keys.RETURN)
        
        selenium.find_element_by_link_text("Logout edit") # errors if not found
        
        # Run common tests
        (master_window, slave_window, iframe) = self.slave_helper(self.live_server_url + m.get_absolute_url())
        
        # Load form
        selenium.switch_to_window(master_window)
        selenium.get(self.live_server_url + m.get_absolute_url())
        
        self.assertEqual(selenium.find_element_by_css_selector(".shiro h2").text, "Ao: b")
        self.assertEqual(selenium.find_element_by_id("id_shiro-points").get_attribute("value"), "4")
        self.assertEqual(selenium.find_element_by_css_selector(".aka h2").text, "Aka: a")
        self.assertEqual(selenium.find_element_by_id("id_aka-points").get_attribute("value"), "2")
        
        selenium.switch_to_window(slave_window)
        sleep(.2)
        self.assertEqual(iframe.get_attribute("src"), self.live_server_url + m.get_absolute_url() + "?slave=true")
        selenium.switch_to_frame(iframe)
        self.assertEqual(selenium.find_element_by_css_selector(".shiro h2").text, "Ao: b")
        self.assertEqual(selenium.find_element_by_id("id_shiro-points").get_attribute("value"), "4")
        self.assertEqual(selenium.find_element_by_css_selector(".aka h2").text, "Aka: a")
        self.assertEqual(selenium.find_element_by_id("id_aka-points").get_attribute("value"), "2")
        
        # Swap
        selenium.switch_to_window(master_window)
        selenium.find_element_by_name("btn_swap").click()
        
        self.assertEqual(selenium.find_element_by_css_selector(".shiro h2").text, "Ao: a")
        self.assertEqual(selenium.find_element_by_id("id_shiro-points").get_attribute("value"), "2")
        self.assertEqual(selenium.find_element_by_css_selector(".aka h2").text, "Aka: b")
        self.assertEqual(selenium.find_element_by_id("id_aka-points").get_attribute("value"), "4")
        
        selenium.switch_to_window(slave_window)
        sleep(.2)
        self.assertEqual(iframe.get_attribute("src"), self.live_server_url + m.get_absolute_url() + "?slave=true")
        selenium.switch_to_frame(iframe)
        self.assertEqual(selenium.find_element_by_css_selector(".shiro h2").text, "Ao: a")
        self.assertEqual(selenium.find_element_by_id("id_shiro-points").get_attribute("value"), "2")
        self.assertEqual(selenium.find_element_by_css_selector(".aka h2").text, "Aka: b")
        self.assertEqual(selenium.find_element_by_id("id_aka-points").get_attribute("value"), "4")
    
    
    def test_new_slave(self):
        """Tests a slave being opened after the kumite match has started.
        
        """
        
        selenium = self.selenium
        selenium.get(self.live_server_url + "/kumite/match/manual/edit/")
        
        master_window = selenium.current_window_handle
        
        # Launch slave manually after the match has started.
        selenium.execute_script("window.open('" + self.live_server_url + "/kumite/slave/" + "','_blank');");
        WebDriverWait(selenium, 5).until(EC.number_of_windows_to_be(2))
        slave_window = selenium.window_handles
        slave_window = slave_window[1 if master_window == slave_window[0] else 0]
        self.assertNotEqual(slave_window, master_window)
        
        selenium.switch_to_window(slave_window)
        self.assertEqual(selenium.current_url, self.live_server_url + "/kumite/slave/")
        iframe = selenium.find_element_by_id("frame")
        sleep(.2)
        self.assertEqual(iframe.get_attribute("src"), self.live_server_url + "/kumite/match/manual/edit/?slave=true")
        
        
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