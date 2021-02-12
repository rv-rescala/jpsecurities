import unittest
from jpsecurities.site.sbi import SBI
from selenium.webdriver.chrome.options import Options
import time
import logging
import sys
import os
from logging import Formatter, handlers, StreamHandler, getLogger, DEBUG

logging.getLogger().setLevel(DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


class TestSBI(unittest.TestCase):
    chrome_options = Options()
    chrome_options.binary_location = os.environ['CHROME_BIN_LOCATION']
    # chrome_options.headless = True
    executable_path = os.environ['CHROME_EXE_PATH']
    username = os.environ['SBI_USERNAME']
    pwd = os.environ['SBI_PWD']

    def test(self):
        with SBI(executable_path=self.executable_path, chrome_options=self.chrome_options,
                     username=self.username, pwd=self.pwd) as sbi:
            df = sbi.kashikabu_rate()
            print(df)
            # df.to_csv('~/Downloads/a.csv')
            # time.sleep(10000)


if __name__ == "__main__":
    unittest.main()
