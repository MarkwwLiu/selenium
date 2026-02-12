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
    parser.addoption('--env', default=None, choices=['dev', 'staging', 'prod'],
                     help='指定測試環境（預設使用環境變數 TEST_ENV 或 dev）')


@pytest.fixture(scope='session')
def logger():
    """Session 層級的 Logger fixture。"""
    log_dir = LOGS_DIR if LOG_ENABLED else None
    return setup_logger(name='selenium_test', log_dir=log_dir)


@pytest.fixture(scope='session')
def env_config(request):
    """
    Session 層級的環境設定 fixture。

    Usage:
        def test_example(env_config):
            print(env_config['base_url'])  # 依環境取得對應 URL
    """
    from config.environments import get_env_config
    env_name = request.config.getoption('--env')
    return get_env_config(env_name)


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


@pytest.fixture(scope='session')
def waiter(driver):
    """
    Session 層級的進階等待工具 fixture。

    Usage:
        def test_example(waiter):
            waiter.wait_for_page_load()
            waiter.wait_for_ajax()
            waiter.wait_for_stable(By.ID, 'counter')
    """
    from utils.waiter import Waiter
    return Waiter(driver)


@pytest.fixture(scope='function')
def soft_assert():
    """
    Soft Assert fixture，每個測試自動取得新實例。

    Usage:
        def test_example(soft_assert):
            soft_assert.equal(title, '首頁')
            soft_assert.true(is_visible)
            soft_assert.assert_all()
    """
    from utils.soft_assert import SoftAssert
    return SoftAssert()


@pytest.fixture(scope='function')
def console_capture(driver):
    """
    Console 擷取 fixture。

    Usage:
        def test_example(console_capture):
            # ... 執行操作 ...
            console_capture.assert_no_errors()
    """
    from utils.console_capture import ConsoleCapture
    return ConsoleCapture(driver)


@pytest.fixture(scope='session')
def cookie_manager(driver):
    """
    Cookie 管理 fixture。

    Usage:
        def test_example(cookie_manager):
            cookie_manager.save_cookies('cookies/state.json')
    """
    from utils.cookie_manager import CookieManager
    return CookieManager(driver)


@pytest.fixture(scope='session')
def table_parser(driver):
    """
    Table 解析 fixture。

    Usage:
        def test_example(table_parser):
            data = table_parser.parse(By.ID, 'my-table')
    """
    from utils.table_parser import TableParser
    return TableParser(driver)


@pytest.fixture(scope='session')
def visual_regression(driver):
    """
    視覺回歸 fixture。

    Usage:
        def test_example(visual_regression):
            result = visual_regression.check('homepage')
            assert result['match']
    """
    from config.settings import BASELINES_DIR, DIFFS_DIR
    from utils.visual_regression import VisualRegression
    return VisualRegression(driver, baseline_dir=BASELINES_DIR, diff_dir=DIFFS_DIR)


@pytest.fixture(scope='session')
def network_interceptor(driver):
    """
    Network 攔截 fixture（僅限 Chrome/Edge）。

    Usage:
        def test_example(network_interceptor):
            network_interceptor.start_capture()
            # ... 操作頁面 ...
            assert network_interceptor.has_request('*/api/data*')
            network_interceptor.stop_capture()
    """
    from utils.network_interceptor import NetworkInterceptor
    interceptor = NetworkInterceptor(driver)
    yield interceptor
    try:
        interceptor.reset_network()
    except Exception:
        pass


@pytest.fixture(scope='function')
def data_factory():
    """
    測試資料工廠 fixture。

    Usage:
        def test_register(data_factory):
            user = data_factory.user()
            form = data_factory.form_data(['name', 'email', 'phone'])
    """
    from utils.data_factory import DataFactory
    return DataFactory(locale='zh_TW')


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
