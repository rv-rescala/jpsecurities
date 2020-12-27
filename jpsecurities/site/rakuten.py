from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import logging
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from enum import Enum
from selenium.webdriver.common.by import By
from jpsecurities.common.selenium import click_link_by_href, download
import csv
import urllib.parse

logger = logging.getLogger()


class GlobalMenu(Enum):
    DOMESTIC_STOCK = "国内株式"
    KASIKABU = "貸株"


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

    def get_session_id(self):
        url = self.driver.current_url
        #qs = urllib.parse.urlparse(url).query
        #qs_d = urllib.parse.parse_qs(qs)
        logger.debug(f"get_session_id url: {url}")
        session_id = url.split("=")[1].split("?")[0]
        logger.info(f"get_session_id: {session_id}")
        return session_id

    def transition_global_menu(self, menu: GlobalMenu, default_wait: str = 10) -> BeautifulSoup:
        self.home()
        wait = WebDriverWait(self.driver, default_wait)
        result = None
        # 国内株式
        if (menu is GlobalMenu.DOMESTIC_STOCK) or (menu is GlobalMenu.KASIKABU):
            # 国内株式メニュー
            wait.until(EC.presence_of_element_located((By.LINK_TEXT, "国内株式"))).click()
            if menu is GlobalMenu.DOMESTIC_STOCK:
                result = BeautifulSoup(self.driver.page_source, "lxml")
            # 貸株
            if menu is GlobalMenu.KASIKABU:
                wait.until(EC.presence_of_element_located((By.LINK_TEXT, "貸株"))).click()
                result = BeautifulSoup(self.driver.page_source, "lxml")
        return result

    def download_kashikabu_accounting_details(self, default_wait: int = 10, path: str = "/tmp"):
        """

        :param default_wait:
        :return:
        """
        wait = WebDriverWait(self.driver, default_wait)
        self.transition_global_menu(GlobalMenu.KASIKABU, default_wait)
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "貸株"))).click()
        # 貸株詳細ページ
        kashikabu_detail_url = click_link_by_href(self.driver, "info_jp_sl_detail_list_post")
        logging.info(f"kashikabu_detail_url: {kashikabu_detail_url}")
        # download csv
        session_id = self.get_session_id()
        download_path = f"{path}/kashikabu_accounting_details.csv"
        kashikabu_detail_csv_rul = f"https://member.rakuten-sec.co.jp/app/info_jp_sl_detail_list_post.do;BV_SessionID={session_id}?eventType=csv"
        logging.info(f"kashikabu_detail_csv_rul: {kashikabu_detail_csv_rul}")
        download(driver=self.driver, url=kashikabu_detail_csv_rul, path=download_path)
        return download_path

    def kashikabu_accounting_details(self, default_wait: int = 10):
        """

        :param default_wait:
        :return:
        """
        download_path = self.download_kashikabu_accounting_details(default_wait=default_wait)
        kashikabu_accounting_details = []
        with open(download_path, 'r', encoding='shift_jis') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            for row in csv_reader:
                kashikabu_accounting_details.append({
                    "accounting_date": row[0].replace("/", ""),
                    "service_type": row[1],
                    "stock_code": row[2],
                    "stock_name": row[3],
                    "quantity": row[4],
                    "market_price": row[5],
                    "lending_stock_interest_rate": row[6],
                    "recorded_amount": row[7]
                })
        return kashikabu_accounting_details

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
            "rakuten_domestic_stock": nobr[0],
            "rakuten_us_stock": nobr[1],
            "rakuten_china_stock": nobr[2],
            "rakuten_asean_stock": nobr[3],
            "rakuten_bonds": nobr[4],
            "rakuten_investment_trusts": nobr[5],
            "rakuten_foreign_currency_mmf": nobr[6],
            "rakuten_deposits": nobr[7],
            "rakuten_expected_dividends_on_sales": nobr[8],
            "rakuten_margin_transaction_deposit": nobr[9],
            "rakuten_domestic_futures_op_trading_margin": nobr[10],
            "rakuten_total_foreign_currency_deposits": nobr[11],
            "rakuten_net_credit_interest_evaluation": nobr[12]
        }
        logger.debug(daily_revenue)
        return daily_revenue
