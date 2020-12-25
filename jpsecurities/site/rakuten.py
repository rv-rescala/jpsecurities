from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import logging
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import time

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
        return self

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

    def home(self, default_wait: int = 10):
        home = "pcm-g-header__inner-01"

        WebDriverWait(self.driver, default_wait).until(lambda x: x.find_element_by_class_name(home))
        self.driver.find_element_by_class_name(home).click()  # ヘッダの楽天証券ロゴをクリック
        WebDriverWait(self.driver, default_wait).until(lambda x: x.find_element_by_class_name(home))

    def asset_info(self, default_wait: int = 10):
        # parse home page and get content
        self.home()
        asset_total_top = "asset_total_top"  # div id
        WebDriverWait(self.driver, default_wait).until(lambda x: x.find_element_by_id(asset_total_top))
        #html = self.driver.page_source.encode('utf-8')
        soup = BeautifulSoup(self.driver.page_source, "lxml")
        home_asset_info = soup.find("div", {"id": asset_total_top})
        print(home_asset_info)
