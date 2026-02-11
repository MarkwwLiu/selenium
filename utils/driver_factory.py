"""
WebDriver 工廠模式

根據設定檔建立對應的瀏覽器 WebDriver，支援：
- Chrome / Firefox / Edge
- Headless 模式（無頭模式，適用於 CI/CD）
"""

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from selenium.webdriver.firefox.service import Service as FirefoxService
from selenium.webdriver.edge.service import Service as EdgeService
from webdriver_manager.chrome import ChromeDriverManager
from webdriver_manager.firefox import GeckoDriverManager
from webdriver_manager.microsoft import EdgeChromiumDriverManager


class DriverFactory:
    """根據瀏覽器類型與設定建立 WebDriver 實例。"""

    @staticmethod
    def create_driver(browser='chrome', headless=False):
        """
        建立並回傳 WebDriver。

        Args:
            browser: 瀏覽器類型 ('chrome', 'firefox', 'edge')
            headless: 是否啟用無頭模式

        Returns:
            WebDriver 實例
        """
        browser = browser.lower()

        if browser == 'chrome':
            return DriverFactory._create_chrome(headless)
        elif browser == 'firefox':
            return DriverFactory._create_firefox(headless)
        elif browser == 'edge':
            return DriverFactory._create_edge(headless)
        else:
            raise ValueError(f'不支援的瀏覽器類型: {browser}（支援: chrome, firefox, edge）')

    @staticmethod
    def _create_chrome(headless=False):
        options = webdriver.ChromeOptions()
        if headless:
            options.add_argument('--headless=new')
            options.add_argument('--no-sandbox')
            options.add_argument('--disable-dev-shm-usage')
        service = ChromeService(ChromeDriverManager().install())
        return webdriver.Chrome(service=service, options=options)

    @staticmethod
    def _create_firefox(headless=False):
        options = webdriver.FirefoxOptions()
        if headless:
            options.add_argument('--headless')
        service = FirefoxService(GeckoDriverManager().install())
        return webdriver.Firefox(service=service, options=options)

    @staticmethod
    def _create_edge(headless=False):
        options = webdriver.EdgeOptions()
        if headless:
            options.add_argument('--headless=new')
        service = EdgeService(EdgeChromiumDriverManager().install())
        return webdriver.Edge(service=service, options=options)
