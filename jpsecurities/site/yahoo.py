import requests
from bs4 import BeautifulSoup


class Yahoo:
    @staticmethod
    def get_stock_info(code):
        """[yahooファイナンスから株式の情報を取得]

        :param code:
        :return:
        """
        base_url = "http://stocks.finance.yahoo.co.jp/stocks/detail/"
        query = {}
        query["code"] = str(code) + ".T"
        ret = requests.get(base_url, params=query)
        soup = BeautifulSoup(ret.content)
        stocktable = soup.find('table', {'class': 'stocksTable'})
        lineFiclearfix = [list(filter(lambda x: x, s.text.split("\n"))) for s in soup.findAll('div', {'class': 'lineFi clearfix'})]
        lineFiyjMSclearfix = [list(filter(lambda x: x, s.text.split("\n"))) for s in soup.findAll('div', {'class': 'lineFi yjMS clearfix'})]
        lineFiclearfix.extend(lineFiyjMSclearfix)
        r = list(map(lambda x: {x[1]: x[0].replace("\xa0", "")}, lineFiclearfix))

        symbol = stocktable.findAll('th', {'class': 'symbol'})[0].text
        stockprice = stocktable.findAll('td', {'class': 'stoksPrice'})[1].text
        r["stock_code"] = code
        r["stock_name"] = symbol
        r["stock_price"] = stockprice
        return r