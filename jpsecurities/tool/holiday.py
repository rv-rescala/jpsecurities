import logging
from bs4 import BeautifulSoup
import requests
import pandas as pd
import sys
from enum import Enum

logger = logging.getLogger()

class CountryType(Enum):
    japan = "japan"


def today_is_holiday(country_type: CountryType):
    if country_type is CountryType.japan:
        url = "http://s-proj.com/utils/checkHoliday.php?kind=h&opt=market"
        r = requests.get(url)
        if r.content == b'else':
            return False
        else:
            return True