#!/usr/bin/env python3
"""
測試匯出器 — 拋棄式腳本產生器

分析指定的測試檔案，追蹤所有相依的 Page Object、Utils、測試資料，
打包成一個可以獨立執行的 Python 檔案，不需要整個框架。

Usage:
    python export_test.py scenarios/demo_search/tests/test_search.py
    python export_test.py scenarios/demo_search/tests/test_search.py -o ~/Desktop/run_search.py
    python export_test.py scenarios/demo_search/tests/test_search.py --browser chrome --headless

產出的腳本可以直接執行:
    pytest run_search.py -v
    python run_search.py          # 自帶 pytest.main() 入口
"""

import argparse
import ast
import os
import sys
import json
import re
import textwrap
from datetime import datetime

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))


def main():
    parser = argparse.ArgumentParser(description='匯出測試為獨立拋棄式腳本')
    parser.add_argument('test_file', help='要匯出的測試檔案路徑')
    parser.add_argument('-o', '--output', default='', help='輸出檔案路徑（預設: exported_<name>.py）')
    parser.add_argument('--browser', default='chrome', choices=['chrome', 'firefox', 'edge'],
                        help='內嵌的預設瀏覽器')
    parser.add_argument('--headless', action='store_true', help='內嵌為無頭模式')
    parser.add_argument('--url', default='', help='覆寫 scenario URL')
    args = parser.parse_args()

    test_path = os.path.abspath(args.test_file)
    if not os.path.exists(test_path):
        print(f'[錯誤] 找不到檔案: {test_path}')
        sys.exit(1)

    exporter = TestExporter(
        test_path=test_path,
        browser=args.browser,
        headless=args.headless,
        url_override=args.url,
    )
    result = exporter.export()

    # 決定輸出路徑
    if args.output:
        output_path = os.path.abspath(args.output)
    else:
        base_name = os.path.splitext(os.path.basename(test_path))[0]
        output_path = os.path.join(os.getcwd(), f'exported_{base_name}.py')

    os.makedirs(os.path.dirname(output_path) or '.', exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f'[OK] 已匯出: {output_path}')
    print(f'     執行方式: pytest {output_path} -v')
    print(f'     或:       python {output_path}')


class TestExporter:
    """測試匯出器核心。"""

    def __init__(self, test_path, browser='chrome', headless=False, url_override=''):
        self.test_path = test_path
        self.test_dir = os.path.dirname(test_path)
        self.browser = browser
        self.headless = headless
        self.url_override = url_override

        # 尋找 scenario 根目錄（有 conftest.py 的上一層）
        self.scenario_dir = self._find_scenario_dir()
        self.scenario_url = url_override or self._detect_scenario_url()

        # 追蹤的檔案
        self.page_objects = {}    # {class_name: source_code}
        self.test_data_files = {} # {var_name: json_content}
        self.utils_used = set()   # 用到的 utils 模組名稱

    def export(self) -> str:
        """執行完整匯出流程，回傳合併後的 Python 程式碼。"""
        test_source = self._read_file(self.test_path)
        tree = ast.parse(test_source)

        # 1. 分析 imports
        imports_info = self._analyze_imports(tree, test_source)

        # 2. 讀取 Page Object 原始碼
        for po_info in imports_info['page_objects']:
            self._collect_page_object(po_info)

        # 3. 讀取測試資料
        self._collect_test_data(test_source)

        # 4. 分析測試用到的 fixtures
        fixtures_used = self._analyze_fixtures(tree)

        # 5. 組裝輸出
        return self._assemble(test_source, imports_info, fixtures_used)

    def _assemble(self, test_source, imports_info, fixtures_used) -> str:
        """組裝最終輸出的 Python 程式碼。"""
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        test_name = os.path.basename(self.test_path)

        sections = []

        # === Header ===
        sections.append(f'''#!/usr/bin/env python3
"""
拋棄式測試腳本（自動匯出）

原始檔案: {self.test_path}
匯出時間: {now}
瀏覽器:   {self.browser}
無頭模式: {self.headless}
目標 URL: {self.scenario_url or '(未指定)'}

執行方式:
    pytest {test_name} -v
    python {test_name}
"""
''')

        # === Imports ===
        sections.append(self._build_imports())

        # === BasePage（內嵌精簡版）===
        if self.page_objects:
            sections.append(self._build_inline_base_page())

        # === Page Objects（內嵌）===
        for class_name, source in self.page_objects.items():
            sections.append(f'\n# === Page Object: {class_name} ===\n')
            # 移除原本的 import BasePage，已經內嵌了
            cleaned = self._remove_imports(source, ['from pages.base_page', 'from pages import'])
            sections.append(cleaned)

        # === 測試資料（內嵌 Python literal）===
        if self.test_data_files:
            sections.append('\n# === 測試資料（內嵌）===\n')
            for var_name, data in self.test_data_files.items():
                sections.append(f'{var_name} = {repr(data)}\n')

        # === data_loader 簡化版 ===
        if self._needs_data_loader(test_source):
            sections.append(self._build_inline_data_loader())

        # === Driver 設定 + Fixtures ===
        sections.append(self._build_fixtures(fixtures_used))

        # === 測試程式碼 ===
        sections.append('\n# === 測試 ===\n')
        cleaned_test = self._clean_test_source(test_source)
        sections.append(cleaned_test)

        # === main() 入口 ===
        sections.append(self._build_main_entry())

        return '\n'.join(sections)

    def _build_imports(self) -> str:
        """產生標準 imports。"""
        return textwrap.dedent('''
            import os
            import sys
            import json
            import time
            import pytest

            from selenium import webdriver
            from selenium.webdriver.remote.webdriver import WebDriver
            from selenium.webdriver.support.ui import WebDriverWait, Select
            from selenium.webdriver.support import expected_conditions as EC
            from selenium.webdriver.common.action_chains import ActionChains
            from selenium.webdriver.common.by import By
            from selenium.webdriver.common.keys import Keys
            from selenium.webdriver.chrome.service import Service as ChromeService
            from selenium.webdriver.firefox.service import Service as FirefoxService
            from selenium.webdriver.edge.service import Service as EdgeService

            try:
                from webdriver_manager.chrome import ChromeDriverManager
                from webdriver_manager.firefox import GeckoDriverManager
                from webdriver_manager.microsoft import EdgeChromiumDriverManager
                _HAS_WDM = True
            except ImportError:
                _HAS_WDM = False
        ''')

    def _build_inline_base_page(self) -> str:
        """內嵌精簡版 BasePage。"""
        bp_path = os.path.join(ROOT_DIR, 'pages', 'base_page.py')
        if not os.path.exists(bp_path):
            return ''

        source = self._read_file(bp_path)
        # 移除 imports（已經在頂部了）
        cleaned = self._remove_imports(source, [
            'from selenium', 'from pages', 'import ',
        ])
        # 移除 docstring header
        cleaned = re.sub(r'^"""[\s\S]*?"""', '', cleaned, count=1).strip()

        return f'\n# === BasePage（內嵌）===\n\n{cleaned}\n'

    def _build_inline_data_loader(self) -> str:
        """產生內嵌版 data_loader。"""
        return textwrap.dedent('''
            # === data_loader（內嵌）===

            def load_json(file_path):
                with open(file_path, 'r', encoding='utf-8') as f:
                    return json.load(f)

            def load_test_data(file_path, fields, id_field='id'):
                data = load_json(file_path)
                params = []
                for row in data:
                    values = tuple(row.get(f, '') for f in fields)
                    test_id = row.get(id_field, '')
                    params.append(pytest.param(*values, id=test_id))
                return params
        ''')

    def _build_fixtures(self, fixtures_used) -> str:
        """產生 driver / page / URL 等 fixture。"""
        headless_str = 'True' if self.headless else 'False'
        url_str = self.scenario_url or 'https://example.com'

        parts = ['\n# === 設定 & Fixtures ===\n']
        parts.append(f'BROWSER = {self.browser!r}')
        parts.append(f'HEADLESS = {headless_str}')
        parts.append(f'SCENARIO_URL = {url_str!r}')
        parts.append(f'IMPLICIT_WAIT = 10')
        parts.append('')

        # create_driver 函式
        parts.append(textwrap.dedent('''
            def create_driver(browser=BROWSER, headless=HEADLESS):
                """建立 WebDriver。"""
                browser = browser.lower()
                if browser == 'chrome':
                    options = webdriver.ChromeOptions()
                    if headless:
                        options.add_argument('--headless=new')
                        options.add_argument('--no-sandbox')
                        options.add_argument('--disable-dev-shm-usage')
                    if _HAS_WDM:
                        service = ChromeService(ChromeDriverManager().install())
                        return webdriver.Chrome(service=service, options=options)
                    return webdriver.Chrome(options=options)
                elif browser == 'firefox':
                    options = webdriver.FirefoxOptions()
                    if headless:
                        options.add_argument('--headless')
                    if _HAS_WDM:
                        service = FirefoxService(GeckoDriverManager().install())
                        return webdriver.Firefox(service=service, options=options)
                    return webdriver.Firefox(options=options)
                elif browser == 'edge':
                    options = webdriver.EdgeOptions()
                    if headless:
                        options.add_argument('--headless=new')
                    if _HAS_WDM:
                        service = EdgeService(EdgeChromiumDriverManager().install())
                        return webdriver.Edge(service=service, options=options)
                    return webdriver.Edge(options=options)
                else:
                    raise ValueError(f'不支援的瀏覽器: {browser}')
        '''))

        # driver fixture
        parts.append(textwrap.dedent('''
            @pytest.fixture(scope='session')
            def driver():
                """Session 層級 WebDriver。"""
                _driver = create_driver()
                _driver.implicitly_wait(IMPLICIT_WAIT)
                yield _driver
                _driver.quit()
        '''))

        # scenario_url fixture
        if 'scenario_url' in fixtures_used:
            parts.append(textwrap.dedent('''
                @pytest.fixture
                def scenario_url():
                    return SCENARIO_URL
            '''))

        return '\n'.join(parts)

    def _build_main_entry(self) -> str:
        """產生 __main__ 入口。"""
        return textwrap.dedent('''

            # === 直接執行入口 ===

            if __name__ == '__main__':
                sys.exit(pytest.main([__file__, '-v', '--tb=short']))
        ''')

    # === 分析工具 ===

    def _analyze_imports(self, tree, source) -> dict:
        """分析 AST 中的 import 語句。"""
        info = {
            'page_objects': [],   # [{'module': '...', 'name': '...'}]
            'utils': [],          # ['data_loader', ...]
            'stdlib': [],
            'third_party': [],
        }

        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                module = node.module or ''

                # Page Objects: from scenarios.xxx.pages.xxx import XxxPage
                # 或: from pages.xxx import XxxPage
                if '.pages.' in module or module.startswith('pages.'):
                    for alias in node.names:
                        info['page_objects'].append({
                            'module': module,
                            'name': alias.name,
                        })

                # Utils: from utils.xxx import xxx
                elif module.startswith('utils.'):
                    util_name = module.split('.')[1] if '.' in module else module
                    info['utils'].append(util_name)
                    self.utils_used.add(util_name)

        return info

    def _analyze_fixtures(self, tree) -> set:
        """分析測試函式參數，判斷用到哪些 fixtures。"""
        fixtures = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                if node.name.startswith('test_') or node.name.startswith('_'):
                    for arg in node.args.args:
                        name = arg.arg
                        if name not in ('self', 'cls'):
                            fixtures.add(name)
                # fixture function 的參數也要收集
                for deco in node.decorator_list:
                    if isinstance(deco, ast.Attribute) and deco.attr == 'fixture':
                        for arg in node.args.args:
                            name = arg.arg
                            if name not in ('self', 'cls'):
                                fixtures.add(name)
        return fixtures

    def _collect_page_object(self, po_info):
        """讀取 Page Object 原始碼。"""
        module = po_info['module']
        class_name = po_info['name']

        # 嘗試找到實體檔案
        possible_paths = [
            # scenarios/xxx/pages/yyy.py
            os.path.join(ROOT_DIR, module.replace('.', '/') + '.py'),
            # 相對於測試目錄
            os.path.join(self.scenario_dir, 'pages',
                         module.split('.')[-1] + '.py') if self.scenario_dir else '',
        ]

        for path in possible_paths:
            if path and os.path.exists(path):
                source = self._read_file(path)
                self.page_objects[class_name] = source
                return

        print(f'  [警告] 找不到 Page Object: {module}.{class_name}')

    def _collect_test_data(self, test_source):
        """從測試原始碼中找到引用的 JSON/CSV 測試資料檔。"""
        # 找到類似 os.path.join(DATA_DIR, 'search.json') 的模式
        patterns = [
            r"['\"]([^'\"]+\.json)['\"]",
            r"['\"]([^'\"]+\.csv)['\"]",
        ]

        data_files_found = set()
        for pattern in patterns:
            for match in re.finditer(pattern, test_source):
                filename = match.group(1)
                data_files_found.add(filename)

        # 嘗試讀取
        for filename in data_files_found:
            possible_paths = [
                os.path.join(self.test_dir, '..', 'test_data', filename),
                os.path.join(self.scenario_dir, 'test_data', filename) if self.scenario_dir else '',
                os.path.join(ROOT_DIR, filename),
            ]

            for path in possible_paths:
                abs_path = os.path.abspath(path) if path else ''
                if abs_path and os.path.exists(abs_path):
                    try:
                        with open(abs_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                        var_name = '_EMBEDDED_' + os.path.splitext(os.path.basename(filename))[0].upper()
                        self.test_data_files[var_name] = data
                        print(f'  [資料] 內嵌: {filename} → {var_name}')
                    except Exception:
                        pass
                    break

    def _needs_data_loader(self, source) -> bool:
        """是否需要內嵌 data_loader。"""
        return 'load_test_data' in source or 'load_json' in source

    def _clean_test_source(self, source) -> str:
        """清理測試原始碼：移除框架 import，替換內嵌引用。"""
        lines = source.split('\n')
        cleaned = []

        skip_patterns = [
            'from utils.',
            'from pages.',
            'from scenarios.',
            'from config.',
            'import pytest',  # 已在頂部
            'import os',      # 已在頂部
            'import sys',     # 已在頂部
        ]

        # 先用多行合併處理 load_test_data(...) 跨行呼叫
        merged_source = self._merge_multiline_calls(source)
        lines = merged_source.split('\n')

        i = 0
        while i < len(lines):
            line = lines[i]
            stripped = line.strip()

            # 跳過框架 imports
            if any(stripped.startswith(p) for p in skip_patterns):
                i += 1
                continue

            # 跳過 PATH / sys.path 設定
            if 'sys.path' in stripped:
                i += 1
                continue
            if stripped.startswith('ROOT_DIR') or stripped.startswith('DATA_DIR'):
                i += 1
                continue

            # 替換 load_test_data() 呼叫為內嵌版本
            if self.test_data_files and 'load_test_data(' in stripped:
                replaced = self._replace_load_call(line)
                if replaced:
                    cleaned.append(replaced)
                    i += 1
                    continue

            cleaned.append(line)
            i += 1

        result = '\n'.join(cleaned)

        # 加入 _inline_to_params 如果有替換
        if '_inline_to_params' in result:
            inline_helper = textwrap.dedent('''\
                def _inline_to_params(data, fields, id_field='id'):
                    """將內嵌資料轉為 pytest.param。"""
                    params = []
                    for row in data:
                        values = tuple(row.get(f, '') for f in fields)
                        test_id = row.get(id_field, '')
                        params.append(pytest.param(*values, id=test_id))
                    return params

            ''')
            result = inline_helper + result

        return result

    def _merge_multiline_calls(self, source: str) -> str:
        """將跨行的函式呼叫合併為單行，方便後續處理。"""
        lines = source.split('\n')
        merged = []
        buffer = ''
        paren_depth = 0

        for line in lines:
            if buffer:
                buffer += ' ' + line.strip()
                paren_depth += line.count('(') - line.count(')')
                if paren_depth <= 0:
                    merged.append(buffer)
                    buffer = ''
                    paren_depth = 0
            elif 'load_test_data(' in line and line.count('(') > line.count(')'):
                buffer = line
                paren_depth = line.count('(') - line.count(')')
            else:
                merged.append(line)

        if buffer:
            merged.append(buffer)

        return '\n'.join(merged)

    def _replace_load_call(self, line: str) -> str | None:
        """替換 load_test_data(...) 為 _inline_to_params(...)。"""
        for var_name in self.test_data_files:
            orig_name = var_name.replace('_EMBEDDED_', '').lower()
            if orig_name + '.json' in line or orig_name + '.csv' in line:
                # 提取 fields 參數
                fields_match = re.search(r'fields\s*=\s*(\[[^\]]+\])', line)
                if fields_match:
                    fields_str = fields_match.group(1)
                else:
                    fields_str = '[]'

                # 保留原本的 indent 和賦值
                indent = line[:len(line) - len(line.lstrip())]
                assign_match = re.match(r'^(\s*\w+\s*=\s*)', line)
                if assign_match:
                    prefix = assign_match.group(1)
                    return f'{prefix}_inline_to_params({var_name}, {fields_str})'
                else:
                    return f'{indent}_inline_to_params({var_name}, {fields_str})'

        return None

    # === 輔助方法 ===

    def _find_scenario_dir(self) -> str:
        """往上尋找 scenario 根目錄（含 conftest.py 且在 scenarios/ 下）。"""
        current = self.test_dir
        for _ in range(5):
            conftest = os.path.join(current, 'conftest.py')
            if os.path.exists(conftest) and 'scenarios' in current:
                return current
            parent = os.path.dirname(current)
            if parent == current:
                break
            current = parent
        return self.test_dir

    def _detect_scenario_url(self) -> str:
        """從 scenario conftest.py 中偵測 SCENARIO_URL。"""
        conftest = os.path.join(self.scenario_dir, 'conftest.py')
        if not os.path.exists(conftest):
            return ''

        source = self._read_file(conftest)
        match = re.search(r"SCENARIO_URL\s*=\s*['\"]([^'\"]+)['\"]", source)
        return match.group(1) if match else ''

    def _read_file(self, path) -> str:
        """讀取檔案。"""
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()

    def _remove_imports(self, source, prefixes) -> str:
        """移除以指定前綴開頭的 import 行。"""
        lines = source.split('\n')
        cleaned = []
        for line in lines:
            stripped = line.strip()
            if any(stripped.startswith(p) for p in prefixes):
                continue
            cleaned.append(line)
        return '\n'.join(cleaned)


if __name__ == '__main__':
    main()
