"""
Page Object Model - ShareBoxNow 首頁

封裝首頁的元素定位與操作方法。
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver

from pages.base_page import BasePage
from config.settings import BASE_URL


class HomePage(BasePage):
    """ShareBoxNow 首頁的 Page Object。"""

    # === 元素定位器 (Locators) ===
    TITLE_LINK = (By.CSS_SELECTOR, '.entry-title-link')

    def __init__(self, driver: WebDriver):
        super().__init__(driver)
        self.url = BASE_URL

    def open_home(self):
        """開啟首頁。"""
        self.open(self.url)
        return self

    def get_entry_title_text(self):
        """取得首頁文章標題的文字。"""
        element = self.wait_for_element(*self.TITLE_LINK)
        return element.text
