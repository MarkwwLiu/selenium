"""
screenshot 和 logger 單元測試
"""

import logging
import os
from unittest.mock import MagicMock
import pytest

from utils.screenshot import take_screenshot
from utils.logger import setup_logger


class TestTakeScreenshot:
    def test_creates_directory(self, tmp_path):
        driver = MagicMock()
        driver.save_screenshot.return_value = True
        save_dir = str(tmp_path / 'new_dir')
        take_screenshot(driver, save_dir, 'test_case')
        assert os.path.isdir(save_dir)

    def test_calls_save_screenshot(self, tmp_path):
        driver = MagicMock()
        driver.save_screenshot.return_value = True
        take_screenshot(driver, str(tmp_path), 'test_case')
        driver.save_screenshot.assert_called_once()

    def test_returns_filepath(self, tmp_path):
        driver = MagicMock()
        driver.save_screenshot.return_value = True
        result = take_screenshot(driver, str(tmp_path), 'test_case')
        assert result.endswith('.png')
        assert 'test_case' in result

    def test_filename_contains_test_name(self, tmp_path):
        driver = MagicMock()
        driver.save_screenshot.return_value = True
        result = take_screenshot(driver, str(tmp_path), 'my_test_name')
        assert 'my_test_name' in os.path.basename(result)


class TestSetupLogger:
    def test_returns_logger(self):
        logger = setup_logger(name='test_unit_logger_1')
        assert isinstance(logger, logging.Logger)
        assert logger.name == 'test_unit_logger_1'
        # cleanup
        logger.handlers.clear()

    def test_console_handler_present(self):
        logger = setup_logger(name='test_unit_logger_2')
        handler_types = [type(h) for h in logger.handlers]
        assert logging.StreamHandler in handler_types
        logger.handlers.clear()

    def test_file_handler_when_log_dir(self, tmp_path):
        logger = setup_logger(name='test_unit_logger_3', log_dir=str(tmp_path))
        handler_types = [type(h) for h in logger.handlers]
        assert logging.FileHandler in handler_types
        # 確認日誌檔案被建立
        log_files = [f for f in os.listdir(str(tmp_path)) if f.endswith('.log')]
        assert len(log_files) == 1
        logger.handlers.clear()

    def test_no_file_handler_without_log_dir(self):
        logger = setup_logger(name='test_unit_logger_4', log_dir=None)
        handler_types = [type(h) for h in logger.handlers]
        assert logging.FileHandler not in handler_types
        logger.handlers.clear()

    def test_no_duplicate_handlers(self):
        """重複呼叫不應加入重複的 handler。"""
        logger = setup_logger(name='test_unit_logger_5')
        handler_count = len(logger.handlers)
        setup_logger(name='test_unit_logger_5')
        assert len(logger.handlers) == handler_count
        logger.handlers.clear()

    def test_log_level(self):
        logger = setup_logger(name='test_unit_logger_6')
        assert logger.level == logging.DEBUG
        logger.handlers.clear()
