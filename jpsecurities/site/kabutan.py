import logging
from bs4 import BeautifulSoup
import requests
import pandas as pd
import sys

logger = logging.getLogger()


class KabutanException(Exception):
    pass


class Kabutan:
    base_url = "https://kabutan.jp/stock/?code="
           
    def __init__(self, implicitly_wait: int = 10, proxy=None, verify=True):
        self.request = requests.Session()
        if proxy:
            self.request.proxies.update(proxy)
        self.request.verify = verify
        self.implicitly_wait = implicitly_wait

    def __enter__(self):
        logger.info(f"{self.__class__.__name__} Start")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info(f"{self.__class__.__name__} End")

    def get_stock_info(self, code):
        url = f"{self.base_url}{code}"
        logging.info(f"request to {url}")
        ret = self.request.get(url, timeout=self.implicitly_wait)
        soup = BeautifulSoup(ret.content, features="html.parser")
        update_date = soup.find('div', id="kobetsu_left").findAll('time')[1].text.replace("月", "").replace("日", "")
        kobetsu_left = soup.find('div', id="kobetsu_left").findAll('tr')
        r = {"company_code": code,
                               "opening_price": kobetsu_left[0].find("td").text.replace(",", ""),
                               "high_price": kobetsu_left[1].find("td").text.replace(",", ""),
                               "low_price": kobetsu_left[2].find("td").text.replace(",", ""),
                               "closing_price": kobetsu_left[3].find("td").text.replace(",", ""),
                               "trading_volume": kobetsu_left[4].find("td").text.replace("\xa0", "").replace(",", "").replace("株", "").replace("\xa0", ""),
                               "update_date": update_date,
                               "total_trading_price": kobetsu_left[5].find("td").text.replace("\xa0", ""),
                               "vwap": kobetsu_left[6].find("td").text.replace("\xa0", ""),
                               "execution_count": kobetsu_left[7].find("td").text.replace(" ", "").replace("回", "").replace("\xa0", ""),
                               "share_unit_number": kobetsu_left[9].find("td").text.replace(",", "").replace("株", "").replace("\xa0", "")
                               }
        return r
    