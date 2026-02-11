"""
首頁測試案例（含 BeautifulReport 報告產生）

執行後會在 reports/ 目錄下產生 HTML 格式的測試報告。
執行方式: python -m tests.test_home_page_report （從專案根目錄執行）
"""

import sys
import os
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from BeautifulReport import BeautifulReport

from tests.base_test import BaseTest
from pages.home_page import HomePage
from config.settings import REPORTS_DIR, REPORT_FILENAME, REPORT_DESCRIPTION


class TestHomePageReport(BaseTest):
    """ShareBoxNow 首頁的測試（產生 HTML 報告）。"""

    def setUp(self):
        """每個測試方法執行前，開啟首頁。"""
        self.home_page = HomePage(self.driver)
        self.home_page.open_home()

    def test_entry_title_is_correct(self):
        """驗證首頁文章標題是否正確。"""
        expected = '【2024】多種優惠商品資訊，千萬別錯過！'
        actual = self.home_page.get_entry_title_text()
        self.assertEqual(actual, expected, f'標題不符：預期「{expected}」，實際「{actual}」')

    def test_entry_title_contains_keyword(self):
        """驗證首頁文章標題包含關鍵字。"""
        keyword = '優惠商品'
        actual = self.home_page.get_entry_title_text()
        self.assertIn(keyword, actual, f'標題未包含關鍵字「{keyword}」')


if __name__ == '__main__':
    os.makedirs(REPORTS_DIR, exist_ok=True)
    suite = unittest.TestLoader().loadTestsFromTestCase(TestHomePageReport)
    result = BeautifulReport(suite)
    result.report(
        filename=REPORT_FILENAME,
        description=REPORT_DESCRIPTION,
        report_dir=REPORTS_DIR,
    )
    print(f'\n報告已產生: {os.path.join(REPORTS_DIR, REPORT_FILENAME)}.html')
