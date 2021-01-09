import unittest
from jpsecurities.site.taisyaku import Taisyaku
from selenium.webdriver.chrome.options import Options
import time
import logging
import sys
import os
from logging import Formatter, handlers, StreamHandler, getLogger, DEBUG
import pandas as pd

logging.getLogger().setLevel(DEBUG)
logging.getLogger().addHandler(logging.StreamHandler(sys.stdout))


class TestTaisyaku(unittest.TestCase):
    chrome_options = Options()
    chrome_options.binary_location = os.environ['CHROME_BIN_LOCATION']
    executable_path = os.environ['CHROME_EXE_PATH']
    username = os.environ['RAKUTEN_USERNAME']
    pwd = os.environ['RAKUTEN_PWD']

    def test_download_assets(self):
        with Taisyaku(executable_path=self.executable_path, chrome_options=self.chrome_options) as t:
            #df_pcsl = t.get_pcsl()
            #df_balance = t.get_pcsl_and_balance_url()
            #df_pcsl_balance = t.get_pcsl_balance()
            #df_pcsl_balance.to_csv('/tmp/df_pcsl_balance.csv')
            df = t.get_taisyaku()
            df.to_csv('/tmp/taisyaku.csv')
            #t.get_seigenichiran()

if __name__ == "__main__":
    unittest.main()
