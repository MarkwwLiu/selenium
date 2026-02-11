"""
參數化測試範例模板

示範如何使用 @pytest.mark.parametrize 進行：
- 正向測試 (positive)：合法輸入，預期成功
- 反向測試 (negative)：非法輸入，預期失敗/錯誤訊息
- 邊界測試 (boundary)：邊界值，驗證臨界行為

使用方式:
    pytest tests/test_example_parametrize.py -v
    pytest tests/test_example_parametrize.py -m positive
    pytest tests/test_example_parametrize.py -m negative
    pytest tests/test_example_parametrize.py -m boundary

注意：這是範例模板，請依實際網站修改 PageObject 和測試資料。
"""

import pytest

from pages.home_page import HomePage


# ============================================================
# 測試資料定義
# ============================================================

# 正向測試資料：(輸入值, 預期結果, 測試說明)
POSITIVE_CASES = [
    pytest.param('優惠商品', True, id='包含關鍵字-優惠商品'),
    pytest.param('2024', True, id='包含年份-2024'),
]

# 反向測試資料：(輸入值, 預期結果, 測試說明)
NEGATIVE_CASES = [
    pytest.param('不存在的關鍵字XYZ', False, id='不存在的關鍵字'),
    pytest.param('', False, id='空字串'),
]

# 邊界測試資料：(輸入值, 預期結果, 測試說明)
BOUNDARY_CASES = [
    pytest.param('【', True, id='特殊字元-左括號'),
    pytest.param('！', True, id='特殊字元-驚嘆號'),
]


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def home_page(driver):
    """建立 HomePage 並開啟首頁。"""
    page = HomePage(driver)
    page.open_home()
    return page


# ============================================================
# 測試案例
# ============================================================

class TestParametrizeExample:
    """參數化測試範例。"""

    @pytest.mark.positive
    @pytest.mark.parametrize('keyword, expected', POSITIVE_CASES)
    def test_title_contains_keyword_positive(self, home_page, keyword, expected):
        """正向測試：標題應包含合法關鍵字。"""
        actual = home_page.get_entry_title_text()
        result = keyword in actual
        assert result == expected, f'預期標題{"包含" if expected else "不包含"}「{keyword}」，實際標題：「{actual}」'

    @pytest.mark.negative
    @pytest.mark.parametrize('keyword, expected', NEGATIVE_CASES)
    def test_title_contains_keyword_negative(self, home_page, keyword, expected):
        """反向測試：標題不應包含非法關鍵字。"""
        actual = home_page.get_entry_title_text()
        result = keyword in actual if keyword else bool(actual.strip())
        assert result == expected, f'預期標題{"包含" if expected else "不包含"}「{keyword}」，實際標題：「{actual}」'

    @pytest.mark.boundary
    @pytest.mark.parametrize('keyword, expected', BOUNDARY_CASES)
    def test_title_contains_keyword_boundary(self, home_page, keyword, expected):
        """邊界測試：標題對特殊字元的處理。"""
        actual = home_page.get_entry_title_text()
        result = keyword in actual
        assert result == expected, f'預期標題{"包含" if expected else "不包含"}「{keyword}」，實際標題：「{actual}」'


# ============================================================
# 進階範例：多參數組合
# ============================================================

# 未來可以這樣用：
#
# FORM_TEST_DATA = [
#     pytest.param('user@mail.com', 'Pass1234', True, '登入成功', id='正向-合法帳密'),
#     pytest.param('user@mail.com', '',         False, '請輸入密碼', id='反向-空密碼'),
#     pytest.param('',              'Pass1234', False, '請輸入帳號', id='反向-空帳號'),
#     pytest.param('a' * 256,       'Pass1234', False, '帳號過長',   id='邊界-帳號256字元'),
#     pytest.param('user@mail.com', 'a' * 1,    False, '密碼過短',   id='邊界-密碼1字元'),
# ]
#
# class TestLoginForm:
#     @pytest.mark.parametrize('email, password, should_pass, expected_msg', FORM_TEST_DATA)
#     def test_login(self, login_page, email, password, should_pass, expected_msg):
#         login_page.input_text(*login_page.EMAIL_INPUT, email)
#         login_page.input_text(*login_page.PASSWORD_INPUT, password)
#         login_page.click(*login_page.SUBMIT_BTN)
#
#         if should_pass:
#             login_page.wait_for_url_contains('/dashboard')
#             assert '/dashboard' in login_page.get_current_url()
#         else:
#             error = login_page.get_element_text(*login_page.ERROR_MSG)
#             assert expected_msg in error
