import os

from django.test import LiveServerTestCase
from selenium import webdriver
from selenium.webdriver.common.keys import Keys


class MatchViewTestCase(LiveServerTestCase):

    def setUp(self):
        from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
        
        username = os.environ.get('SAUCE_USERNAME')
        password = os.environ.get('SAUCE_ACCESS_KEY')
        if None in (username, password):
            self.selenium = webdriver.Safari()
            self.selenium.implicitly_wait(5)
        else:
            desired_cap = {
                'platform': "Mac OS X 10.9",
                'browserName': "internet explorer", # safari, chrome, firefox, android, iphone
                # 'version': "31",
                'tunnel-identifier': os.environ.get['TRAVIS_JOB_NUMBER'],
                'build': os.environ["TRAVIS_BUILD_NUMBER"],
                'tags': [os.environ["TRAVIS_PYTHON_VERSION"], "CI"],
            }
            driver = webdriver.Remote(
               command_executor='http://' + username + ':' + password + '@ondemand.saucelabs.com:80/wd/hub',
               desired_capabilities=desired_cap)

        super().setUp()
    
    
    def tearDown(self):
        self.selenium.quit()
        super().tearDown()
    
    
    def test_manual_match(self):
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
        
#         # Fill the form with data
#         first_name.send_keys('Yusuf')
#         last_name.send_keys('Unary')
#         username.send_keys('unary')
#         email.send_keys('yusuf@qawba.com')
#         password1.send_keys('123456')
#         password2.send_keys('123456')
#
#         #submitting the form
#         submit.send_keys(Keys.RETURN)
#
#         #check the returned result
#         assert 'Check your email' in selenium.page_source