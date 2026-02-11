"""
統一測試執行入口

一鍵執行所有測試，支援命令列參數切換瀏覽器與模式。

使用方式:
    python run.py                                       # 預設執行（Chrome，有畫面）
    python run.py --browser firefox                     # 用 Firefox 執行
    python run.py --headless                            # 無頭模式
    python run.py --html                                # 產生 HTML 報告
    python run.py --allure                              # 產生 Allure 報告
    python run.py --env staging                         # 指定測試環境
    python run.py --reruns 2                            # 失敗重跑 2 次
    python run.py -m smoke                              # 只跑 smoke 標籤的測試
    python run.py -k "keyword"                          # 只跑名稱含 keyword 的測試
    python run.py --browser edge --headless --html      # 組合使用
"""

import sys
import pytest


def main():
    args = ['--tb=short', '-v']

    # 解析自訂參數並轉換為 pytest 格式
    i = 1
    passthrough = []
    while i < len(sys.argv):
        arg = sys.argv[i]

        if arg in ('--browser', '-b') and i + 1 < len(sys.argv):
            args.extend(['--browser', sys.argv[i + 1]])
            i += 2
        elif arg == '--headless':
            args.append('--headless-mode')
            i += 1
        elif arg == '--html':
            args.extend(['--html=reports/report.html', '--self-contained-html'])
            i += 1
        elif arg == '--allure':
            args.extend(['--alluredir=reports/allure-results'])
            i += 1
        elif arg in ('--env', '-e') and i + 1 < len(sys.argv):
            args.extend(['--env', sys.argv[i + 1]])
            i += 2
        elif arg == '--reruns' and i + 1 < len(sys.argv):
            args.extend(['--reruns', sys.argv[i + 1]])
            i += 2
        elif arg == '--reruns-delay' and i + 1 < len(sys.argv):
            args.extend(['--reruns-delay', sys.argv[i + 1]])
            i += 2
        else:
            passthrough.append(arg)
            i += 1

    args.extend(passthrough)

    print(f'參數: {" ".join(args)}')
    print('-' * 40)

    exit_code = pytest.main(args)
    sys.exit(exit_code)


if __name__ == '__main__':
    main()
