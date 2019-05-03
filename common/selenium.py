import os
import socket

from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.utils.decorators import classproperty

from selenium import webdriver
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
from selenium.common.exceptions import WebDriverException



class Env():
    
    def __init__(self, include=None, exclude=None):
        
        # Runnig on Travis CI or local?
        self.in_travis = os.environ.get('TRAVIS_JOB_NUMBER') is not None
        
        self._setup_provider()
        
        if self.provider['host'] == 'local':
            browsers = [
                {'browserName': 'Safari'},
                {'browserName': 'Chrome'},
                ]
        else:
            browsers = [
                # {'browserName': "internet explorer", 'version': "8"}, # Renders wrong
                # {'browserName': "internet explorer", 'version': "9"}, # Renders wrong
                # {'browserName': "internet explorer", 'version': "10"}, # Renders wrong
                {'browserName': "internet explorer", 'version': "11"},
            
                {'browserName': 'MicrosoftEdge'},
            
                {'browserName': 'Chrome'}, # Drag works.
                # {'browserName': 'Chrome', 'version', 49} # Last version for Windows XP
                {'browserName': 'Chrome', 'version': 38}, # BrowserStack support
            
                {'browserName': 'Firefox'},
            
                # {'browserName': "Safari", 'version': "7"}, # Renders wrong
                # {'browserName': "Safari", 'version': "8"}, # Fails to connect
                # {'browserName': "Safari", 'version': "9"}, # Fails to connect
                {'browserName': "Safari", 'version':"12"},
                ] ;
        if include is not None:
            if isinstance(include, str):
                include = (include,)
            browsers = [x for x in browsers if x['browserName'] in include]
        if exclude is not None:
            if isinstance(exclude, str):
                exclude = (exclude,)
            browsers = [x for x in browsers if x['browserName'] not in exclude]
        self.browsers = browsers
    
    
    def _setup_provider(self):
    
        get_envs = lambda *names: [os.environ.get(x) for x in names]
        
        host = 'local'
        url = ''
        extra_caps = {}
    
        # Configure for SauceLabs
        params = get_envs('SAUCE_USERNAME', 'SAUCE_ACCESS_KEY')
        if None not in params:
            (username, password) = params
            host = 'saucelabs'
            url = 'http://' + username + ':' + password + '@ondemand.saucelabs.com:80/wd/hub'
        
            if self.in_travis:
                extra_caps['tunnel-identifier'] = os.environ.get('TRAVIS_JOB_NUMBER')
                extra_cap['build'] = os.environ.get("TRAVIS_BUILD_NUMBER")
                extra_cap['tags'] =[os.environ.get("TRAVIS_PYTHON_VERSION"), "CI"]
    
        # Configure for BrowserStack
        params = get_envs('BROWSERSTACK_USER', 'BROWSERSTACK_ACCESS_KEY')
        if None not in params:
            (username, password) = params
            host = 'browserstack'
            url = 'http://' + username + ':' + password + "@hub-cloud.browserstack.com/wd/hub"
            
            extra_caps['browserstack.local'] = 'true'
            local_id = os.environ.get('BROWSERSTACK_LOCAL_IDENTIFIER')
            if local_id:
                extra_caps['browserstack.localIdentifier'] = os.environ.get('BROWSERSTACK_LOCAL_IDENTIFIER')
            
            if self.in_travis:
                extra_caps['name'] = "build " + os.environ.get("TRAVIS_BUILD_NUMBER") + ". "
            else:
                extra_caps['name'] = ''
            
            # extra_caps['browserstack.debug'] = 'true'
    
        # Export settings
        self.provider = {}
        self.provider['host'] = host
        self.provider['extra_caps'] = extra_caps
        self.provider['url'] = url
    
    
    def cases(self):
        
        class Browser:
            def __init__(self, env, browser_i):
                self.env = env
                self.browser_i = browser_i
            
            
            @property
            def browser_caps(self):
                return self.env.browsers[self.browser_i]
            
            
            def build_driver(self, desc=""):
                
                if self.env.provider['host'] == 'local':
                    if self.browser_caps['browserName'] == 'Safari':
                        selenium = webdriver.Safari()
                    elif self.browser_caps['browserName'] == 'Chrome':
                        selenium = webdriver.Chrome()
                    else:
                        raise ValueError("Unsupported local webdriver {}".format(self.provider['host']))
                else:
                    caps = {**self.env.provider['extra_caps'], **self.browser_caps}
                    
                    if self.env.provider['host'] == 'browserstack':
                        caps['name'] = caps['name'] + desc
                    
                    selenium = webdriver.Remote(command_executor=self.env.provider['url'], desired_capabilities=caps)
                
                return selenium
        
        return [Browser(self, ii) for ii in range(len(self.browsers))]
    
    
    def parameterized_class(self):
        return [{'browser': x} for x in self.cases()]


class SeleniumTestCaseHelper(StaticLiveServerTestCase):
    
    host = socket.gethostbyname(socket.gethostname()) # It can be necessary to set this to the local IP address for some Safari configurations
    
    def setUp(self):
        super().setUp()
        
        self.selenium = self.browser.build_driver(self.id())
        self.selenium.implicitly_wait(5)
    
    
    def tearDown(self):
        self.selenium.quit()
    
    
    def run_as_sub_tests(self, sub_tests):
        
        for st in sub_tests:
            with self.subTest(st):
                st()
            
            # Close all but first window
            windows = self.selenium.window_handles
            for w in windows[:0:-1]:
                self.selenium.switch_to_window(w)
                self.selenium.close()
            self.selenium.switch_to_window(self.selenium.window_handles[0])
    
    
    def shortDescription(self):
        desc = super().shortDescription()
        browser_name = "Browser case " + str(self.browser.browser_caps)
        return desc + " " + browser_name if desc else browser_name
    
    
    def wait_for_safari_load(self):
        
        class SafariWaiter:
            def __init__(self, selenium):
                self.selenium = selenium
            
            def __enter__(self):
                self.old_url = self.selenium.current_url
            
            def __exit__(self, *args):
                if self.selenium.capabilities['browserName'] != 'Safari':
                    # Only Safari has this problem
                    return
        
                from selenium.webdriver.support.ui import WebDriverWait
                from selenium.webdriver.support import expected_conditions as EC
        
                # wait for URL to change with 15 seconds timeout
                WebDriverWait(self.selenium, 5).until(EC.url_changes(self.old_url))
        
        return SafariWaiter(self.selenium)
    
    
    def assert_selenium_logs(self):
        try:
            errors = self.selenium.get_log('browser')
        except (ValueError, WebDriverException) as e:
            # Some browsers do not support getting logs
            if self.selenium.capabilities['browserName'] in ('Safari', 'internet explorer', 'MicrosoftEdge', 'firefox'):
                # They don't support logs
                # print("Could not get browser logs for driver {} due to exception: {}".format(self.selenium, e))
                return
            else:
                raise(e)
    
        errors = [x for x in errors if x['level'] == 'SEVERE']
    
        self.assertFalse(errors, 'Console errors detected.')
