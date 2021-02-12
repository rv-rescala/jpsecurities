from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.desired_capabilities import DesiredCapabilities
import logging
from selenium.webdriver.support.ui import WebDriverWait
from bs4 import BeautifulSoup
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from jpsecurities.util.request import *
import pandas as pd

logger = logging.getLogger()
from selenium.webdriver.support import expected_conditions

class SBIException(Exception):
    pass


class SBI:
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
        url = "https://site3.sbisec.co.jp/ETGate/"
        self.driver.get(url)
        wait = WebDriverWait(self.driver, self.implicitly_wait)
        wait.until(expected_conditions.element_to_be_clickable((By.ID, "user_input")))
        logger.info("SBIWebDriver.login: 1st wait_rendering finish")
        self.driver.find_element_by_name("user_id").send_keys(self.username)
        self.driver.find_element_by_name("user_password").send_keys(self.pwd)
        self.driver.find_element_by_name("ACT_login").click()  # ACT_login click
        wait.until(EC.presence_of_element_located((By.ID, "scsbaccnt-cfd_unopen")))
        logger.info("SBIWebDriver.login: login finish")
        return True

    def kashikabu_rate(self, default_wait: int = 10, tmp_path: str = "/tmp") -> pd.DataFrame:
        """

        :param default_wait:
        :param tmp_path:
        :return:
        """
        # 貸株遷移用ページ
        wait = WebDriverWait(self.driver, default_wait)
        kashikabu_init_page_url = "https://site3.sbisec.co.jp/ETGate/?OutSide=on&_ControlID=WPLETmgR001Control&_PageID=WPLETmgR001Mdtl20&_DataStoreID=DSWPLETmgR001Control&_ActionID=DefaultAID&getFlg=on&burl=search_domestic&cat1=domestic&cat2=stocklending&dir=stocklending&file=domestic_stocklending.html"
        self.driver.get(kashikabu_init_page_url)
        wait.until(EC.presence_of_element_located((By.ID, "scsbaccnt-cfd_unopen")))
        # 貸株ページ
        kashikabu_page_url = "https://site3.sbisec.co.jp/ETGate/?OutSide=on&_ControlID=WPLETsmR001Control&_DataStoreID=DSWPLETsmR001Control&_PageID=WPLETsmR001Sdtl12&_ActionID=NoActionID&sw_page=LndStk&cat1=home&cat2=none&sw_param1=&sw_param2=lndstk_ratelist&getFlg=on"
        self.driver.get(kashikabu_page_url)
        wait.until(EC.presence_of_element_located((By.ID, "footer01P")))
        # 貸株CSVページからcsvをダウンロード
        kashikabu_csv_url = "https://site0.sbisec.co.jp/marble/account/japan/ratelist/csv.do"
        request_session = webdriver_to_request(self.driver)
        post_data = {
            'init': 'false',
            'inqType': '2',
            'searchStrings': '',
            'interestSearchType': '0',
            'productCodeSearchType': '',
            'attribute': 'lriCouponRate',
            'direction': '2',
            'page': '0',
            'dispRow': '50'
        }
        download_path = f"{tmp_path}/sbi_kashikabu_rate.csv"
        download(request=request_session, url=kashikabu_csv_url, path=download_path, request_type=RequestType.post, post_data=post_data)
        df = pd.read_csv(download_path, encoding="SHIFT-JIS", skiprows=3)
        # 適用日	銘柄コード	銘柄名	適用金利（年）	非対象期間	事由
        columns = df.columns
        df = df.rename(columns={columns[0]: 'target_date'})
        df = df.rename(columns={columns[1]: 'stock_code'})
        df = df.rename(columns={columns[2]: 'stock_name'})
        df = df.rename(columns={columns[3]: 'interest_rate'})
        df = df.rename(columns={columns[4]: 'non_target_duration'})
        df = df.rename(columns={columns[5]: 'description'})
        return df