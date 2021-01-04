import requests
from selenium import webdriver
from bs4 import BeautifulSoup


def webdriver_to_request(driver: webdriver):
    """

    :param driver:
    :return:
    """
    session = requests.session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie["name"], cookie["value"])
    return session


def download(request: requests, url: str, path: str, request_type: str = "get", post_data=None):
    """

    :param request:
    :param url:
    :param path:
    :param request_type:
    :param post_data:
    :return:
    """
    if request_type == "post":
        bi = request.post(url=url, post_data=post_data)
    else:
        bi = request.get(url=url).content
    with open(path, "wb") as f:
        f.write(bi)
    return path
