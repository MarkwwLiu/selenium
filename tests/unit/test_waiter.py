"""
utils/waiter.py 單元測試
"""

import time
from unittest.mock import MagicMock, patch
import pytest
from selenium.common.exceptions import TimeoutException

from utils.waiter import Waiter


@pytest.fixture
def mock_driver():
    return MagicMock()


@pytest.fixture
def waiter(mock_driver):
    return Waiter(mock_driver, default_timeout=2)


class TestInit:
    @pytest.mark.positive
    def test_default_timeout(self, mock_driver):
        w = Waiter(mock_driver)
        assert w.default_timeout == 10

    @pytest.mark.positive
    def test_custom_timeout(self, mock_driver):
        w = Waiter(mock_driver, default_timeout=30)
        assert w.default_timeout == 30


class TestWaitForPageLoad:
    @pytest.mark.positive
    @patch('utils.waiter.WebDriverWait')
    def test_success(self, MockWait, waiter):
        MockWait.return_value.until.return_value = True
        waiter.wait_for_page_load()
        MockWait.return_value.until.assert_called_once()

    @pytest.mark.positive
    @patch('utils.waiter.WebDriverWait')
    def test_custom_timeout(self, MockWait, waiter):
        MockWait.return_value.until.return_value = True
        waiter.wait_for_page_load(timeout=30)
        MockWait.assert_called_once_with(waiter.driver, 30)


class TestWaitForAjax:
    @pytest.mark.positive
    @patch('utils.waiter.WebDriverWait')
    def test_success(self, MockWait, waiter):
        MockWait.return_value.until.return_value = True
        waiter.wait_for_ajax()
        MockWait.return_value.until.assert_called_once()


class TestWaitForElementCount:
    @pytest.mark.positive
    @patch('utils.waiter.WebDriverWait')
    def test_success(self, MockWait, waiter):
        MockWait.return_value.until.return_value = True
        waiter.wait_for_element_count('id', 'item', 5)
        MockWait.return_value.until.assert_called_once()


class TestWaitForElementCountGte:
    @pytest.mark.positive
    @patch('utils.waiter.WebDriverWait')
    def test_success(self, MockWait, waiter):
        MockWait.return_value.until.return_value = True
        waiter.wait_for_element_count_gte('id', 'item', 3)
        MockWait.return_value.until.assert_called_once()


class TestWaitForAttribute:
    @pytest.mark.positive
    @patch('utils.waiter.WebDriverWait')
    def test_success(self, MockWait, waiter):
        MockWait.return_value.until.return_value = True
        waiter.wait_for_attribute('id', 'el', 'data-status', 'ready')
        MockWait.return_value.until.assert_called_once()


class TestWaitForAttributeContains:
    @pytest.mark.positive
    @patch('utils.waiter.WebDriverWait')
    def test_success(self, MockWait, waiter):
        MockWait.return_value.until.return_value = True
        waiter.wait_for_attribute_contains('id', 'el', 'class', 'active')
        MockWait.return_value.until.assert_called_once()


class TestWaitForTextChange:
    @pytest.mark.positive
    @patch('utils.waiter.WebDriverWait')
    def test_success(self, MockWait, waiter):
        MockWait.return_value.until.return_value = True
        waiter.wait_for_text_change('id', 'counter', 'old')
        MockWait.return_value.until.assert_called_once()


class TestWaitForValueNotEmpty:
    @pytest.mark.positive
    @patch('utils.waiter.WebDriverWait')
    def test_success(self, MockWait, waiter):
        MockWait.return_value.until.return_value = True
        waiter.wait_for_value_not_empty('id', 'input')
        MockWait.return_value.until.assert_called_once()


class TestWaitForStable:
    @pytest.mark.positive
    def test_text_stabilizes(self, mock_driver):
        """文字穩定後立即回傳。"""
        mock_el = MagicMock()
        mock_el.text = '穩定文字'
        mock_driver.find_element.return_value = mock_el
        waiter = Waiter(mock_driver, default_timeout=3)
        result = waiter.wait_for_stable('id', 'el', stable_seconds=0.3)
        assert result == '穩定文字'

    @pytest.mark.negative
    def test_timeout(self, mock_driver):
        """文字一直變化時超時。"""
        call_count = [0]

        def changing_text():
            el = MagicMock()
            call_count[0] += 1
            el.text = f'text_{call_count[0]}'
            return el

        mock_driver.find_element.side_effect = lambda *a: changing_text()
        waiter = Waiter(mock_driver, default_timeout=1)
        with pytest.raises(TimeoutException):
            waiter.wait_for_stable('id', 'el', stable_seconds=5)

    @pytest.mark.positive
    def test_handles_element_exception(self, mock_driver):
        """元素找不到時繼續重試。"""
        call_count = [0]

        def side_effect(*args):
            call_count[0] += 1
            if call_count[0] <= 2:
                raise Exception('element not found')
            el = MagicMock()
            el.text = 'found'
            return el

        mock_driver.find_element.side_effect = side_effect
        waiter = Waiter(mock_driver, default_timeout=3)
        result = waiter.wait_for_stable('id', 'el', stable_seconds=0.3)
        assert result == 'found'


class TestWaitUntil:
    @pytest.mark.positive
    @patch('utils.waiter.WebDriverWait')
    def test_success(self, MockWait, waiter):
        MockWait.return_value.until.return_value = 'result'
        result = waiter.wait_until(lambda d: True)
        assert result == 'result'

    @pytest.mark.positive
    @patch('utils.waiter.WebDriverWait')
    def test_with_message(self, MockWait, waiter):
        MockWait.return_value.until.return_value = True
        waiter.wait_until(lambda d: True, message='等待條件')
        MockWait.return_value.until.assert_called_once()
