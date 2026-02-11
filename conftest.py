"""
Pytest 共用 Fixtures

提供所有測試共用的 WebDriver、Logger、截圖等 fixture，
取代原本 unittest 的 BaseTest 類別。
"""

import time
import pytest

from config.settings import (
    BROWSER, HEADLESS, IMPLICIT_WAIT, TEARDOWN_WAIT,
    SCREENSHOTS_DIR, LOGS_DIR,
    SCREENSHOT_ON_FAILURE, LOG_ENABLED,
)
from utils.driver_factory import DriverFactory
from utils.screenshot import take_screenshot
from utils.logger import setup_logger


def pytest_addoption(parser):
    """註冊自訂命令列參數。"""
    parser.addoption('--browser', default=None, choices=['chrome', 'firefox', 'edge'],
                     help='指定瀏覽器（預設使用 config/settings.py 的設定）')
    parser.addoption('--headless-mode', action='store_true', default=False,
                     help='啟用無頭模式（不顯示瀏覽器視窗）')


@pytest.fixture(scope='session')
def logger():
    """Session 層級的 Logger fixture。"""
    log_dir = LOGS_DIR if LOG_ENABLED else None
    return setup_logger(name='selenium_test', log_dir=log_dir)


@pytest.fixture(scope='session')
def driver(request, logger):
    """
    Session 層級的 WebDriver fixture。

    整個測試 session 共用一個瀏覽器實例，結束後自動關閉。
    """
    browser = request.config.getoption('--browser') or BROWSER
    headless = request.config.getoption('--headless-mode') or HEADLESS

    logger.info(f'===== 啟動測試 Session =====')
    logger.info(f'瀏覽器: {browser} | Headless: {headless}')

    _driver = DriverFactory.create_driver(browser=browser, headless=headless)
    _driver.implicitly_wait(IMPLICIT_WAIT)
    logger.info('WebDriver 初始化完成')

    yield _driver

    _driver.quit()
    logger.info('===== 測試 Session 結束 =====\n')


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """將每個測試階段的結果附加到 item 上，供 fixture 使用。"""
    outcome = yield
    report = outcome.get_result()
    setattr(item, f'rep_{report.when}', report)


@pytest.fixture(autouse=True)
def test_lifecycle(request, driver, logger):
    """
    自動套用到每個測試的生命週期 fixture：
    - 前置：紀錄測試開始
    - 後置：失敗截圖 + 紀錄結果 + 等待
    """
    test_name = request.node.name
    logger.info(f'▶ 執行: {test_name}')

    yield

    # 檢查測試結果
    rep_call = getattr(request.node, 'rep_call', None)

    if rep_call and rep_call.failed:
        if SCREENSHOT_ON_FAILURE:
            filepath = take_screenshot(driver, SCREENSHOTS_DIR, test_name)
            logger.warning(f'✘ 失敗: {test_name} → 截圖已儲存: {filepath}')
        else:
            logger.warning(f'✘ 失敗: {test_name}')
    else:
        logger.info(f'✔ 通過: {test_name}')

    time.sleep(TEARDOWN_WAIT)
