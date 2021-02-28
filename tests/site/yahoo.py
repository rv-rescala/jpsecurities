import unittest
from jpsecurities.site.yahoo import Yahoo
from selenium.webdriver.chrome.options import Options
import time
import logging
import sys
import os
from logging import Formatter, handlers, StreamHandler, getLogger, DEBUG
import pandas as pd

logging.getLogger().setLevel(DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


class TestYahoo(unittest.TestCase):
    def test(self):
        print(Yahoo.get_stock_info("2438"))


if __name__ == "__main__":
    unittest.main()