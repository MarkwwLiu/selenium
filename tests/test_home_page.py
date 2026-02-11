"""
首頁測試案例

使用 pytest + Page Object Model 對 ShareBoxNow 首頁進行測試。
執行方式: pytest tests/test_home_page.py
"""

import pytest

from pages.home_page import HomePage


@pytest.fixture
def home_page(driver):
    """建立 HomePage 實例並開啟首頁。"""
    page = HomePage(driver)
    page.open_home()
    return page


class TestHomePage:
    """ShareBoxNow 首頁的測試。"""

    @pytest.mark.smoke
    def test_entry_title_is_correct(self, home_page):
        """驗證首頁文章標題是否正確。"""
        expected = '【2024】多種優惠商品資訊，千萬別錯過！'
        actual = home_page.get_entry_title_text()
        assert actual == expected, f'標題不符：預期「{expected}」，實際「{actual}」'

    @pytest.mark.smoke
    def test_entry_title_contains_keyword(self, home_page):
        """驗證首頁文章標題包含關鍵字。"""
        keyword = '優惠商品'
        actual = home_page.get_entry_title_text()
        assert keyword in actual, f'標題未包含關鍵字「{keyword}」'
