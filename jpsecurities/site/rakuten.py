from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import logging
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from enum import Enum
from selenium.webdriver.common.by import By
from jpsecurities.util.selenium import click_link_by_href, download
import csv
import pandas as pd
import re
logger = logging.getLogger()
from datetime import datetime, timedelta, timezone


class GlobalMenu(Enum):
    DOMESTIC_STOCK = "国内株式"
    KASHIKABU = "貸株"
    LIST_OF_SPOT = "保有商品一覧"
    LIST_OF_MARGIN = "信用建玉一覧"


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
        if (menu is GlobalMenu.DOMESTIC_STOCK) or (menu is GlobalMenu.KASHIKABU) or (menu is GlobalMenu.LIST_OF_SPOT) or (menu is GlobalMenu.LIST_OF_MARGIN):
            # 国内株式メニュー
            wait.until(EC.presence_of_element_located((By.LINK_TEXT, "国内株式"))).click()
            if menu is GlobalMenu.DOMESTIC_STOCK:
                result = BeautifulSoup(self.driver.page_source, "lxml")
            else:
                wait.until(EC.presence_of_element_located((By.LINK_TEXT, menu.value))).click()
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

    def kashikabu_accounting_details(self, default_wait: int = 10) -> pd.DataFrame:
        """
        アカウントに紐づく楽天証券の金利・配当金相当額 計上明細を取得
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
        df = pd.DataFrame(kashikabu_accounting_details)
        return df

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

    def kashikabu_rate(self, continuous: bool = False, default_wait: int = 10) -> pd.DataFrame:
        """

        :param continuous:
        :param default_wait:
        :return:
        """
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
            #df_from = df.assign(date=formated_from_date)
            #df_to = df.assign(date=formated_to_date)
            #df = pd.concat([df_from, df_to])
            df["from_date"] = formated_from_date
            df["to_date"] = formated_to_date
            df["next_from_date"] = formated_to_date + timedelta(days=1)
            df["next_to_date"] = formated_to_date + timedelta(days=7)
            df = df.rename(columns={columns[0]: 'stock_code'})
            df = df.rename(columns={columns[1]: 'stock_name'})
            df = df.rename(columns={columns[2]: 'interest_rate'})
            df = df.rename(columns={columns[3]: 'next_interest_rate'})
            df = df.rename(columns={columns[4]: 'trust_interest_rate'})
            df = df.rename(columns={columns[5]: 'next_trust_interest_rate'})
            df = df.rename(columns={columns[6]: 'non_target_period'}) # 非対象期間
            df = df.rename(columns={columns[7]: 'description'}) # 摘要
            df["interest_rate"] = df["interest_rate"].str.replace('%', '').astype(float) * 0.01
            df["next_interest_rate"] = df["next_interest_rate"].str.replace('%', '').astype(float) * 0.01
            df["trust_interest_rate"] = df["trust_interest_rate"].str.replace('%', '').astype(float) * 0.01
            df["next_trust_interest_rate"] = df["next_trust_interest_rate"].str.replace('%', '').astype(float) * 0.01
            logging.info(f"formated_from_date formated_to_date, {formated_from_date} {formated_to_date}")
        else:
            raise RakutenException(f"from_to date is illegal, {from_date}, {to_date}")
        # 日付データの連続化処理
        # Enhance: より効率的な値の連続化
        if continuous:
            # コード一覧を取得
            codes = df["stock_code"].unique()
            r_df = None
            count = 0
            for code in codes:
                df_code = df[df["stock_code"] == code]
                # 連続化の処理
                r = pd.date_range(start=df_code.from_date.min(), end=df_code.next_to_date.max())
                df_continuous = df_code.set_index('from_date').reindex(r).fillna(method='ffill').rename_axis('from_date').reset_index()
                # 今回、次回貸株金利を反映
                df_current = df_continuous.query('from_date < to_date').copy()
                df_current["target_date"] = df_current["from_date"]
                df_next = df_continuous.query('from_date >= to_date').copy()
                df_next["target_date"] = df_next["from_date"]
                df_next["interest_rate"] = df_next["next_interest_rate"]
                df_next["trust_interest_rate"] = df_next["next_trust_interest_rate"]
                if count > 0:
                    r_df = pd.concat([r_df, df_current, df_next])
                else:
                    r_df = pd.concat([df_current, df_next])
                count = count + 1
        else:
            r_df = df
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

    def get_spot_transaction_info(self, default_wait: int = 10) -> pd.DataFrame:
        """

        :param default_wait:
        :return:
        """
        wait = WebDriverWait(self.driver, default_wait)
        self.transition_global_menu(GlobalMenu.LIST_OF_SPOT, default_wait)

        WebDriverWait(self.driver, default_wait).until(lambda x: x.find_element_by_id("poss-tbl-sp"))
        soup = BeautifulSoup(self.driver.page_source, "lxml")
        sp = soup.find("table", {"id": "poss-tbl-sp"}).findAll("tr", {"align": "right"})

        def __parse(x):
            stock_code = x.findAll("td", {"class": "align-L valign-M"})[0].text.replace("\n", "")
            company_name = x.findAll("td", {"class": "align-L valign-M"})[1].text.replace("\n", "")
            stock_quantity = x.find("a", {"id": "stock_detail_link"}).text.replace("\n", "").replace("\t", "")
            # 平均取得価額
            average_acquisition_price = x.findAll("td", {"class": "valign-M align-R"})[1].text.split("\n")[2]
            # 取得総額
            total_acquisition_amount = x.findAll("td", {"class": "valign-M align-R"})[1].text.split("\n")[3]
            # 現在値
            _p = list(filter(lambda y: y != "", x.find("td", {"class": "cell-05 valign-M align-R"}).text.replace("\n", "").split("\t")))
            present_value = _p[0]
            # 前日比
            day_before_ratio = _p[1]
            # 時価評価額
            _p = list(filter(lambda y: y != "",
                             x.findAll("td", {"class": "valign-M align-R"})[2].text.replace("\n", "").split("\t")))
            market_value = _p[0]
            stock_gain_loss = _p[1]
            #wait.until(EC.presence_of_element_located((By.LINK_TEXT, "詳細"))).click()
            #self.driver.back()
            return {"stock_code": stock_code, "spot_company_name": company_name, "spot_quantity": stock_quantity,
                    "spot_average_acquisition_price": average_acquisition_price,
                    "spot_total_acquisition_amount": total_acquisition_amount,
                    "spot_present_value": present_value, "spot_day_before_ratio": day_before_ratio,
                    "spot_market_value": market_value, "spot_gain_loss": stock_gain_loss}
        d = list(map(lambda x: __parse(x), sp))
        df = pd.DataFrame(d)
        df["spot_quantity"] = df["spot_quantity"].str.replace(' 株', '').str.replace(',', '').astype(float)
        df["spot_average_acquisition_price"] = df["spot_average_acquisition_price"].str.replace(' 円', '').str.replace(
            ',', '').astype(float)
        df["spot_total_acquisition_amount"] = df["spot_total_acquisition_amount"].str.replace(',', '').str.replace(' 円',
                                                                                                                   '').astype(
            float)
        df["spot_present_value"] = df["spot_present_value"].str.replace(' 円', '').str.replace(',', '').astype(float)
        df["spot_day_before_ratio"] = df["spot_day_before_ratio"].str.replace(' 円', '').str.replace(',', '').astype(
            float)
        df["spot_market_value"] = df["spot_market_value"].str.replace(' 円', '').str.replace(',', '').astype(float)
        df["spot_gain_loss"] = df["spot_gain_loss"].str.replace(' 円', '').str.replace(',', '').astype(float)
        return df

    def get_margin_transaction_info(self, default_wait: int = 10) -> pd.DataFrame:
        """

        :param default_wait:
        :return:
        """
        wait = WebDriverWait(self.driver, default_wait)
        self.transition_global_menu(GlobalMenu.LIST_OF_MARGIN, default_wait)
        wait.until(EC.presence_of_element_located((By.LINK_TEXT, "銘柄別合計"))).click()

        soup = BeautifulSoup(self.driver.page_source, "lxml")
        sp = list(map(lambda x: x.text.replace("\t","").split("\n"), soup.find("table", {"class": "ta1"}).findAll("tr")))
        sp = list(map(lambda x: list(filter(lambda y: y != "", x)), sp))

        def __perse(s):
            company_name = s[2]
            stock_code = s[3].split("\xa0")[0]
            buy_or_sell = s[4]
            margin_type = s[5]
            stock_quantity = s[7]
            stock_gain_loss = s[10]
            return {"margin_company_name": company_name, "stock_code": stock_code, "margin_buy_or_sell": buy_or_sell,
                    "margin_type": margin_type, "margin_quantity": stock_quantity, "margin_gain_loss": stock_gain_loss}
        d = list(map(lambda x: __perse(x), sp[1:]))
        df = pd.DataFrame(d)
        df["margin_quantity"] = df["margin_quantity"].str.replace(' 円', '').str.replace(',', '').astype(float)
        df["margin_gain_loss"] = df["margin_gain_loss"].str.replace(' 円', '').str.replace(',', '').astype(float)
        return df

    def get_spot_margin_transaction_info(self, default_wait: int = 10) -> pd.DataFrame:
        df_spot = self.get_spot_transaction_info(default_wait=default_wait)
        df_margin = self.get_margin_transaction_info(default_wait=default_wait)
        df = pd.merge(df_spot, df_margin, on='stock_code', how='outer')
        return df