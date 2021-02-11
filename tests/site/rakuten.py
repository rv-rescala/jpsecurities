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
    #chrome_options.headless = True
    executable_path = os.environ['CHROME_EXE_PATH']
    username = os.environ['RAKUTEN_USERNAME']
    pwd = os.environ['RAKUTEN_PWD']

    def test(self):
        with Rakuten(executable_path=self.executable_path, chrome_options=self.chrome_options,
                     username=self.username, pwd=self.pwd) as rakuten:
            df = rakuten.kashikabu_rate(continuous = True)
            print(df)
            df.to_csv('~/Downloads/a.csv')
            #time.sleep(10000)
            

if __name__ == "__main__":
    unittest.main()
