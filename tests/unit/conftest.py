"""
Unit test 專屬 conftest.py

覆蓋根層級的 driver/logger fixture，
讓 unit test 不需要啟動真實瀏覽器。
"""

import pytest
from unittest.mock import MagicMock


@pytest.fixture(scope='session')
def driver():
    """Mock driver，unit test 不啟動真實瀏覽器。"""
    return MagicMock()


@pytest.fixture(scope='session')
def logger():
    """Mock logger。"""
    return MagicMock()
