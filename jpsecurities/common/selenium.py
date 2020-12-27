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
from selenium.webdriver.support import expected_conditions as EC
from enum import Enum
from selenium.webdriver.common.by import By
from jpsecurities.common.request import webdriver_to_request
from jpsecurities.common.request import download as request_download

logger = logging.getLogger()


def click_link_by_href(driver: webdriver, href_contain: str):
    """

    :param driver:
    :param href_contain:
    :return:
    """
    anchors = driver.find_elements_by_tag_name("a")
    for anchor in anchors:
        link = anchor.get_attribute("href")
        if href_contain in link:
            logger.debug(f"click_link_by_href: {link}")
            anchor.click()
            return link
    return None


def download(driver: webdriver, url: str, path: str, request_type: str = "get", post_data=None):
    """

    :param driver:
    :param url:
    :param path:
    :param request_type:
    :param post_data:
    :return:
    """
    return request_download(webdriver_to_request(driver), url, path, request_type, post_data)



