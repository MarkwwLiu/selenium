"""
Cookie 管理工具

提供 Cookie 的新增、讀取、刪除、匯出/匯入功能，
適用於登入狀態保存、跳過重複登入等場景。
"""

import json
import os
from selenium.webdriver.remote.webdriver import WebDriver


class CookieManager:
    """Cookie 管理工具，綁定一個 WebDriver 實例。"""

    def __init__(self, driver: WebDriver):
        self.driver = driver

    def get_cookie(self, name):
        """取得指定名稱的 Cookie，找不到回傳 None。"""
        return self.driver.get_cookie(name)

    def get_all_cookies(self):
        """取得所有 Cookie，回傳 list[dict]。"""
        return self.driver.get_cookies()

    def add_cookie(self, name, value, **kwargs):
        """
        新增一個 Cookie。

        Args:
            name: Cookie 名稱
            value: Cookie 值
            **kwargs: 其他選項如 domain, path, secure, httpOnly, expiry

        Usage:
            cm.add_cookie('token', 'abc123')
            cm.add_cookie('session', 'xyz', domain='.example.com', secure=True)
        """
        cookie = {'name': name, 'value': value}
        cookie.update(kwargs)
        self.driver.add_cookie(cookie)

    def delete_cookie(self, name):
        """刪除指定名稱的 Cookie。"""
        self.driver.delete_cookie(name)

    def delete_all_cookies(self):
        """刪除所有 Cookie。"""
        self.driver.delete_all_cookies()

    def save_cookies(self, file_path):
        """
        將當前所有 Cookie 匯出到 JSON 檔案。

        適用於保存登入狀態，下次測試直接載入跳過登入流程。

        Usage:
            cm.save_cookies('cookies/login_state.json')
        """
        cookies = self.get_all_cookies()
        os.makedirs(os.path.dirname(file_path) or '.', exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(cookies, f, ensure_ascii=False, indent=2)
        return file_path

    def load_cookies(self, file_path):
        """
        從 JSON 檔案載入 Cookie。

        注意：載入前需先導航到目標網域（Cookie 有域名限制）。

        Usage:
            driver.get('https://example.com')
            cm.load_cookies('cookies/login_state.json')
            driver.refresh()  # 重新整理讓 Cookie 生效
        """
        with open(file_path, 'r', encoding='utf-8') as f:
            cookies = json.load(f)

        for cookie in cookies:
            # 移除可能造成問題的欄位
            cookie.pop('sameSite', None)
            try:
                self.driver.add_cookie(cookie)
            except Exception:
                # 跳過無法新增的 Cookie（例如跨域）
                pass

    def has_cookie(self, name):
        """檢查指定 Cookie 是否存在。"""
        return self.get_cookie(name) is not None

    def get_cookie_value(self, name):
        """取得指定 Cookie 的值，不存在回傳 None。"""
        cookie = self.get_cookie(name)
        return cookie['value'] if cookie else None
