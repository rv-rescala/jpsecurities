import requests
from selenium import webdriver
from bs4 import BeautifulSoup
from enum import Enum


class RequestType(Enum):
    post = "post"
    get = "get"


def webdriver_to_request(driver: webdriver):
    """

    :param driver:
    :return:
    """
    session = requests.session()
    for cookie in driver.get_cookies():
        session.cookies.set(cookie["name"], cookie["value"])
    return session


def download(request: requests, url: str, path: str, request_type: RequestType = RequestType.get, post_data=None):
    """

    :param request:
    :param url:
    :param path:
    :param request_type:
    :param post_data:
    :return:
    """
    if request_type is RequestType.post:
        bi = request.post(url, post_data).content
    else:
        bi = request.get(url).content
    with open(path, "wb") as f:
        f.write(bi)
    return path
