from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import logging
import requests

from jpsecurities.site.taisyaku import Taisyaku

logger = logging.getLogger()


class KashikabuException(Exception):
    pass


class Kashikabu:
    def __init__(self, executable_path: str, chrome_options: Options,
                 implicitly_wait: int = 10, proxy=None, verify=True):
        """

        :param executable_path:
        :param chrome_options:
        :param implicitly_wait:
        :param proxy:
        :param verify:
        """
        self.executable_path = executable_path
        self.chrome_options = chrome_options
        self.implicitly_wait = implicitly_wait

        self.request = requests.Session()
        if proxy:
            self.request.proxies.update(proxy)
        self.request.verify = verify

    def get_all_list(self):
        with Taisyaku(executable_path=self.executable_path, chrome_options=self.chrome_options) as t:
            df_taisyaku = t.get_taisyaku()
        print(df_taisyaku)


