"""
Demo 情境：Google 搜尋測試

示範如何用情境模組架構撰寫獨立測試。
所有截圖、日誌輸出到 scenarios/demo_search/results/。
"""

import os
import sys
import time
import pytest

# === 路徑設定 ===
SCENARIO_DIR = os.path.dirname(os.path.abspath(__file__))
SCENARIO_NAME = os.path.basename(SCENARIO_DIR)
RESULTS_DIR = os.path.join(SCENARIO_DIR, 'results')

ROOT_DIR = os.path.abspath(os.path.join(SCENARIO_DIR, '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config.settings import BROWSER, HEADLESS, IMPLICIT_WAIT, TEARDOWN_WAIT, LOG_ENABLED
from utils.driver_factory import DriverFactory
from utils.screenshot import take_screenshot
from utils.logger import setup_logger
from utils.waiter import Waiter

# === 情境參數 ===
SCENARIO_URL = 'https://www.google.com'


# === Fixtures ===

@pytest.fixture(scope='session')
def logger():
    log_dir = RESULTS_DIR if LOG_ENABLED else None
    return setup_logger(name=f'scenario_{SCENARIO_NAME}', log_dir=log_dir)


@pytest.fixture(scope='session')
def driver(request, logger):
    browser = request.config.getoption('--browser', default=None) or BROWSER
    headless = request.config.getoption('--headless-mode', default=False) or HEADLESS

    logger.info(f'===== 情境 [{SCENARIO_NAME}] 啟動 =====')
    _driver = DriverFactory.create_driver(browser=browser, headless=headless)
    _driver.implicitly_wait(IMPLICIT_WAIT)

    yield _driver

    _driver.quit()
    logger.info(f'===== 情境 [{SCENARIO_NAME}] 結束 =====\n')


@pytest.fixture(scope='session')
def waiter(driver):
    return Waiter(driver)


@pytest.fixture
def scenario_url():
    return SCENARIO_URL


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    outcome = yield
    report = outcome.get_result()
    setattr(item, f'rep_{report.when}', report)


@pytest.fixture(autouse=True)
def test_lifecycle(request, driver, logger):
    test_name = request.node.name
    logger.info(f'▶ 執行: {test_name}')

    yield

    rep_call = getattr(request.node, 'rep_call', None)
    if rep_call and rep_call.failed:
        filepath = take_screenshot(driver, RESULTS_DIR, test_name)
        logger.warning(f'✘ 失敗: {test_name} → 截圖: {filepath}')
    else:
        logger.info(f'✔ 通過: {test_name}')

    time.sleep(TEARDOWN_WAIT)
