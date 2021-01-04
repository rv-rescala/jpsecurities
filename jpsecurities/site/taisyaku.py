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
from jpsecurities.common.request import download
import requests
from requests import Session
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

        df_balance = self.get_balance()
        df_balance["申込日"] = df_balance["申込日"].str.replace('/','')

        df = pd.merge(df_pcsl, df_balance, on='コード', how='outer')
        return df
