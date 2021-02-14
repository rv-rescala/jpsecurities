import unittest
from jpsecurities.site.gmo import GMO
from selenium.webdriver.chrome.options import Options
import time
import logging
import sys
import os
from logging import Formatter, handlers, StreamHandler, getLogger, DEBUG

logging.getLogger().setLevel(DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


class TestGMO(unittest.TestCase):
    #chrome_options = Options()
    #chrome_options.binary_location = os.environ['CHROME_BIN_LOCATION']
    # chrome_options.headless = True
    #executable_path = os.environ['CHROME_EXE_PATH']
    #username = os.environ['SBI_USERNAME']
    #pwd = os.environ['SBI_PWD']

    def test(self):
        df = GMO.kashikabu_rate(continuous=True)
        print(df)
        df.to_csv('~/Downloads/a.csv')
        # time.sleep(10000)


if __name__ == "__main__":
    unittest.main()
