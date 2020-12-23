from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import logging

logger = logging.getLogger()


class Rakuten:
    def __init__(self, executable_path: str, chrome_options: Options):
        """

        :param executable_path:
        :param chrome_options:
        :return:
        """
        caps = DesiredCapabilities.CHROME
        caps['loggingPrefs'] = {'performance': 'INFO'}
        self.driver: webdriver = webdriver.Chrome(executable_path=executable_path,
                                                  chrome_options=chrome_options,
                                                  desired_capabilities=caps)
        logger.info("Rakuten Start")

    def __del__(self):
        self.driver.quit()
        logger.info("Rakuten End")

    def login(self):
        self.driver.get(url="https://www.rakuten-sec.co.jp/web/login_error.html")
