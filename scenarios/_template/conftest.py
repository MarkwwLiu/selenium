"""
情境模組專屬 conftest.py（模板）

由 generate_scenario.py 複製後自動配置。
職責：
1. 將專案根目錄加入 sys.path（讓 import 核心模組可用）
2. 提供情境專屬的 fixture（driver、logger、snapshot、analyzer）
3. 截圖與報告輸出到情境自己的 results/ 目錄
"""

import os
import sys
import time
import pytest

# === 路徑設定 ===
SCENARIO_DIR = os.path.dirname(os.path.abspath(__file__))
SCENARIO_NAME = os.path.basename(SCENARIO_DIR)
RESULTS_DIR = os.path.join(SCENARIO_DIR, 'results')
SNAPSHOTS_DIR = os.path.join(RESULTS_DIR, 'snapshots')

ROOT_DIR = os.path.abspath(os.path.join(SCENARIO_DIR, '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config.settings import BROWSER, HEADLESS, IMPLICIT_WAIT, TEARDOWN_WAIT, LOG_ENABLED
from utils.driver_factory import DriverFactory
from utils.screenshot import take_screenshot
from utils.logger import setup_logger
from utils.waiter import Waiter
from utils.page_snapshot import PageSnapshot
from utils.page_analyzer import PageAnalyzer

# === 情境參數（產生器會覆寫這裡）===
SCENARIO_URL = ''


# === Fixtures ===

@pytest.fixture(scope='session')
def logger():
    """情境專屬 Logger，日誌寫入 results/ 目錄。"""
    log_dir = RESULTS_DIR if LOG_ENABLED else None
    return setup_logger(name=f'scenario_{SCENARIO_NAME}', log_dir=log_dir)


@pytest.fixture(scope='session')
def driver(request, logger):
    """Session 層級 WebDriver，整個情境共用一個瀏覽器。"""
    browser = request.config.getoption('--browser', default=None) or BROWSER
    headless = request.config.getoption('--headless-mode', default=False) or HEADLESS

    logger.info(f'===== 情境 [{SCENARIO_NAME}] 啟動 =====')
    logger.info(f'瀏覽器: {browser} | Headless: {headless}')

    _driver = DriverFactory.create_driver(browser=browser, headless=headless)
    _driver.implicitly_wait(IMPLICIT_WAIT)
    logger.info('WebDriver 初始化完成')

    yield _driver

    _driver.quit()
    logger.info(f'===== 情境 [{SCENARIO_NAME}] 結束 =====\n')


@pytest.fixture(scope='session')
def waiter(driver):
    """進階等待工具 fixture。"""
    return Waiter(driver)


@pytest.fixture(scope='session')
def analyzer(driver):
    """頁面元素分析器 fixture。"""
    return PageAnalyzer(driver)


@pytest.fixture
def snapshot(driver):
    """
    每個測試獨立的快照管理器。
    快照存到 results/snapshots/{測試名稱}/ 目錄下。
    """
    test_name = os.environ.get('PYTEST_CURRENT_TEST', 'unknown').split('::')[-1].split(' ')[0]
    snap_dir = os.path.join(SNAPSHOTS_DIR, test_name)
    snap = PageSnapshot(driver, snap_dir)
    yield snap
    snap.save_timeline()


@pytest.fixture
def scenario_url():
    """取得此情境的目標 URL。"""
    return SCENARIO_URL


@pytest.hookimpl(tryfirst=True, hookwrapper=True)
def pytest_runtest_makereport(item, call):
    """將每個測試階段的結果附加到 item 上。"""
    outcome = yield
    report = outcome.get_result()
    setattr(item, f'rep_{report.when}', report)


@pytest.fixture(autouse=True)
def test_lifecycle(request, driver, logger):
    """
    自動套用：紀錄測試開始、失敗截圖到情境 results/、紀錄結果。
    """
    test_name = request.node.name
    os.environ['PYTEST_CURRENT_TEST'] = f'{request.node.nodeid} (call)'
    logger.info(f'▶ 執行: {test_name}')

    yield

    rep_call = getattr(request.node, 'rep_call', None)
    if rep_call and rep_call.failed:
        filepath = take_screenshot(driver, RESULTS_DIR, test_name)
        logger.warning(f'✘ 失敗: {test_name} → 截圖: {filepath}')
    else:
        logger.info(f'✔ 通過: {test_name}')

    time.sleep(TEARDOWN_WAIT)
