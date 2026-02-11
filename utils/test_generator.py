"""
測試案例自動產生器

根據 PageAnalyzer 的分析結果，自動推測正向/反向/邊界測試資料，
產生 JSON 測試檔案和 pytest 測試骨架。
"""

import json
import os
import re
from datetime import datetime


# === 根據 input type 推測測試值 ===

VALUE_GENERATORS = {
    'text': {
        'positive': ['Hello World', '測試文字'],
        'negative': ['', ' '],
        'boundary': ['a', 'a' * 255],
    },
    'email': {
        'positive': ['user@example.com', 'test.user+tag@mail.co.jp'],
        'negative': ['', 'not-an-email', '@no-local.com', 'no-domain@'],
        'boundary': ['a@b.co', 'a' * 64 + '@' + 'b' * 63 + '.com'],
    },
    'password': {
        'positive': ['P@ssw0rd123', 'SecurePass!1'],
        'negative': ['', ' '],
        'boundary': ['a', 'a' * 128],
    },
    'number': {
        'positive': ['42', '100'],
        'negative': ['', 'abc', '!@#'],
        'boundary': ['0', '-1', '999999999'],
    },
    'tel': {
        'positive': ['0912345678', '+886912345678'],
        'negative': ['', 'not-a-phone', 'abcdefg'],
        'boundary': ['1', '0' * 20],
    },
    'url': {
        'positive': ['https://example.com', 'https://www.google.com/search?q=test'],
        'negative': ['', 'not-a-url', 'ftp://'],
        'boundary': ['https://a.co', 'https://' + 'a' * 200 + '.com'],
    },
    'search': {
        'positive': ['Selenium', 'Python 自動化測試'],
        'negative': [''],
        'boundary': ['a', 'a' * 500],
    },
    'textarea': {
        'positive': ['這是一段正常的測試文字。\n包含換行。'],
        'negative': ['', ' '],
        'boundary': ['a', 'a' * 1000],
    },
}


def _get_values_for_input(constraint):
    """根據 input 的 type 和限制條件產生測試值。"""
    input_type = constraint.get('type', 'text')
    base = VALUE_GENERATORS.get(input_type, VALUE_GENERATORS['text'])

    positive = list(base['positive'])
    negative = list(base['negative'])
    boundary = list(base['boundary'])

    # 根據 maxlength 調整邊界值
    maxlen = constraint.get('maxlength')
    if maxlen:
        boundary.append('a' * maxlen)        # 剛好等於上限
        boundary.append('a' * (maxlen + 1))  # 超過上限
        boundary.append('a' * (maxlen - 1))  # 差一個到上限

    # 根據 minlength 調整邊界值
    minlen = constraint.get('minlength')
    if minlen and minlen > 0:
        boundary.append('a' * minlen)        # 剛好等於下限
        boundary.append('a' * (minlen - 1))  # 差一個不到下限

    # 根據 min/max (數值) 調整
    if constraint.get('min'):
        try:
            v = int(constraint['min'])
            boundary.extend([str(v), str(v - 1)])
        except ValueError:
            pass
    if constraint.get('max'):
        try:
            v = int(constraint['max'])
            boundary.extend([str(v), str(v + 1)])
        except ValueError:
            pass

    # 如果是 required，空字串屬於反向
    if constraint.get('required') and '' not in negative:
        negative.insert(0, '')

    # 去重
    positive = list(dict.fromkeys(positive))
    negative = list(dict.fromkeys(negative))
    boundary = list(dict.fromkeys(boundary))

    return positive, negative, boundary


def generate_test_data(constraints, output_path=None):
    """
    根據 input constraints 自動產生測試資料 JSON。

    Args:
        constraints: PageAnalyzer.get_input_constraints() 的回傳值
        output_path: 輸出 JSON 的路徑（None 則只回傳 dict）

    Returns:
        dict: { field_name: { positive: [...], negative: [...], boundary: [...] } }
    """
    test_data = {}

    for c in constraints:
        field_name = c.get('name') or c['locator']['value']
        positive, negative, boundary = _get_values_for_input(c)

        test_data[field_name] = {
            'locator': c['locator'],
            'type': c['type'],
            'required': c.get('required', False),
            'positive': positive,
            'negative': negative,
            'boundary': boundary,
        }

    if output_path:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(test_data, f, ensure_ascii=False, indent=2)

    return test_data


def generate_page_object(report, scenario_name, output_path):
    """
    根據分析報告自動產生 Page Object 骨架。

    Args:
        report: PageAnalyzer.analyze() 的回傳值
        scenario_name: 情境名稱（用於類別名）
        output_path: 輸出 .py 的路徑
    """
    class_name = ''.join(w.capitalize() for w in scenario_name.split('_')) + 'Page'
    url = report.get('url', '')

    lines = [
        '"""',
        f'Page Object - {scenario_name}',
        '',
        f'自動產生於 {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        f'來源 URL: {url}',
        '"""',
        '',
        'from selenium.webdriver.common.by import By',
        'from pages.base_page import BasePage',
        '',
        '',
        f'class {class_name}(BasePage):',
        f'    """Page Object for {url}"""',
        '',
        '    # === Locators（自動偵測）===',
    ]

    by_map = {'id': 'By.ID', 'name': 'By.NAME', 'css': 'By.CSS_SELECTOR', 'xpath': 'By.XPATH'}

    # 產生 input locators
    for i, inp in enumerate(report.get('inputs', [])):
        loc = inp['locator']
        by_str = by_map.get(loc['by'], 'By.CSS_SELECTOR')
        var_name = _to_var_name(inp.get('name') or inp.get('id') or f'input_{i}')
        lines.append(f'    {var_name.upper()} = ({by_str}, \'{loc["value"]}\')')

    # 產生 button locators
    for i, btn in enumerate(report.get('buttons', [])):
        loc = btn['locator']
        by_str = by_map.get(loc['by'], 'By.CSS_SELECTOR')
        var_name = _to_var_name(btn.get('name') or btn.get('id') or btn.get('text') or f'button_{i}')
        lines.append(f'    BTN_{var_name.upper()} = ({by_str}, \'{loc["value"]}\')')

    # 產生 select locators
    for i, sel in enumerate(report.get('selects', [])):
        loc = sel['locator']
        by_str = by_map.get(loc['by'], 'By.CSS_SELECTOR')
        var_name = _to_var_name(sel.get('name') or sel.get('id') or f'select_{i}')
        lines.append(f'    SELECT_{var_name.upper()} = ({by_str}, \'{loc["value"]}\')')

    # 產生 textarea locators
    for i, ta in enumerate(report.get('textareas', [])):
        loc = ta['locator']
        by_str = by_map.get(loc['by'], 'By.CSS_SELECTOR')
        var_name = _to_var_name(ta.get('name') or ta.get('id') or f'textarea_{i}')
        lines.append(f'    {var_name.upper()} = ({by_str}, \'{loc["value"]}\')')

    lines.append('')
    lines.append(f'    def __init__(self, driver, url=\'{url}\'):')
    lines.append('        super().__init__(driver)')
    lines.append('        self.url = url')
    lines.append('')
    lines.append('    def open_page(self):')
    lines.append('        """開啟頁面。"""')
    lines.append('        self.open(self.url)')
    lines.append('        return self')
    lines.append('')

    # 產生 input 方法
    for i, inp in enumerate(report.get('inputs', [])):
        var_name = _to_var_name(inp.get('name') or inp.get('id') or f'input_{i}')
        lines.append(f'    def fill_{var_name}(self, text):')
        lines.append(f'        """輸入 {inp.get("placeholder") or var_name}。"""')
        lines.append(f'        self.input_text(*self.{var_name.upper()}, text)')
        lines.append('')

    # 產生 button 方法
    for i, btn in enumerate(report.get('buttons', [])):
        var_name = _to_var_name(btn.get('name') or btn.get('id') or btn.get('text') or f'button_{i}')
        lines.append(f'    def click_{var_name}(self):')
        lines.append(f'        """點擊 {btn.get("text") or var_name}。"""')
        lines.append(f'        self.click(*self.BTN_{var_name.upper()})')
        lines.append('')

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return output_path


def generate_test_file(test_data, page_class_name, page_module_path, output_path):
    """
    根據測試資料自動產生 pytest 測試骨架。

    Args:
        test_data: generate_test_data() 的回傳值
        page_class_name: Page Object 類別名
        page_module_path: Page Object 的 import 路徑
        output_path: 輸出 .py 的路徑
    """
    lines = [
        '"""',
        f'自動產生的測試案例',
        f'產生時間: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
        '"""',
        '',
        'import pytest',
        '',
        f'from {page_module_path} import {page_class_name}',
        '',
        '',
        '# === Fixtures ===',
        '',
        '@pytest.fixture',
        'def page(driver, scenario_url):',
        f'    p = {page_class_name}(driver, url=scenario_url)',
        '    p.open_page()',
        '    return p',
        '',
        '',
        '# === Tests ===',
        '',
        f'class Test{page_class_name.replace("Page", "")}:',
    ]

    for field_name, data in test_data.items():
        safe_name = _to_var_name(field_name)

        # 正向測試
        lines.append('')
        lines.append(f'    @pytest.mark.positive')
        lines.append(f'    @pytest.mark.parametrize("value", {data["positive"]!r})')
        lines.append(f'    def test_{safe_name}_positive(self, page, value):')
        lines.append(f'        """正向測試：{field_name} 接受合法值。"""')
        lines.append(f'        page.fill_{safe_name}(value)')
        lines.append(f'        assert page.get_input_value(*page.{safe_name.upper()}) != ""')
        lines.append('')

        # 反向測試
        lines.append(f'    @pytest.mark.negative')
        lines.append(f'    @pytest.mark.parametrize("value", {data["negative"]!r})')
        lines.append(f'    def test_{safe_name}_negative(self, page, value):')
        lines.append(f'        """反向測試：{field_name} 拒絕非法值。"""')
        lines.append(f'        page.fill_{safe_name}(value)')
        lines.append(f'        # TODO: 驗證錯誤訊息或表單驗證')
        lines.append('')

        # 邊界測試
        lines.append(f'    @pytest.mark.boundary')
        lines.append(f'    @pytest.mark.parametrize("value", {data["boundary"]!r})')
        lines.append(f'    def test_{safe_name}_boundary(self, page, value):')
        lines.append(f'        """邊界測試：{field_name} 邊界值行為。"""')
        lines.append(f'        page.fill_{safe_name}(value)')
        lines.append(f'        # TODO: 驗證邊界行為')
        lines.append('')

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(lines))

    return output_path


def _to_var_name(text):
    """把任意字串轉成合法的 Python 變數名。"""
    text = re.sub(r'[^\w]', '_', text)
    text = re.sub(r'_+', '_', text).strip('_').lower()
    if not text or text[0].isdigit():
        text = 'field_' + text
    return text
