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
import pandas as pd
import urllib.parse
import re

logger = logging.getLogger()
from datetime import datetime, timedelta, timezone


class GlobalMenu(Enum):
    DOMESTIC_STOCK = "国内株式"
    KASHIKABU = "貸株"

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
        """

        :return:
        """
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
        """

        :param exc_type:
        :param exc_val:
        :param exc_tb:
        :return:
        """
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
        """
        ホームに移動
        :param default_wait:
        :return:
        """
        home = "pcm-g-header__inner-01"
        WebDriverWait(self.driver, default_wait).until(lambda x: x.find_element_by_class_name(home))
        self.driver.find_element_by_class_name(home).click()  # ヘッダの楽天証券ロゴをクリック
        WebDriverWait(self.driver, default_wait).until(lambda x: x.find_element_by_class_name(home))

    def get_session_id(self):
        """
        セッションIDを取得
        :return:
        """
        url = self.driver.current_url
        #qs = urllib.parse.urlparse(url).query
        #qs_d = urllib.parse.parse_qs(qs)
        logger.debug(f"get_session_id url: {url}")
        session_id = url.split("=")[1].split("?")[0]
        logger.info(f"get_session_id: {session_id}")
        return session_id

    def transition_global_menu(self, menu: GlobalMenu, default_wait: str = 10) -> BeautifulSoup:
        """
        グローバルメニューの遷移
        :param menu:
        :param default_wait:
        :return:
        """
        self.home()
        wait = WebDriverWait(self.driver, default_wait)
        result = None
        # 国内株式
        if (menu is GlobalMenu.DOMESTIC_STOCK) or (menu is GlobalMenu.KASHIKABU):
            # 国内株式メニュー
            wait.until(EC.presence_of_element_located((By.LINK_TEXT, "国内株式"))).click()
            if menu is GlobalMenu.DOMESTIC_STOCK:
                result = BeautifulSoup(self.driver.page_source, "lxml")
            # 貸株
            if menu is GlobalMenu.KASHIKABU:
                wait.until(EC.presence_of_element_located((By.LINK_TEXT, "貸株"))).click()
                result = BeautifulSoup(self.driver.page_source, "lxml")
        return result

    def download_kashikabu_accounting_details(self, default_wait: int = 10, path: str = "/tmp"):
        """
        楽天証券の金利・配当金相当額 計上明細をダウンロード
        URL: https://member.rakuten-sec.co.jp/app/info_jp_sl_detail_list_post.do
        :param default_wait:
        :return:
        """
        wait = WebDriverWait(self.driver, default_wait)
        self.transition_global_menu(GlobalMenu.KASHIKABU, default_wait)
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "貸株"))).click()
        # 貸株詳細ページのURLを取得
        kashikabu_detail_url = click_link_by_href(self.driver, "info_jp_sl_detail_list_post")
        logging.info(f"kashikabu_detail_url: {kashikabu_detail_url}")
        # download csv
        session_id = self.get_session_id()
        download_path = f"{path}/rakuten_kashikabu_accounting_details.csv"
        kashikabu_detail_csv_rul = f"https://member.rakuten-sec.co.jp/app/info_jp_sl_detail_list_post.do;BV_SessionID={session_id}?eventType=csv"
        logging.debug(f"kashikabu_detail_csv_rul: {kashikabu_detail_csv_rul}")
        download(driver=self.driver, url=kashikabu_detail_csv_rul, path=download_path)
        return download_path

    def kashikabu_accounting_details(self, default_wait: int = 10):
        """
        楽天証券の金利・配当金相当額 計上明細を取得
        :param default_wait:
        :return:
        """
        download_path = self.download_kashikabu_accounting_details(default_wait=default_wait)
        kashikabu_accounting_details = []
        with open(download_path, 'r', encoding='shift_jis') as csvfile:
            csv_reader = csv.reader(csvfile, delimiter=',', quotechar='"')
            next(csv_reader)
            for row in csv_reader:
                kashikabu_accounting_details.append({
                    "accounting_date": row[0].replace("/", ""),
                    "jp_securities": "rakuten",
                    "service_type": row[1],
                    "stock_code": row[2],
                    "stock_name": row[3],
                    "quantity": row[4],
                    "market_price": row[5],
                    "lending_stock_interest_rate": row[6],
                    "recorded_amount": row[7]
                })
        return kashikabu_accounting_details

    def download_kashikabu_rate(self, default_wait: int = 10, path: str = "/tmp"):
        """
        貸株金利一覧をダウンロード
        URL: https://member.rakuten-sec.co.jp/app/info_jp_sl_rate_search_new.do
        :param default_wait:
        :param path:
        :return:
        """
        wait = WebDriverWait(self.driver, default_wait)
        self.transition_global_menu(GlobalMenu.KASHIKABU, default_wait)
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "貸株金利"))).click()
        # download csv
        session_id = self.get_session_id()
        download_path = f"{path}/rakuten_kashikabu_rate.csv"
        url = f"https://member.rakuten-sec.co.jp/app/info_jp_sl_rate_search_new.do;BV_SessionID={session_id}?eventType=csv"
        logging.debug(f"download_kashikabu_rate url : {url}")
        download(driver=self.driver, url=url, path=download_path)
        return download_path

    def kashikabu_rate(self, default_wait: int = 10) -> pd.DataFrame:
        path = self.download_kashikabu_rate()
        df = pd.read_csv(path, encoding="SHIFT-JIS")
        df = df.rename(columns={'銘柄コード': 'コード'})
        logger.info(f"kashikabu_rate df.columns: {df.columns}")
        columns = df.columns

        # 日付のフォーマット処理
        from_date = re.findall("(?<=（).+?(?=）)", columns[2])[0]
        to_date = re.findall("(?<=（).+?(?=\-)", columns[3])[0]
        JST = timezone(timedelta(hours=+9), 'JST')
        today = datetime.now(JST).date()

        logger.info(f"rakuten kashikabu rate, from: {from_date}, to: {to_date}")
        if to_date > from_date:
            formated_from_date = datetime.strptime(f"{today.year}/{from_date}", '%Y/%m/%d')
            formated_to_date = datetime.strptime(f"{today.year}/{to_date}", '%Y/%m/%d') - timedelta(days=1)
            df_from = df.assign(date=formated_from_date)
            df_to = df.assign(date=formated_to_date)
            df = pd.concat([df_from, df_to])
            df = df.rename(columns={columns[2]: '貸株金利'})
            df = df.rename(columns={columns[3]: '貸株金利(予定)'})
            df = df.rename(columns={columns[4]: '信用貸株金利'})
            df = df.rename(columns={columns[5]: '信用貸株金利(予定)'})
            logging.info(f"formated_from_date formated_to_date, {formated_from_date} {formated_to_date}")
        else:
            raise RakutenException(f"from_to date is illegal, {from_date}, {to_date}")
        # 日付データの連続化処理
        # Enhance: より効率的な値の連続化
        codes = df["コード"].unique()
        r_df = None
        count = 0
        for code in codes:
            df_code = df[df["コード"] == code]
            r = pd.date_range(start=df_code.date.min(), end=df_code.date.max())
            df_filled_code = df_code.set_index('date').reindex(r).fillna(method='ffill').rename_axis('date').reset_index()
            if count > 1:
                r_df = pd.concat([r_df, df_filled_code])
            else:
                r_df = df_filled_code
            count = count + 1
        return r_df

    def asset_info(self, default_wait: int = 10):
        """
        楽天証券の保有資産情報を取得
        :param default_wait:
        :return:
        """
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
