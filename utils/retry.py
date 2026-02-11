"""
重試工具

提供 retry 裝飾器，處理 Selenium 中不穩定元素的重試邏輯。
適用於因網路延遲、動畫、非同步載入導致的間歇性失敗。
"""

import time
import functools
from selenium.common.exceptions import (
    StaleElementReferenceException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    TimeoutException,
    NoSuchElementException,
)

# 預設可重試的例外類型
RETRYABLE_EXCEPTIONS = (
    StaleElementReferenceException,
    ElementClickInterceptedException,
    ElementNotInteractableException,
    TimeoutException,
    NoSuchElementException,
)


def retry(max_attempts=3, delay=0.5, exceptions=RETRYABLE_EXCEPTIONS):
    """
    重試裝飾器。

    Args:
        max_attempts: 最大嘗試次數（含首次）
        delay: 每次重試間隔秒數
        exceptions: 要捕獲並重試的例外類型 tuple

    Usage:
        @retry(max_attempts=3, delay=1)
        def click_unstable_button(self):
            self.click(By.ID, 'submit')
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    if attempt < max_attempts:
                        time.sleep(delay)
            raise last_exception
        return wrapper
    return decorator


def retry_on_stale(func):
    """
    簡易裝飾器：StaleElementReferenceException 時重試 3 次。

    Usage:
        @retry_on_stale
        def get_dynamic_text(self):
            return self.get_element_text(By.ID, 'counter')
    """
    return retry(
        max_attempts=3,
        delay=0.5,
        exceptions=(StaleElementReferenceException,),
    )(func)
