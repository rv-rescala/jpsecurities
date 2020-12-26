from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import logging
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
import time

logger = logging.getLogger()


class RakutenException(Exception):
    pass


class Rakuten:
    def __init__(self, executable_path: str, chrome_options: Options, username: str, pwd: str,
                 implicitly_wait: int = 10):
        """

        :param executable_path:
        :param chrome_options:
        :return:
        """
        self.executable_path = executable_path
        self.chrome_options = chrome_options
        self.implicitly_wait = implicitly_wait
        self.username = username
        self.pwd = pwd

    def __enter__(self):
        caps = DesiredCapabilities.CHROME
        caps['loggingPrefs'] = {'performance': 'INFO'}
        self.driver: webdriver = webdriver.Chrome(executable_path=self.executable_path,
                                                  chrome_options=self.chrome_options,
                                                  desired_capabilities=caps)
        self.driver.implicitly_wait(self.implicitly_wait)
        logger.info("Rakuten Start")
        self.login()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()
        logger.info("Rakuten End")

    def login(self):
        url = "https://www.rakuten-sec.co.jp/web/login_error.html"
        logger.info(f"Access to {url}.")
        self.driver.get(url=url)
        self.driver.find_element_by_name("loginid").send_keys(self.username)
        self.driver.find_element_by_name("passwd").send_keys(self.pwd)
        self.driver.find_element_by_name("submit%template").click()  # login

        cur_url = self.driver.current_url
        if cur_url == url:  # login failed
            logger.error(f"Rakuten login is failed.")
            raise RakutenException("Login is failed.")
        else:  # login success
            logger.info(f"Rakuten login is success.")
            return True

    def home(self, default_wait: int = 10):
        home = "pcm-g-header__inner-01"

        WebDriverWait(self.driver, default_wait).until(lambda x: x.find_element_by_class_name(home))
        self.driver.find_element_by_class_name(home).click()  # ヘッダの楽天証券ロゴをクリック
        WebDriverWait(self.driver, default_wait).until(lambda x: x.find_element_by_class_name(home))

    def asset_info(self, default_wait: int = 10):
        # parse home page and get content
        self.home()
        WebDriverWait(self.driver, default_wait).until(lambda x: x.find_element_by_class_name("pcm-content"))
        soup = BeautifulSoup(self.driver.page_source, "lxml")

        # daily収益
        balance_data_actual_data = soup.find("div", {"id": "balance_data_actual_data"}).findAll("tr")
        nobr = list(map(lambda x: x.text.replace(",","").replace(" 円", ""), filter(None, map(lambda x: x.find("nobr"), balance_data_actual_data))))
        """
        国内株式
        米国株式
        中国株式
        アセアン株式
        債券
        投資信託
        外貨建MMF
        預り金
        売建予想配当金
        信用取引保証金
        国内先物OP取引証拠金
        外貨預り金合計
        信用建玉評価損益
        """
        daily_revenue = {
            "Domestic": nobr[0],
            "US": nobr[1],
            "China": nobr[2],
            "ASEAN": nobr[3],
            "Bonds": nobr[4],
            "InvestmentTrusts": nobr[5],
            "ForeignCurrencyMMFs": nobr[6],
            "Deposits": nobr[7],
            "ExpectedDividendsOnSales": nobr[8],
            "MarginTransactionGuaranteeMoney": nobr[9],
            "DomesticFuturesOpTradingMargins": nobr[10],
            "TotalForeignCurrencyDeposits": nobr[11],
            "UnrealizedGainsLossesOnMarginTransaction": nobr[12]
        }
        print(daily_revenue)
