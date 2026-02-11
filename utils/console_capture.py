"""
瀏覽器 Console Log 擷取工具

擷取瀏覽器控制台的 JavaScript 錯誤與警告，
用於測試除錯與前端品質檢查。
"""

import json
import os
from selenium.webdriver.remote.webdriver import WebDriver


class ConsoleCapture:
    """
    瀏覽器 Console Log 擷取器。

    注意：需要 Chrome/Edge 瀏覽器才支援 get_log('browser')。
    Firefox 目前不支援此 API。
    """

    # 日誌層級常數
    SEVERE = 'SEVERE'
    WARNING = 'WARNING'
    INFO = 'INFO'
    ALL_LEVELS = (SEVERE, WARNING, INFO)

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self._history = []

    def get_logs(self, level=None):
        """
        取得瀏覽器 console log。

        Args:
            level: 過濾層級，可選 'SEVERE', 'WARNING', 'INFO'。
                   None 表示取得全部。

        Returns:
            list[dict]: 每筆包含 level, message, timestamp 欄位。
        """
        try:
            logs = self.driver.get_log('browser')
        except Exception:
            return []

        if level:
            logs = [log for log in logs if log.get('level') == level]

        self._history.extend(logs)
        return logs

    def get_errors(self):
        """只取得 SEVERE 層級的錯誤日誌。"""
        return self.get_logs(level=self.SEVERE)

    def get_warnings(self):
        """只取得 WARNING 層級的警告日誌。"""
        return self.get_logs(level=self.WARNING)

    def has_errors(self):
        """檢查頁面是否有 JavaScript 錯誤。"""
        return len(self.get_errors()) > 0

    def get_history(self):
        """取得自建立以來收集的所有日誌歷史。"""
        return list(self._history)

    def clear_history(self):
        """清除日誌歷史。"""
        self._history.clear()

    def save_logs(self, file_path, level=None):
        """
        將 console log 儲存到 JSON 檔案。

        Usage:
            capture.save_logs('logs/console_errors.json', level='SEVERE')
        """
        logs = self.get_logs(level=level)
        os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(logs, f, ensure_ascii=False, indent=2)
        return file_path

    def assert_no_errors(self):
        """
        斷言頁面沒有 JS 錯誤，有錯則拋出 AssertionError。

        Usage:
            capture.assert_no_errors()  # 如有 SEVERE 錯誤會 raise
        """
        errors = self.get_errors()
        if errors:
            messages = [e.get('message', '') for e in errors]
            raise AssertionError(
                f'頁面有 {len(errors)} 個 JavaScript 錯誤:\n'
                + '\n'.join(f'  - {m}' for m in messages)
            )
