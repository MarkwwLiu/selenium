"""
Page Object Model - 基礎頁面類別

所有頁面物件的父類別，提供共用的瀏覽器操作方法。
"""

from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys


class BasePage:
    """所有 Page Object 的基礎類別。"""

    def __init__(self, driver: WebDriver, snapshot=None):
        self.driver = driver
        self._snapshot = snapshot  # PageSnapshot 實例，設定後每步自動快照

    def enable_snapshot(self, snapshot):
        """啟用自動快照（傳入 PageSnapshot 實例）。"""
        self._snapshot = snapshot

    def _take_snapshot(self, label=''):
        """如果有啟用快照，自動擷取。"""
        if self._snapshot:
            self._snapshot.take(label)

    # === 導航 ===

    def open(self, url: str):
        """開啟指定的 URL。"""
        self.driver.get(url)
        self._take_snapshot('open')

    def get_title(self):
        """取得頁面標題 (browser tab title)。"""
        return self.driver.title

    def get_current_url(self):
        """取得當前頁面 URL。"""
        return self.driver.current_url

    def refresh(self):
        """重新整理頁面。"""
        self.driver.refresh()

    def go_back(self):
        """回到上一頁。"""
        self.driver.back()

    # === 元素查找 ===

    def find_element(self, by, value):
        """尋找單一元素。"""
        return self.driver.find_element(by, value)

    def find_elements(self, by, value):
        """尋找多個元素，回傳 list。"""
        return self.driver.find_elements(by, value)

    def is_element_present(self, by, value):
        """檢查元素是否存在（不等待）。"""
        return len(self.driver.find_elements(by, value)) > 0

    # === 等待策略 ===

    def wait_for_element(self, by, value, timeout=10):
        """等待元素出現在 DOM 中。"""
        return WebDriverWait(self.driver, timeout).until(
            EC.presence_of_element_located((by, value))
        )

    def wait_for_visible(self, by, value, timeout=10):
        """等待元素可見。"""
        return WebDriverWait(self.driver, timeout).until(
            EC.visibility_of_element_located((by, value))
        )

    def wait_for_clickable(self, by, value, timeout=10):
        """等待元素可點擊。"""
        return WebDriverWait(self.driver, timeout).until(
            EC.element_to_be_clickable((by, value))
        )

    def wait_for_invisible(self, by, value, timeout=10):
        """等待元素消失（例如 loading spinner）。"""
        return WebDriverWait(self.driver, timeout).until(
            EC.invisibility_of_element_located((by, value))
        )

    def wait_for_text_present(self, by, value, text, timeout=10):
        """等待元素包含指定文字。"""
        return WebDriverWait(self.driver, timeout).until(
            EC.text_to_be_present_in_element((by, value), text)
        )

    def wait_for_url_contains(self, text, timeout=10):
        """等待 URL 包含指定文字（用於頁面跳轉判斷）。"""
        return WebDriverWait(self.driver, timeout).until(
            EC.url_contains(text)
        )

    # === 元素互動 ===

    def click(self, by, value):
        """等待元素可點擊後點擊。"""
        self.wait_for_clickable(by, value).click()
        self._take_snapshot(f'click_{value}')

    def input_text(self, by, value, text, clear_first=True):
        """在輸入框中輸入文字。"""
        element = self.wait_for_visible(by, value)
        if clear_first:
            element.clear()
        element.send_keys(text)
        self._take_snapshot(f'input_{value}')

    def clear_and_type(self, by, value, text):
        """用全選+刪除的方式清除後輸入（處理 clear() 無效的情況）。"""
        element = self.wait_for_visible(by, value)
        element.send_keys(Keys.CONTROL + 'a')
        element.send_keys(Keys.DELETE)
        element.send_keys(text)

    def get_element_text(self, by, value):
        """取得指定元素的文字內容。"""
        return self.wait_for_visible(by, value).text

    def get_element_attribute(self, by, value, attribute):
        """取得元素的指定屬性值。"""
        return self.wait_for_element(by, value).get_attribute(attribute)

    def get_input_value(self, by, value):
        """取得輸入框的當前值。"""
        return self.get_element_attribute(by, value, 'value')

    # === 下拉選單 ===

    def select_by_value(self, by, value, option_value):
        """透過 value 選擇下拉選單選項。"""
        element = self.wait_for_visible(by, value)
        Select(element).select_by_value(option_value)
        self._take_snapshot(f'select_{value}')

    def select_by_text(self, by, value, visible_text):
        """透過顯示文字選擇下拉選單選項。"""
        element = self.wait_for_visible(by, value)
        Select(element).select_by_visible_text(visible_text)
        self._take_snapshot(f'select_{value}')

    def select_by_index(self, by, value, index):
        """透過索引選擇下拉選單選項。"""
        element = self.wait_for_visible(by, value)
        Select(element).select_by_index(index)
        self._take_snapshot(f'select_{value}')

    # === Checkbox / Radio ===

    def is_selected(self, by, value):
        """檢查 checkbox 或 radio 是否被選取。"""
        return self.find_element(by, value).is_selected()

    def set_checkbox(self, by, value, checked=True):
        """設定 checkbox 狀態。"""
        element = self.wait_for_clickable(by, value)
        if element.is_selected() != checked:
            element.click()

    # === 滾動 ===

    def scroll_to_element(self, by, value):
        """滾動到指定元素。"""
        element = self.find_element(by, value)
        self.driver.execute_script('arguments[0].scrollIntoView({block: "center"});', element)
        return element

    def scroll_to_bottom(self):
        """滾動到頁面底部。"""
        self.driver.execute_script('window.scrollTo(0, document.body.scrollHeight);')

    def scroll_to_top(self):
        """滾動到頁面頂部。"""
        self.driver.execute_script('window.scrollTo(0, 0);')

    # === iframe / Alert / 視窗 ===

    def switch_to_iframe(self, by, value):
        """切換到 iframe。"""
        iframe = self.wait_for_element(by, value)
        self.driver.switch_to.frame(iframe)

    def switch_to_default(self):
        """切回主頁面（離開 iframe）。"""
        self.driver.switch_to.default_content()

    def accept_alert(self):
        """接受 alert 彈窗。"""
        WebDriverWait(self.driver, 5).until(EC.alert_is_present())
        self.driver.switch_to.alert.accept()

    def dismiss_alert(self):
        """取消 alert 彈窗。"""
        WebDriverWait(self.driver, 5).until(EC.alert_is_present())
        self.driver.switch_to.alert.dismiss()

    def get_alert_text(self):
        """取得 alert 彈窗的文字。"""
        WebDriverWait(self.driver, 5).until(EC.alert_is_present())
        return self.driver.switch_to.alert.text

    def switch_to_window(self, index=-1):
        """切換到指定視窗（預設切到最後一個新開的）。"""
        handles = self.driver.window_handles
        self.driver.switch_to.window(handles[index])

    # === 滑鼠操作 ===

    def hover(self, by, value):
        """滑鼠移到元素上方（hover）。"""
        element = self.wait_for_visible(by, value)
        ActionChains(self.driver).move_to_element(element).perform()

    def double_click(self, by, value):
        """雙擊元素。"""
        element = self.wait_for_clickable(by, value)
        ActionChains(self.driver).double_click(element).perform()

    def right_click(self, by, value):
        """右鍵點擊元素。"""
        element = self.wait_for_clickable(by, value)
        ActionChains(self.driver).context_click(element).perform()

    # === JavaScript 執行 ===

    def execute_js(self, script, *args):
        """執行 JavaScript。"""
        return self.driver.execute_script(script, *args)

    def js_click(self, by, value):
        """透過 JavaScript 點擊（處理被遮擋的元素）。"""
        element = self.find_element(by, value)
        self.driver.execute_script('arguments[0].click();', element)

    # === 元素狀態 ===

    def is_enabled(self, by, value):
        """檢查元素是否啟用（非 disabled）。"""
        return self.find_element(by, value).is_enabled()

    def is_displayed(self, by, value):
        """檢查元素是否顯示在頁面上。"""
        try:
            return self.find_element(by, value).is_displayed()
        except Exception:
            return False

    def get_elements_text(self, by, value):
        """取得多個元素的文字，回傳 list。"""
        elements = self.find_elements(by, value)
        return [el.text for el in elements]

    def get_element_count(self, by, value):
        """取得符合條件的元素數量。"""
        return len(self.find_elements(by, value))
