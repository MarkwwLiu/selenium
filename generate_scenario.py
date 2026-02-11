#!/usr/bin/env python3
"""
情境模組產生器

用法:
    python generate_scenario.py <scenario_name> [--url <target_url>]

範例:
    python generate_scenario.py login_test --url https://example.com/login
    python generate_scenario.py search_form

產生結果:
    scenarios/<scenario_name>/
    ├── conftest.py          ← 已配置的 conftest（driver、logger、截圖）
    ├── pytest.ini           ← 獨立的 pytest 設定
    ├── pages/
    │   └── __init__.py
    ├── tests/
    │   └── __init__.py
    ├── test_data/           ← 放 JSON / CSV 測試資料
    └── results/             ← 截圖、日誌、報告輸出
"""

import argparse
import shutil
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(BASE_DIR, 'scenarios', '_template')
SCENARIOS_DIR = os.path.join(BASE_DIR, 'scenarios')


def create_scenario(name: str, url: str = ''):
    """從模板複製並建立新的情境模組。"""
    target_dir = os.path.join(SCENARIOS_DIR, name)

    if os.path.exists(target_dir):
        print(f'[!] 情境已存在: {target_dir}')
        print('    請刪除後重新產生，或直接修改該目錄。')
        return

    # 複製模板
    shutil.copytree(TEMPLATE_DIR, target_dir)

    # 建立額外目錄
    os.makedirs(os.path.join(target_dir, 'results'), exist_ok=True)
    os.makedirs(os.path.join(target_dir, 'test_data'), exist_ok=True)

    # 如果有指定 URL，替換 conftest.py 中的 SCENARIO_URL
    if url:
        conftest_path = os.path.join(target_dir, 'conftest.py')
        with open(conftest_path, 'r', encoding='utf-8') as f:
            content = f.read()

        content = content.replace("SCENARIO_URL = ''", f"SCENARIO_URL = '{url}'")

        with open(conftest_path, 'w', encoding='utf-8') as f:
            f.write(content)

    print(f'[OK] 情境模組已建立: {target_dir}')
    print(f'     目標 URL: {url or "(未指定，請至 conftest.py 設定 SCENARIO_URL)"}')
    print()
    print('目錄結構:')
    print(f'  scenarios/{name}/')
    print(f'  ├── conftest.py      ← driver/logger/截圖 fixture')
    print(f'  ├── pytest.ini       ← pytest 設定')
    print(f'  ├── pages/           ← Page Object')
    print(f'  ├── tests/           ← 測試案例')
    print(f'  ├── test_data/       ← JSON/CSV 測試資料')
    print(f'  └── results/         ← 截圖/日誌/報告')
    print()
    print('執行方式:')
    print(f'  pytest scenarios/{name}/tests/ -v')
    print(f'  pytest scenarios/{name}/tests/ -m positive')
    print(f'  pytest scenarios/{name}/tests/ --html=scenarios/{name}/results/report.html')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='建立新的測試情境模組')
    parser.add_argument('name', help='情境名稱（英文、底線）')
    parser.add_argument('--url', default='', help='測試目標 URL')
    args = parser.parse_args()

    create_scenario(args.name, args.url)
