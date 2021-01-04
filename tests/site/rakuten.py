import unittest
from jpsecurities.site.rakuten import Rakuten
from selenium.webdriver.chrome.options import Options
import time
import logging
import sys
import os
from logging import Formatter, handlers, StreamHandler, getLogger, DEBUG

logging.getLogger().setLevel(DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


class TestRakuten(unittest.TestCase):
    chrome_options = Options()
    chrome_options.binary_location = os.environ['CHROME_BIN_LOCATION']
    executable_path = os.environ['CHROME_EXE_PATH']
    username = os.environ['RAKUTEN_USERNAME']
    pwd = os.environ['RAKUTEN_PWD']

    def test_asset_info(self):
        with Rakuten(executable_path=self.executable_path, chrome_options=self.chrome_options,
                     username=self.username, pwd=self.pwd) as rakuten:
            rakuten_asset_info = rakuten.asset_info()
            time.sleep(10000)

    def test_kashikabu_accounting_details(self):
        with Rakuten(executable_path=self.executable_path, chrome_options=self.chrome_options,
                     username=self.username, pwd=self.pwd) as rakuten:
            kashikabu_accounting_details = rakuten.kashikabu_accounting_details()
            print(kashikabu_accounting_details)
            time.sleep(10000)
            

if __name__ == "__main__":
    unittest.main()
