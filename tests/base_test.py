"""
基礎測試類別

提供所有測試類別共用的 setUp / tearDown 邏輯，整合：
- WebDriver Factory（多瀏覽器 + Headless）
- 失敗自動截圖
- 結構化日誌紀錄
"""

import sys
import os
import time
import unittest

# 將專案根目錄加入 sys.path，讓 config / pages / utils 可以被匯入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import (
    BROWSER, HEADLESS, IMPLICIT_WAIT, TEARDOWN_WAIT,
    SCREENSHOTS_DIR, LOGS_DIR,
    SCREENSHOT_ON_FAILURE, LOG_ENABLED,
)
from utils.driver_factory import DriverFactory
from utils.screenshot import take_screenshot
from utils.logger import setup_logger


class BaseTest(unittest.TestCase):
    """所有測試類別的基礎父類別。"""

    logger = None

    @classmethod
    def setUpClass(cls):
        """
        初始化瀏覽器（透過 DriverFactory）並設定日誌。
        """
        # 設定日誌
        log_dir = LOGS_DIR if LOG_ENABLED else None
        cls.logger = setup_logger(name=cls.__name__, log_dir=log_dir)
        cls.logger.info(f'===== 開始測試: {cls.__name__} =====')
        cls.logger.info(f'瀏覽器: {BROWSER} | Headless: {HEADLESS}')

        # 建立 WebDriver
        cls.driver = DriverFactory.create_driver(
            browser=BROWSER,
            headless=HEADLESS,
        )
        cls.driver.implicitly_wait(IMPLICIT_WAIT)
        cls.logger.info('WebDriver 初始化完成')

    @classmethod
    def tearDownClass(cls):
        """關閉瀏覽器並釋放資源。"""
        cls.driver.quit()
        cls.logger.info(f'===== 結束測試: {cls.__name__} =====\n')

    def setUp(self):
        """紀錄測試方法開始。"""
        self.logger.info(f'▶ 執行: {self._testMethodName}')

    def tearDown(self):
        """
        每個測試方法結束後：
        1. 檢查是否失敗 → 自動截圖
        2. 紀錄結果到日誌
        3. 等待指定秒數
        """
        # 檢查測試結果
        result = self._outcome.result if hasattr(self._outcome, 'result') else None
        has_error = False

        if result:
            for test, _ in result.errors + result.failures:
                if test is self:
                    has_error = True
                    break

        if has_error and SCREENSHOT_ON_FAILURE:
            filepath = take_screenshot(
                self.driver, SCREENSHOTS_DIR, self._testMethodName
            )
            self.logger.warning(f'✘ 失敗: {self._testMethodName} → 截圖已儲存: {filepath}')
        elif has_error:
            self.logger.warning(f'✘ 失敗: {self._testMethodName}')
        else:
            self.logger.info(f'✔ 通過: {self._testMethodName}')

        time.sleep(TEARDOWN_WAIT)
