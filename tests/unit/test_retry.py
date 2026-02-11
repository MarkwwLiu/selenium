"""
retry 裝飾器單元測試
"""

from unittest.mock import MagicMock, patch
import pytest
from selenium.common.exceptions import (
    StaleElementReferenceException,
    ElementClickInterceptedException,
    NoSuchElementException,
)

from utils.retry import retry, retry_on_stale


class TestRetryDecorator:
    def test_success_first_attempt(self):
        """第一次就成功，不需重試。"""
        mock_fn = MagicMock(return_value='ok')

        @retry(max_attempts=3, delay=0)
        def do_something():
            return mock_fn()

        assert do_something() == 'ok'
        assert mock_fn.call_count == 1

    def test_success_after_retries(self):
        """前 2 次失敗，第 3 次成功。"""
        mock_fn = MagicMock(
            side_effect=[StaleElementReferenceException(), StaleElementReferenceException(), 'ok']
        )

        @retry(max_attempts=3, delay=0)
        def do_something():
            return mock_fn()

        assert do_something() == 'ok'
        assert mock_fn.call_count == 3

    def test_all_attempts_fail(self):
        """所有重試都失敗，應拋出最後一個例外。"""
        @retry(max_attempts=3, delay=0)
        def do_something():
            raise StaleElementReferenceException('always fails')

        with pytest.raises(StaleElementReferenceException):
            do_something()

    def test_non_retryable_exception(self):
        """非可重試的例外應立即拋出。"""
        @retry(max_attempts=3, delay=0, exceptions=(StaleElementReferenceException,))
        def do_something():
            raise ValueError('not retryable')

        with pytest.raises(ValueError):
            do_something()

    def test_custom_exceptions(self):
        """自訂可重試的例外類型。"""
        mock_fn = MagicMock(
            side_effect=[ElementClickInterceptedException(), 'ok']
        )

        @retry(max_attempts=3, delay=0, exceptions=(ElementClickInterceptedException,))
        def do_something():
            return mock_fn()

        assert do_something() == 'ok'
        assert mock_fn.call_count == 2

    def test_preserves_function_name(self):
        """裝飾器應保留原始函數的名稱。"""
        @retry(max_attempts=3, delay=0)
        def my_function():
            pass

        assert my_function.__name__ == 'my_function'

    def test_passes_args_and_kwargs(self):
        """確保參數正確傳遞。"""
        @retry(max_attempts=3, delay=0)
        def add(a, b, extra=0):
            return a + b + extra

        assert add(1, 2, extra=3) == 6

    @patch('utils.retry.time.sleep')
    def test_delay_between_retries(self, mock_sleep):
        """每次重試間應有延遲。"""
        mock_fn = MagicMock(
            side_effect=[StaleElementReferenceException(), StaleElementReferenceException(), 'ok']
        )

        @retry(max_attempts=3, delay=0.5)
        def do_something():
            return mock_fn()

        do_something()
        assert mock_sleep.call_count == 2
        mock_sleep.assert_called_with(0.5)


class TestRetryOnStale:
    def test_retries_on_stale(self):
        """StaleElementReferenceException 時自動重試。"""
        mock_fn = MagicMock(
            side_effect=[StaleElementReferenceException(), 'ok']
        )

        @retry_on_stale
        def do_something():
            return mock_fn()

        assert do_something() == 'ok'

    def test_does_not_retry_other_exceptions(self):
        """非 StaleElement 的例外不重試。"""
        @retry_on_stale
        def do_something():
            raise NoSuchElementException('not stale')

        with pytest.raises(NoSuchElementException):
            do_something()
