"""
統一測試執行入口

一鍵執行所有測試，支援命令列參數切換瀏覽器與模式。

使用方式:
    python run.py                          # 預設執行（Chrome，有畫面）
    python run.py --browser firefox        # 用 Firefox 執行
    python run.py --headless               # 無頭模式
    python run.py --report                 # 產生 HTML 報告
    python run.py --browser edge --headless --report  # 組合使用
"""

import os
import sys
import argparse
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import config.settings as settings


def parse_args():
    parser = argparse.ArgumentParser(description='Selenium 自動化測試執行器')
    parser.add_argument(
        '--browser', '-b',
        choices=['chrome', 'firefox', 'edge'],
        default=None,
        help='指定瀏覽器（預設使用 config/settings.py 的設定）',
    )
    parser.add_argument(
        '--headless',
        action='store_true',
        default=None,
        help='啟用無頭模式（不顯示瀏覽器視窗）',
    )
    parser.add_argument(
        '--report',
        action='store_true',
        help='產生 HTML 測試報告（BeautifulReport）',
    )
    return parser.parse_args()


def run_with_report():
    """使用 BeautifulReport 產生 HTML 報告。"""
    from BeautifulReport import BeautifulReport

    os.makedirs(settings.REPORTS_DIR, exist_ok=True)

    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')

    result = BeautifulReport(suite)
    result.report(
        filename=settings.REPORT_FILENAME,
        description=settings.REPORT_DESCRIPTION,
        report_dir=settings.REPORTS_DIR,
    )
    report_path = os.path.join(settings.REPORTS_DIR, f'{settings.REPORT_FILENAME}.html')
    print(f'\n報告已產生: {report_path}')


def run_with_text():
    """使用 TextTestRunner 輸出到終端機。"""
    loader = unittest.TestLoader()
    suite = loader.discover('tests', pattern='test_*.py')
    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)


def main():
    args = parse_args()

    # 用命令列參數覆蓋 settings（如有指定）
    if args.browser:
        settings.BROWSER = args.browser
    if args.headless:
        settings.HEADLESS = True

    print(f'瀏覽器: {settings.BROWSER}')
    print(f'Headless: {settings.HEADLESS}')
    print('-' * 40)

    if args.report:
        run_with_report()
    else:
        run_with_text()


if __name__ == '__main__':
    main()
