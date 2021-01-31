import unittest
from jpsecurities.site.kabutan import Kabutan
import time
import logging
import sys
import os
from selenium.webdriver.chrome.options import Options
from logging import Formatter, handlers, StreamHandler, getLogger, DEBUG
import pandas as pd

logging.getLogger().setLevel(DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


class TestKabutan(unittest.TestCase):
    chrome_options = Options()
    chrome_options.binary_location = os.environ['CHROME_BIN_LOCATION']
    chrome_options.headless = True

    def test_get(self):
        with Kabutan() as t:
            r = t.get_stock_info("2438")
            print(r)

if __name__ == "__main__":
    unittest.main()
