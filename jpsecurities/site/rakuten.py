from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import logging

logger = logging.getLogger()


class RakutenException(Exception):
    pass


class Rakuten:
    def __init__(self, executable_path: str, chrome_options: Options, username: str, pwd: str, implicitly_wait: int = 10):
        """

        :param executable_path:
        :param chrome_options:
        :return:
        """
        self.executable_path = executable_path
        self.chrome_options = chrome_options
        self.implicitly_wait = implicitly_wait
        self.username = username
        self.pwd = pwd

    def __enter__(self):
        caps = DesiredCapabilities.CHROME
        caps['loggingPrefs'] = {'performance': 'INFO'}
        self.driver: webdriver = webdriver.Chrome(executable_path=self.executable_path,
                                                  chrome_options=self.chrome_options,
                                                  desired_capabilities=caps)
        self.driver.implicitly_wait(self.implicitly_wait)
        logger.info("Rakuten Start")
        self.login()

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()
        logger.info("Rakuten End")

    def login(self):
        url = "https://www.rakuten-sec.co.jp/web/login_error.html"
        logger.info(f"Access to {url}.")
        self.driver.get(url=url)
        self.driver.find_element_by_name("loginid").send_keys(self.username)
        self.driver.find_element_by_name("passwd").send_keys(self.pwd)
        self.driver.find_element_by_name("submit%template").click()  # login

        cur_url = self.driver.current_url
        if cur_url == url:  # login failed
            logger.error(f"Rakuten login is failed.")
            raise RakutenException("Login is failed.")
        else:  # login success
            logger.info(f"Rakuten login is success.")
            return True
