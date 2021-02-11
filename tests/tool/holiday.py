import unittest
from jpsecurities.util.holiday import today_is_holiday, CountryType
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
    def test_is_holiday_today(self):
        print(today_is_holiday(country_type=CountryType.japan))

if __name__ == "__main__":
    unittest.main()
