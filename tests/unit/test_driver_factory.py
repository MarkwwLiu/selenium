"""
utils/driver_factory.py 單元測試
"""

from unittest.mock import patch, MagicMock
import pytest
from utils.driver_factory import DriverFactory


class TestCreateDriver:
    @pytest.mark.positive
    @patch('utils.driver_factory.webdriver.Chrome')
    @patch('utils.driver_factory.ChromeDriverManager')
    @patch('utils.driver_factory.ChromeService')
    def test_chrome_default(self, MockService, MockManager, MockChrome):
        MockManager.return_value.install.return_value = '/path/chromedriver'
        driver = DriverFactory.create_driver('chrome', headless=False)
        MockChrome.assert_called_once()
        assert driver is MockChrome.return_value

    @pytest.mark.positive
    @patch('utils.driver_factory.webdriver.Chrome')
    @patch('utils.driver_factory.ChromeDriverManager')
    @patch('utils.driver_factory.ChromeService')
    def test_chrome_headless(self, MockService, MockManager, MockChrome):
        MockManager.return_value.install.return_value = '/path/chromedriver'
        DriverFactory.create_driver('chrome', headless=True)
        MockChrome.assert_called_once()

    @pytest.mark.positive
    @patch('utils.driver_factory.webdriver.Firefox')
    @patch('utils.driver_factory.GeckoDriverManager')
    @patch('utils.driver_factory.FirefoxService')
    def test_firefox(self, MockService, MockManager, MockFirefox):
        MockManager.return_value.install.return_value = '/path/geckodriver'
        driver = DriverFactory.create_driver('firefox')
        MockFirefox.assert_called_once()
        assert driver is MockFirefox.return_value

    @pytest.mark.positive
    @patch('utils.driver_factory.webdriver.Firefox')
    @patch('utils.driver_factory.GeckoDriverManager')
    @patch('utils.driver_factory.FirefoxService')
    def test_firefox_headless(self, MockService, MockManager, MockFirefox):
        MockManager.return_value.install.return_value = '/path/geckodriver'
        DriverFactory.create_driver('firefox', headless=True)
        MockFirefox.assert_called_once()

    @pytest.mark.positive
    @patch('utils.driver_factory.webdriver.Edge')
    @patch('utils.driver_factory.EdgeChromiumDriverManager')
    @patch('utils.driver_factory.EdgeService')
    def test_edge(self, MockService, MockManager, MockEdge):
        MockManager.return_value.install.return_value = '/path/edgedriver'
        driver = DriverFactory.create_driver('edge')
        MockEdge.assert_called_once()
        assert driver is MockEdge.return_value

    @pytest.mark.positive
    @patch('utils.driver_factory.webdriver.Edge')
    @patch('utils.driver_factory.EdgeChromiumDriverManager')
    @patch('utils.driver_factory.EdgeService')
    def test_edge_headless(self, MockService, MockManager, MockEdge):
        MockManager.return_value.install.return_value = '/path/edgedriver'
        DriverFactory.create_driver('edge', headless=True)
        MockEdge.assert_called_once()

    @pytest.mark.negative
    def test_unsupported_browser(self):
        with pytest.raises(ValueError, match='不支援的瀏覽器類型'):
            DriverFactory.create_driver('safari')

    @pytest.mark.positive
    @patch('utils.driver_factory.webdriver.Chrome')
    @patch('utils.driver_factory.ChromeDriverManager')
    @patch('utils.driver_factory.ChromeService')
    def test_case_insensitive(self, MockService, MockManager, MockChrome):
        MockManager.return_value.install.return_value = '/path/chromedriver'
        DriverFactory.create_driver('CHROME')
        MockChrome.assert_called_once()
