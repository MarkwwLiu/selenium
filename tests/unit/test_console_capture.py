"""
utils/console_capture.py 單元測試
"""

import json
import os
import tempfile
from unittest.mock import MagicMock
import pytest

from utils.console_capture import ConsoleCapture


@pytest.fixture
def mock_driver():
    return MagicMock()


@pytest.fixture
def capture(mock_driver):
    return ConsoleCapture(mock_driver)


class TestGetLogs:
    @pytest.mark.positive
    def test_all_levels(self, capture, mock_driver):
        logs = [
            {'level': 'SEVERE', 'message': 'err', 'timestamp': 1},
            {'level': 'WARNING', 'message': 'warn', 'timestamp': 2},
        ]
        mock_driver.get_log.return_value = logs
        result = capture.get_logs()
        assert len(result) == 2

    @pytest.mark.positive
    def test_filtered_level(self, capture, mock_driver):
        logs = [
            {'level': 'SEVERE', 'message': 'err'},
            {'level': 'WARNING', 'message': 'warn'},
        ]
        mock_driver.get_log.return_value = logs
        result = capture.get_logs(level='SEVERE')
        assert len(result) == 1
        assert result[0]['level'] == 'SEVERE'

    @pytest.mark.negative
    def test_driver_exception(self, capture, mock_driver):
        """瀏覽器不支援時回傳空 list。"""
        mock_driver.get_log.side_effect = Exception('not supported')
        result = capture.get_logs()
        assert result == []

    @pytest.mark.positive
    def test_appends_to_history(self, capture, mock_driver):
        mock_driver.get_log.return_value = [{'level': 'INFO', 'message': 'hi'}]
        capture.get_logs()
        capture.get_logs()
        assert len(capture.get_history()) == 2


class TestGetErrors:
    @pytest.mark.positive
    def test_returns_severe(self, capture, mock_driver):
        logs = [
            {'level': 'SEVERE', 'message': 'err'},
            {'level': 'WARNING', 'message': 'warn'},
        ]
        mock_driver.get_log.return_value = logs
        result = capture.get_errors()
        assert len(result) == 1


class TestGetWarnings:
    @pytest.mark.positive
    def test_returns_warnings(self, capture, mock_driver):
        logs = [
            {'level': 'SEVERE', 'message': 'err'},
            {'level': 'WARNING', 'message': 'warn'},
        ]
        mock_driver.get_log.return_value = logs
        result = capture.get_warnings()
        assert len(result) == 1


class TestHasErrors:
    @pytest.mark.positive
    def test_has_errors(self, capture, mock_driver):
        mock_driver.get_log.return_value = [{'level': 'SEVERE', 'message': 'err'}]
        assert capture.has_errors() is True

    @pytest.mark.positive
    def test_no_errors(self, capture, mock_driver):
        mock_driver.get_log.return_value = []
        assert capture.has_errors() is False


class TestHistory:
    @pytest.mark.positive
    def test_get_history(self, capture, mock_driver):
        mock_driver.get_log.return_value = [{'level': 'INFO', 'message': 'a'}]
        capture.get_logs()
        assert len(capture.get_history()) == 1

    @pytest.mark.positive
    def test_clear_history(self, capture, mock_driver):
        mock_driver.get_log.return_value = [{'level': 'INFO', 'message': 'a'}]
        capture.get_logs()
        capture.clear_history()
        assert len(capture.get_history()) == 0

    @pytest.mark.positive
    def test_history_is_copy(self, capture, mock_driver):
        mock_driver.get_log.return_value = [{'level': 'INFO', 'message': 'a'}]
        capture.get_logs()
        history = capture.get_history()
        history.clear()
        assert len(capture.get_history()) == 1


class TestSaveLogs:
    @pytest.mark.positive
    def test_saves_file(self, capture, mock_driver):
        mock_driver.get_log.return_value = [{'level': 'SEVERE', 'message': 'err'}]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'logs.json')
            result = capture.save_logs(path)
            assert result == path
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert len(data) == 1


class TestAssertNoErrors:
    @pytest.mark.positive
    def test_no_errors(self, capture, mock_driver):
        mock_driver.get_log.return_value = []
        capture.assert_no_errors()

    @pytest.mark.negative
    def test_with_errors(self, capture, mock_driver):
        mock_driver.get_log.return_value = [{'level': 'SEVERE', 'message': 'JS error'}]
        with pytest.raises(AssertionError, match='JavaScript 錯誤'):
            capture.assert_no_errors()
