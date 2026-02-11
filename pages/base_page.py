"""
Page Object Model - 基礎頁面類別

所有頁面物件的父類別，提供共用的瀏覽器操作方法。
"""

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC


class BasePage:
    """所有 Page Object 的基礎類別。"""

    def __init__(self, driver: WebDriver):
        self.driver = driver

    def open(self, url: str):
        """開啟指定的 URL。"""
        self.driver.get(url)

    def find_element(self, by, value):
        """尋找單一元素。"""
        return self.driver.find_element(by, value)

    def wait_for_element(self, by, value, timeout=10):
        """等待元素出現後再回傳。"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def get_element_text(self, by, value):
        """取得指定元素的文字內容。"""
        return self.find_element(by, value).text

    def get_title(self):
        """取得頁面標題 (browser tab title)。"""
        return self.driver.title
