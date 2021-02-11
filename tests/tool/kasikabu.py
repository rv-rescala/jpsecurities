import unittest
from jpsecurities.util.kasikabu import Kashikabu
from selenium.webdriver.chrome.options import Options
import time
import logging
import sys
import os
from logging import Formatter, handlers, StreamHandler, getLogger, DEBUG
import pandas as pd

logging.getLogger().setLevel(DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


class TestKashikabu(unittest.TestCase):
    chrome_options = Options()
    chrome_options.binary_location = os.environ['CHROME_BIN_LOCATION']
    chrome_options.headless = True
    executable_path = os.environ['CHROME_EXE_PATH']
    username = os.environ['RAKUTEN_USERNAME']
    pwd = os.environ['RAKUTEN_PWD']

    def test_all_list(self):
        kashikabu = Kashikabu(executable_path=self.executable_path, chrome_options=self.chrome_options)
        df = kashikabu.get_all_list()
        print(df)

if __name__ == "__main__":
    unittest.main()
