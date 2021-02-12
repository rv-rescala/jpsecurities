from selenium import webdriver
import logging
from jpsecurities.util.request import webdriver_to_request
from jpsecurities.util.request import download as request_download

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



