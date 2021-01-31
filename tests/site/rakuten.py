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
            df = rakuten.get_spot_margin_transaction_info()
            df = rakuten.get_spot_margin_transaction_info()
            #df['created_at'] = local_times["created_at"]

            df.loc[df['spot_quantity'] == df['margin_quantity'], 'is_kashikabu_portfolio'] = True
            df.loc[df['spot_quantity'] != df['margin_quantity'], 'is_kashikabu_portfolio'] = False

            df.to_csv('/tmp/get_spot_margin_transaction_info.csv')
            #time.sleep(10000)
            

if __name__ == "__main__":
    unittest.main()
