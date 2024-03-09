import os
from BeautifulReport import BeautifulReport
from selenium import webdriver
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import unittest
import time

class OpenWeb(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        """
        安裝最新版本的 ChromeDriver 並啟動 Chrome 瀏覽器。
        將其指定給類別屬性 'driver'。
        """
        cls.driver = webdriver.Chrome(ChromeDriverManager().install())

    @classmethod
    def tearDownClass(cls):
        """
        關閉 Chrome 瀏覽器。
        """
        cls.driver.quit()

    def setUp(self):
        """
        打開網站並找到標題元素。
        將其指定給實例屬性 'title_element'。
        """
        self.driver.get('https://shareboxnow.com/')
        self.title_element = self.driver.find_element(by=By.CSS_SELECTOR, value='.entry-title-link')

    def tearDown(self):
        """
        等待幾秒，然後關閉 Chrome 瀏覽器。
        """
        time.sleep(3)

    """
    只要類別內 def 開頭符合 test 的就會被列入到測試項目
    如果不符合就不會執行
    """
    def test_open_shareboxnow_pass(self):
        """
        檢查標題 - 通過
        """
        self.assertEqual(self.title_element.text, '【2024】多種優惠商品資訊，千萬別錯過！', '名稱有誤')

    def test_open_shareboxnow_fail(self):
        """
        檢查標題 - 失敗
        """
        self.assertEqual(self.title_element.text, '【2024】多種優惠商品資訊，千萬別錯過q！', '名稱有誤')


if __name__ == '__main__':
    suite = unittest.TestLoader().loadTestsFromTestCase(OpenWeb)
    result = BeautifulReport(suite)
    result.report(filename='Demo_BeautifulReport', description='default description', report_dir=os.getcwd() + '/')
