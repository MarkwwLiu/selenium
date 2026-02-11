"""
Demo 情境測試：Google 搜尋

示範完整的情境模組測試結構：
- 從 JSON 載入測試資料
- 正向 / 反向 / 邊界 分類標記
- 使用 BasePage 核心方法
"""

import os
import pytest

from utils.data_loader import load_test_data
from scenarios.demo_search.pages.search_page import SearchPage

# === 測試資料 ===
DATA_DIR = os.path.join(os.path.dirname(__file__), '..', 'test_data')

POSITIVE_CASES = load_test_data(
    os.path.join(DATA_DIR, 'search.json'),
    fields=['keyword', 'has_result'],
)
# 只保留 positive type
POSITIVE_CASES = [c for c in POSITIVE_CASES if '正向' in (c.id or '')]

NEGATIVE_CASES = load_test_data(
    os.path.join(DATA_DIR, 'search.json'),
    fields=['keyword', 'has_result'],
)
NEGATIVE_CASES = [c for c in NEGATIVE_CASES if '反向' in (c.id or '')]

BOUNDARY_CASES = load_test_data(
    os.path.join(DATA_DIR, 'search.json'),
    fields=['keyword', 'has_result'],
)
BOUNDARY_CASES = [c for c in BOUNDARY_CASES if '邊界' in (c.id or '')]


# === Fixtures ===

@pytest.fixture
def search_page(driver, scenario_url):
    page = SearchPage(driver, url=scenario_url)
    page.open_search()
    return page


# === Tests ===

class TestGoogleSearch:
    """Google 搜尋情境測試。"""

    @pytest.mark.positive
    @pytest.mark.parametrize('keyword, has_result', POSITIVE_CASES)
    def test_search_positive(self, search_page, keyword, has_result):
        """正向測試：合法關鍵字應有搜尋結果。"""
        search_page.search(keyword)
        assert search_page.has_results() == has_result

    @pytest.mark.negative
    @pytest.mark.parametrize('keyword, has_result', NEGATIVE_CASES)
    def test_search_negative(self, search_page, keyword, has_result):
        """反向測試：無意義輸入應無結果或不執行搜尋。"""
        if not keyword:
            # 空字串不應觸發搜尋
            assert search_page.get_title() != ''
            return
        search_page.search(keyword)
        assert search_page.has_results() == has_result

    @pytest.mark.boundary
    @pytest.mark.parametrize('keyword, has_result', BOUNDARY_CASES)
    def test_search_boundary(self, search_page, keyword, has_result):
        """邊界測試：極端輸入的搜尋行為。"""
        search_page.search(keyword)
        assert search_page.has_results() == has_result
