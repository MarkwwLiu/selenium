"""
進階等待工具

提供超越 BasePage 內建方法的複合等待邏輯，
處理動態頁面、AJAX 載入、動畫完成等場景。
"""

import time
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException


class Waiter:
    """進階等待工具，綁定一個 WebDriver 實例。"""

    def __init__(self, driver: WebDriver, default_timeout=10):
        self.driver = driver
        self.default_timeout = default_timeout

    def wait_for_page_load(self, timeout=None):
        """等待頁面完整載入（document.readyState == 'complete'）。"""
        timeout = timeout or self.default_timeout
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script('return document.readyState') == 'complete'
        )

    def wait_for_ajax(self, timeout=None):
        """等待所有 jQuery AJAX 請求完成。"""
        timeout = timeout or self.default_timeout
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.execute_script(
                'return typeof jQuery === "undefined" || jQuery.active === 0'
            )
        )

    def wait_for_element_count(self, by, value, count, timeout=None):
        """等待符合條件的元素數量達到指定值。"""
        timeout = timeout or self.default_timeout
        WebDriverWait(self.driver, timeout).until(
            lambda d: len(d.find_elements(by, value)) == count
        )

    def wait_for_element_count_gte(self, by, value, min_count, timeout=None):
        """等待符合條件的元素數量 >= min_count。"""
        timeout = timeout or self.default_timeout
        WebDriverWait(self.driver, timeout).until(
            lambda d: len(d.find_elements(by, value)) >= min_count
        )

    def wait_for_attribute(self, by, value, attribute, expected, timeout=None):
        """等待元素的指定屬性變為 expected 值。"""
        timeout = timeout or self.default_timeout
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.find_element(by, value).get_attribute(attribute) == expected
        )

    def wait_for_attribute_contains(self, by, value, attribute, text, timeout=None):
        """等待元素的指定屬性包含 text。"""
        timeout = timeout or self.default_timeout
        WebDriverWait(self.driver, timeout).until(
            lambda d: text in (d.find_element(by, value).get_attribute(attribute) or '')
        )

    def wait_for_text_change(self, by, value, original_text, timeout=None):
        """等待元素文字從 original_text 變成其他值。"""
        timeout = timeout or self.default_timeout
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.find_element(by, value).text != original_text
        )

    def wait_for_value_not_empty(self, by, value, timeout=None):
        """等待輸入框的 value 不為空。"""
        timeout = timeout or self.default_timeout
        WebDriverWait(self.driver, timeout).until(
            lambda d: d.find_element(by, value).get_attribute('value') not in ('', None)
        )

    def wait_for_stable(self, by, value, stable_seconds=0.5, timeout=None):
        """
        等待元素穩定（文字不再變化）。
        適用於非同步計算結果、倒數計時停止等場景。
        """
        timeout = timeout or self.default_timeout
        deadline = time.time() + timeout
        last_text = None
        stable_since = None

        while time.time() < deadline:
            try:
                current_text = self.driver.find_element(by, value).text
            except Exception:
                time.sleep(0.1)
                continue

            if current_text == last_text:
                if stable_since and (time.time() - stable_since) >= stable_seconds:
                    return current_text
            else:
                last_text = current_text
                stable_since = time.time()

            time.sleep(0.1)

        raise TimeoutException(f'元素文字未在 {timeout} 秒內穩定')

    def wait_until(self, condition_fn, timeout=None, message=''):
        """
        通用等待：傳入任意 callable，回傳 truthy 即通過。

        Usage:
            waiter.wait_until(lambda d: d.find_element(By.ID, 'result').text == 'OK')
        """
        timeout = timeout or self.default_timeout
        return WebDriverWait(self.driver, timeout).until(condition_fn, message)
