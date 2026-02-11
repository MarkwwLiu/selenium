"""
Selenium 測試專案 - 集中設定檔

將所有可配置的參數集中管理，避免在程式碼中硬編碼。
"""

import os

# === 專案路徑 ===
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
REPORTS_DIR = os.path.join(BASE_DIR, 'reports')
SCREENSHOTS_DIR = os.path.join(BASE_DIR, 'screenshots')
LOGS_DIR = os.path.join(BASE_DIR, 'logs')

# === 瀏覽器設定 ===
BROWSER = 'chrome'           # 支援: 'chrome', 'firefox', 'edge'
HEADLESS = False              # True = 無頭模式（適用於 CI/CD）
IMPLICIT_WAIT = 10            # 隱式等待秒數

# === 測試目標 ===
BASE_URL = 'https://shareboxnow.com/'

# === 報告設定 ===
REPORT_FILENAME = 'Demo_BeautifulReport'
REPORT_DESCRIPTION = 'Selenium 自動化測試報告'

# === 等待時間 ===
TEARDOWN_WAIT = 3             # tearDown 後等待秒數

# === 截圖設定 ===
SCREENSHOT_ON_FAILURE = True  # 測試失敗時是否自動截圖

# === 日誌設定 ===
LOG_ENABLED = True            # 是否啟用日誌紀錄到檔案
