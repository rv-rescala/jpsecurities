import unittest
from jpsecurities.site.rakuten import Rakuten
from selenium.webdriver.chrome.options import Options
import time


class TestRakuten(unittest.TestCase):
    chrome_options = Options()
    chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
    executable_path = '/usr/local/bin/chromedriver'

    def test_login(self):
        rakuten: Rakuten = Rakuten(executable_path=self.executable_path, chrome_options=self.chrome_options)
        rakuten.login()
        time.sleep(30)


if __name__ == "__main__":
    unittest.main()
