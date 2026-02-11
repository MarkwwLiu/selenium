"""
基礎測試類別

提供所有測試類別共用的 setUp / tearDown 邏輯，
包含 WebDriver 的初始化與關閉。
"""

import sys
import os
import time
import unittest

from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

# 將專案根目錄加入 sys.path，讓 config / pages 可以被匯入
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.settings import IMPLICIT_WAIT, TEARDOWN_WAIT


class BaseTest(unittest.TestCase):
    """所有測試類別的基礎父類別。"""

    @classmethod
    def setUpClass(cls):
        """
        初始化 ChromeDriver 並啟動 Chrome 瀏覽器。
        使用 webdriver-manager 自動管理驅動版本。
        """
        service = Service(ChromeDriverManager().install())
        cls.driver = webdriver.Chrome(service=service)
        cls.driver.implicitly_wait(IMPLICIT_WAIT)

    @classmethod
    def tearDownClass(cls):
        """關閉瀏覽器並釋放資源。"""
        cls.driver.quit()

    def tearDown(self):
        """每個測試方法結束後等待一段時間（方便觀察結果）。"""
        time.sleep(TEARDOWN_WAIT)
