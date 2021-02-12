from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import logging
from bs4 import BeautifulSoup
from jpsecurities.util.selenium import download
from jpsecurities.util.request import download
import requests
import pandas as pd


logger = logging.getLogger()


class TaisyakuException(Exception):
    pass


class Taisyaku:
    def __init__(self, executable_path: str, chrome_options: Options,
                 implicitly_wait: int = 10, proxy=None, verify=True):
        """

        :param executable_path:
        :param chrome_options:
        :param implicitly_wait:
        :param proxy:
        :param verify:
        """
        self.executable_path = executable_path
        self.chrome_options = chrome_options
        self.implicitly_wait = implicitly_wait

        self.request = requests.Session()
        if proxy:
            self.request.proxies.update(proxy)
        self.request.verify = verify

    def __enter__(self):
        caps = DesiredCapabilities.CHROME
        caps['loggingPrefs'] = {'performance': 'INFO'}
        self.driver: webdriver = webdriver.Chrome(executable_path=self.executable_path,
                                                  chrome_options=self.chrome_options,
                                                  desired_capabilities=caps)
        self.driver.implicitly_wait(self.implicitly_wait)
        logger.info(f"{self.__class__.__name__} Start")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.driver.quit()
        logger.info(f"{self.__class__.__name__} End")

    def get_pcsl_and_balance_url(self):
        """
        品貸料率一覧表,銘柄別残高一覧表のダウンロードURLを取得
        :return:
        """
        url = "https://www.taisyaku.jp/"
        self.driver.get(url)
        html = self.driver.page_source.encode('utf-8')
        soup = BeautifulSoup(html, "lxml")
        raw_url = soup.find("div", {"class": "download-inner"}).findAll("a")
        urls = {
            "pcsl": raw_url[0]['href'],
            "balance": raw_url[1]['href']
        }
        return urls

    def get_balance(self, only_tosho: bool = True):
        """
        銘柄別残高一覧を取得
        :return:
        """
        name = "balance"
        url = self.get_pcsl_and_balance_url()[name]
        path = download(request=self.request, url=url, path=f"/tmp/{name}.csv")
        df = pd.read_csv(path, skiprows=4, encoding="SHIFT-JIS")
        if only_tosho:
            df = df.query('市場区分 == "東証およびＰＴＳ"')
        return df

    def get_pcsl(self, only_tosho: bool = True):
        """
        品貸料率一覧を取得
        :return:
        """
        name = "pcsl"
        url = self.get_pcsl_and_balance_url()[name]
        path = download(request=self.request, url=url, path=f"/tmp/{name}.csv")
        df = pd.read_csv(path, skiprows=4, encoding="SHIFT-JIS")
        if only_tosho:
            df = df.query('市場区分 == "東証"')
        return df

    def get_pcsl_balance(self):
        """

        :return:
        """
        df_pcsl = self.get_pcsl()
        df_pcsl["貸借申込日"] = df_pcsl["貸借申込日"].astype(str)
        df_pcsl["決済日"] = df_pcsl["決済日"].astype(str)
        df_pcsl = df_pcsl.drop("市場区分", axis=1)
        df_pcsl = df_pcsl.drop("銘柄名", axis=1)

        df_balance = self.get_balance()
        df_balance["申込日"] = df_balance["申込日"].str.replace('/','')

        df = pd.merge(df_pcsl, df_balance, on='コード', how='outer')
        return df

    def get_other(self):
        """
        貸借銘柄等一覧
        :return:
        """
        url = "https://www.taisyaku.jp/sys-list/data/other.xlsx"
        path = download(request=self.request, url=url, path=f"/tmp/other.xlsx")
        df = pd.read_excel(path, skiprows=5, engine='openpyxl')
        df = df.add_prefix("貸借取引対象銘_")
        df = df.rename(columns={'貸借取引対象銘_コード': 'コード'})
        df = df.rename(columns={'貸借取引対象銘_銘柄名': '銘柄名'})
        return df

    def get_seigenichiran(self):
        """
        注意喚起および申込停止措置等一覧表
        :return:
        """
        url = "https://www.taisyaku.jp/sys-list/data/seigenichiran.xlsx"
        path = download(request=self.request, url=url, path=f"/tmp/seigenichiran.xlsx")
        df = pd.read_excel(path, skiprows=9, engine='openpyxl')
        df = df.rename(columns={'Unnamed: 0': '直近発表'})
        df = df.rename(columns={'Unnamed: 1': 'コード'})
        df = df.rename(columns={'Unnamed: 2': '銘柄名'})
        df = df.rename(columns={'Unnamed: 3': '実施措置'})
        df = df.rename(columns={'Unnamed: 4': '実施内容'})
        df = df.rename(columns={'Unnamed: 5': '備考'})
        df = df.rename(columns={'Unnamed: 6': '通知日'})
        df = df.rename(columns={'Unnamed: 7': '実施'})
        df["通知日"] = df["通知日"].str.replace('月|日|年', '')
        df = df.add_prefix("注意喚起および申込停止措置_")
        df = df.rename(columns={'注意喚起および申込停止措置_コード': 'コード'})
        df = df.rename(columns={'注意喚起および申込停止措置_銘柄名': '銘柄名'})
        return df

    def get_other_seigenichiran(self):
        df_other = self.get_other()
        df_seigenichiran = self.get_seigenichiran()
        df_seigenichiran = df_seigenichiran.drop("銘柄名", axis=1)
        df = pd.merge(df_other, df_seigenichiran, on='コード', how='outer')
        return df

    def get_taisyaku(self, only_taisyaku_enable: bool = True):
        df_pcsl_balance = self.get_pcsl_balance()
        df_other_seigenichiran =self.get_other_seigenichiran()
        df_other_seigenichiran = df_other_seigenichiran.drop("銘柄名", axis=1)
        df = pd.merge(df_pcsl_balance, df_other_seigenichiran, on='コード', how='outer')
        return df
