import logging
from bs4 import BeautifulSoup
import requests
import pandas as pd
import sys
from datetime import datetime, timedelta, timezone, date

logger = logging.getLogger()

class GMOException(Exception):
    pass

class GMO:

    @classmethod
    def kashikabu_rate(cls, continuous: bool = False, default_wait: int = 10) -> pd.DataFrame:
        """
        """
        # request
        url = "https://www.click-sec.com/corp/guide/kabu/stock_lending/ratelist/"
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'lxml')

        # parse
        table = soup.find('table', id="search")
        lending_adapte_dates = list(map(lambda x: x.text, table.find("thead").find_all("th")[-2:]))
        logger.debug("parse finish.")

        # 期間の処理
        prev_date_from_to = lending_adapte_dates[0].split("～")
        prev_date_from = prev_date_from_to[0]
        prev_date_to = prev_date_from_to[1]
        next_date_from_to = lending_adapte_dates[1].split("～")
        next_date_from = next_date_from_to[0]
        next_date_to = next_date_from_to[1]
        companies = table.find("tbody").find_all("tr")

        results = list()
        JST = timezone(timedelta(hours=+9), 'JST')
        today = datetime.now(JST).date()

        for company in companies:
            code = company.find('div', class_="td-01-inner").text
            name = company.find('td', class_="search-col td-02").text
            prev_lending_rate = company.find(
                'td', class_="td-03").text.split("%")[0]
            next_lending_rate = company.find(
                'td', class_="td-04").text.split("%")[0]

            def __to_date(s):
                _month = s.split("/")[0]
                _date = s.split("/")[1]
                return date(today.year, int(_month), int(_date))

            r = {
                "stock_code": int(code),
                "interest_rate": float(prev_lending_rate) * 0.01,
                "from_date":  __to_date(str(prev_date_from)),
                "to_date": __to_date(str(prev_date_to)),
                "next_interest_rate": float(next_lending_rate) * 0.01,
                "next_from_date": __to_date(str(next_date_from)),
                "next_to_date": __to_date(str(next_date_to))
            }
            if r["to_date"] < r["from_date"]:
                # TBD: 年跨ぎの処理
                raise GMOException(f'from to date is illegal,{r["to_date"]}, {r["from_date"]}')
            results.append(r)
            df = pd.DataFrame(results)
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
                # format date => fillを行うとdatetimeがobject型に変換される
                #print(df_continuous.dtypes)
                _date_format = '%Y%m%d'
                df_continuous["from_date"] = df_continuous["from_date"].dt.strftime(_date_format)
                df_continuous["to_date"] = df_continuous["to_date"].astype(str).str.replace("-", "")
                df_continuous["next_from_date"] = df_continuous["next_from_date"].astype(str).str.replace("-", "")
                df_continuous["next_to_date"] = df_continuous["next_to_date"].astype(str).str.replace("-", "")
                # 今回、次回貸株金利を反映
                df_current = df_continuous.query('from_date <= to_date').copy()
                df_current["target_date"] = df_current["from_date"]
                df_next = df_continuous.query('from_date > to_date').copy()
                df_next["target_date"] = df_next["from_date"]
                df_next["interest_rate"] = df_next["next_interest_rate"]
                _r_df = pd.concat([df_current, df_next])
                if count > 0:
                    r_df = pd.concat([r_df, _r_df])
                else:
                    r_df = _r_df
                count = count + 1
        else:
            r_df = df
        return r_df
