"""
Demo Page Object：Google 搜尋頁

示範情境模組中的 Page Object 如何繼承核心 BasePage。
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from pages.base_page import BasePage


class SearchPage(BasePage):
    """Google 搜尋頁面。"""

    # === Locators ===
    SEARCH_INPUT = (By.NAME, 'q')
    SEARCH_RESULTS = (By.CSS_SELECTOR, '#search .g')
    RESULT_TITLES = (By.CSS_SELECTOR, '#search .g h3')

    def __init__(self, driver, url='https://www.google.com'):
        super().__init__(driver)
        self.url = url

    def open_search(self):
        """開啟搜尋首頁。"""
        self.open(self.url)
        return self

    def search(self, keyword):
        """輸入關鍵字並按 Enter 搜尋。"""
        self.input_text(*self.SEARCH_INPUT, keyword)
        self.find_element(*self.SEARCH_INPUT).send_keys(Keys.RETURN)
        return self

    def get_result_titles(self):
        """取得搜尋結果標題列表。"""
        self.wait_for_visible(*self.RESULT_TITLES)
        return self.get_elements_text(*self.RESULT_TITLES)

    def get_result_count(self):
        """取得搜尋結果數量。"""
        return self.get_element_count(*self.SEARCH_RESULTS)

    def has_results(self):
        """是否有搜尋結果。"""
        return self.get_result_count() > 0
