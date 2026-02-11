"""
BasePage 單元測試

用 Mock WebDriver 驗證 BasePage 所有方法的行為，
確保後續改動不破壞核心邏輯。
"""

from unittest.mock import MagicMock, patch, PropertyMock
import pytest
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import NoSuchElementException

from pages.base_page import BasePage


@pytest.fixture
def mock_driver():
    driver = MagicMock()
    driver.title = '測試頁面'
    driver.current_url = 'https://example.com/page'
    driver.page_source = '<html></html>'
    driver.window_handles = ['handle_0', 'handle_1']
    return driver


@pytest.fixture
def page(mock_driver):
    return BasePage(mock_driver)


@pytest.fixture
def mock_snapshot():
    return MagicMock()


# === 建構 ===

class TestInit:
    def test_init_default(self, mock_driver):
        page = BasePage(mock_driver)
        assert page.driver is mock_driver
        assert page._snapshot is None

    def test_init_with_snapshot(self, mock_driver, mock_snapshot):
        page = BasePage(mock_driver, snapshot=mock_snapshot)
        assert page._snapshot is mock_snapshot

    def test_enable_snapshot(self, page, mock_snapshot):
        page.enable_snapshot(mock_snapshot)
        assert page._snapshot is mock_snapshot


# === 快照 ===

class TestSnapshot:
    def test_take_snapshot_when_enabled(self, page, mock_snapshot):
        page.enable_snapshot(mock_snapshot)
        page._take_snapshot('test_label')
        mock_snapshot.take.assert_called_once_with('test_label')

    def test_take_snapshot_when_disabled(self, page):
        # 沒有啟用快照時不應報錯
        page._take_snapshot('test_label')

    def test_open_triggers_snapshot(self, page, mock_snapshot):
        page.enable_snapshot(mock_snapshot)
        page.open('https://example.com')
        mock_snapshot.take.assert_called_with('open')

    def test_click_triggers_snapshot(self, page, mock_snapshot):
        page.enable_snapshot(mock_snapshot)
        with patch.object(page, 'wait_for_clickable', return_value=MagicMock()):
            page.click(By.ID, 'btn')
        mock_snapshot.take.assert_called_with('click_btn')

    def test_input_text_triggers_snapshot(self, page, mock_snapshot):
        page.enable_snapshot(mock_snapshot)
        with patch.object(page, 'wait_for_visible', return_value=MagicMock()):
            page.input_text(By.ID, 'email', 'test@mail.com')
        mock_snapshot.take.assert_called_with('input_email')


# === 導航 ===

class TestNavigation:
    def test_open(self, page, mock_driver):
        page.open('https://example.com')
        mock_driver.get.assert_called_once_with('https://example.com')

    def test_get_title(self, page):
        assert page.get_title() == '測試頁面'

    def test_get_current_url(self, page):
        assert page.get_current_url() == 'https://example.com/page'

    def test_refresh(self, page, mock_driver):
        page.refresh()
        mock_driver.refresh.assert_called_once()

    def test_go_back(self, page, mock_driver):
        page.go_back()
        mock_driver.back.assert_called_once()


# === 元素查找 ===

class TestFindElement:
    def test_find_element(self, page, mock_driver):
        mock_el = MagicMock()
        mock_driver.find_element.return_value = mock_el
        result = page.find_element(By.ID, 'test')
        mock_driver.find_element.assert_called_once_with(By.ID, 'test')
        assert result is mock_el

    def test_find_elements(self, page, mock_driver):
        mock_els = [MagicMock(), MagicMock()]
        mock_driver.find_elements.return_value = mock_els
        result = page.find_elements(By.CSS_SELECTOR, '.item')
        assert result == mock_els

    def test_is_element_present_true(self, page, mock_driver):
        mock_driver.find_elements.return_value = [MagicMock()]
        assert page.is_element_present(By.ID, 'exists') is True

    def test_is_element_present_false(self, page, mock_driver):
        mock_driver.find_elements.return_value = []
        assert page.is_element_present(By.ID, 'missing') is False


# === 元素互動 ===

class TestInteraction:
    def test_click(self, page):
        mock_el = MagicMock()
        with patch.object(page, 'wait_for_clickable', return_value=mock_el):
            page.click(By.ID, 'btn')
        mock_el.click.assert_called_once()

    def test_input_text_with_clear(self, page):
        mock_el = MagicMock()
        with patch.object(page, 'wait_for_visible', return_value=mock_el):
            page.input_text(By.ID, 'email', 'test@mail.com')
        mock_el.clear.assert_called_once()
        mock_el.send_keys.assert_called_once_with('test@mail.com')

    def test_input_text_without_clear(self, page):
        mock_el = MagicMock()
        with patch.object(page, 'wait_for_visible', return_value=mock_el):
            page.input_text(By.ID, 'email', 'append', clear_first=False)
        mock_el.clear.assert_not_called()
        mock_el.send_keys.assert_called_once_with('append')

    def test_clear_and_type(self, page):
        mock_el = MagicMock()
        with patch.object(page, 'wait_for_visible', return_value=mock_el):
            page.clear_and_type(By.ID, 'field', 'new_text')
        assert mock_el.send_keys.call_count == 3  # ctrl+a, delete, new_text

    def test_get_element_text(self, page):
        mock_el = MagicMock()
        mock_el.text = '文字內容'
        with patch.object(page, 'wait_for_visible', return_value=mock_el):
            result = page.get_element_text(By.ID, 'label')
        assert result == '文字內容'

    def test_get_element_attribute(self, page):
        mock_el = MagicMock()
        mock_el.get_attribute.return_value = 'attr_value'
        with patch.object(page, 'wait_for_element', return_value=mock_el):
            result = page.get_element_attribute(By.ID, 'el', 'href')
        mock_el.get_attribute.assert_called_once_with('href')
        assert result == 'attr_value'

    def test_get_input_value(self, page):
        with patch.object(page, 'get_element_attribute', return_value='input_val') as mock:
            result = page.get_input_value(By.ID, 'field')
        mock.assert_called_once_with(By.ID, 'field', 'value')
        assert result == 'input_val'


# === 下拉選單 ===

class TestSelect:
    def test_select_by_value(self, page, mock_snapshot):
        mock_el = MagicMock()
        # mock <select> element 需要有 tag_name
        mock_el.tag_name = 'select'
        mock_el.get_attribute.return_value = 'false'
        mock_option = MagicMock()
        mock_option.is_enabled.return_value = True
        mock_el.find_elements.return_value = [mock_option]
        with patch.object(page, 'wait_for_visible', return_value=mock_el):
            with patch('pages.base_page.Select') as MockSelect:
                page.select_by_value(By.ID, 'dropdown', 'opt1')
                MockSelect.assert_called_once_with(mock_el)

    def test_select_by_text(self, page):
        mock_el = MagicMock()
        mock_el.tag_name = 'select'
        with patch.object(page, 'wait_for_visible', return_value=mock_el):
            with patch('pages.base_page.Select') as MockSelect:
                page.select_by_text(By.ID, 'dropdown', '選項一')
                MockSelect.assert_called_once_with(mock_el)

    def test_select_by_index(self, page):
        mock_el = MagicMock()
        mock_el.tag_name = 'select'
        with patch.object(page, 'wait_for_visible', return_value=mock_el):
            with patch('pages.base_page.Select') as MockSelect:
                page.select_by_index(By.ID, 'dropdown', 0)
                MockSelect.assert_called_once_with(mock_el)


# === Checkbox / Radio ===

class TestCheckbox:
    def test_is_selected(self, page, mock_driver):
        mock_el = MagicMock()
        mock_el.is_selected.return_value = True
        mock_driver.find_element.return_value = mock_el
        assert page.is_selected(By.ID, 'cb') is True

    def test_set_checkbox_check(self, page):
        mock_el = MagicMock()
        mock_el.is_selected.return_value = False
        with patch.object(page, 'wait_for_clickable', return_value=mock_el):
            page.set_checkbox(By.ID, 'cb', checked=True)
        mock_el.click.assert_called_once()

    def test_set_checkbox_already_checked(self, page):
        mock_el = MagicMock()
        mock_el.is_selected.return_value = True
        with patch.object(page, 'wait_for_clickable', return_value=mock_el):
            page.set_checkbox(By.ID, 'cb', checked=True)
        mock_el.click.assert_not_called()

    def test_set_checkbox_uncheck(self, page):
        mock_el = MagicMock()
        mock_el.is_selected.return_value = True
        with patch.object(page, 'wait_for_clickable', return_value=mock_el):
            page.set_checkbox(By.ID, 'cb', checked=False)
        mock_el.click.assert_called_once()


# === 滾動 ===

class TestScroll:
    def test_scroll_to_element(self, page, mock_driver):
        mock_el = MagicMock()
        mock_driver.find_element.return_value = mock_el
        result = page.scroll_to_element(By.ID, 'target')
        mock_driver.execute_script.assert_called_once()
        assert result is mock_el

    def test_scroll_to_bottom(self, page, mock_driver):
        page.scroll_to_bottom()
        mock_driver.execute_script.assert_called_once()

    def test_scroll_to_top(self, page, mock_driver):
        page.scroll_to_top()
        mock_driver.execute_script.assert_called_once()


# === iframe / Alert / 視窗 ===

class TestFrameAlertWindow:
    def test_switch_to_iframe(self, page, mock_driver):
        mock_iframe = MagicMock()
        with patch.object(page, 'wait_for_element', return_value=mock_iframe):
            page.switch_to_iframe(By.ID, 'frame1')
        mock_driver.switch_to.frame.assert_called_once_with(mock_iframe)

    def test_switch_to_default(self, page, mock_driver):
        page.switch_to_default()
        mock_driver.switch_to.default_content.assert_called_once()

    def test_switch_to_window(self, page, mock_driver):
        page.switch_to_window(-1)
        mock_driver.switch_to.window.assert_called_once_with('handle_1')

    def test_switch_to_window_first(self, page, mock_driver):
        page.switch_to_window(0)
        mock_driver.switch_to.window.assert_called_once_with('handle_0')


# === 滑鼠操作 ===

class TestMouse:
    @patch('pages.base_page.ActionChains')
    def test_hover(self, MockAC, page):
        mock_el = MagicMock()
        with patch.object(page, 'wait_for_visible', return_value=mock_el):
            page.hover(By.ID, 'menu')
        MockAC.return_value.move_to_element.assert_called_once_with(mock_el)

    @patch('pages.base_page.ActionChains')
    def test_double_click(self, MockAC, page):
        mock_el = MagicMock()
        with patch.object(page, 'wait_for_clickable', return_value=mock_el):
            page.double_click(By.ID, 'item')
        MockAC.return_value.double_click.assert_called_once_with(mock_el)

    @patch('pages.base_page.ActionChains')
    def test_right_click(self, MockAC, page):
        mock_el = MagicMock()
        with patch.object(page, 'wait_for_clickable', return_value=mock_el):
            page.right_click(By.ID, 'item')
        MockAC.return_value.context_click.assert_called_once_with(mock_el)


# === JavaScript ===

class TestJavaScript:
    def test_execute_js(self, page, mock_driver):
        mock_driver.execute_script.return_value = 42
        result = page.execute_js('return 42')
        mock_driver.execute_script.assert_called_with('return 42')
        assert result == 42

    def test_js_click(self, page, mock_driver):
        mock_el = MagicMock()
        mock_driver.find_element.return_value = mock_el
        page.js_click(By.ID, 'btn')
        mock_driver.execute_script.assert_called_once()


# === 元素狀態 ===

class TestElementState:
    def test_is_enabled(self, page, mock_driver):
        mock_el = MagicMock()
        mock_el.is_enabled.return_value = True
        mock_driver.find_element.return_value = mock_el
        assert page.is_enabled(By.ID, 'btn') is True

    def test_is_displayed_true(self, page, mock_driver):
        mock_el = MagicMock()
        mock_el.is_displayed.return_value = True
        mock_driver.find_element.return_value = mock_el
        assert page.is_displayed(By.ID, 'el') is True

    def test_is_displayed_false_on_exception(self, page, mock_driver):
        mock_driver.find_element.side_effect = NoSuchElementException()
        assert page.is_displayed(By.ID, 'missing') is False

    def test_get_elements_text(self, page, mock_driver):
        el1 = MagicMock()
        el1.text = 'A'
        el2 = MagicMock()
        el2.text = 'B'
        mock_driver.find_elements.return_value = [el1, el2]
        assert page.get_elements_text(By.CSS_SELECTOR, '.item') == ['A', 'B']

    def test_get_element_count(self, page, mock_driver):
        mock_driver.find_elements.return_value = [MagicMock()] * 5
        assert page.get_element_count(By.CSS_SELECTOR, '.item') == 5

    def test_get_element_count_zero(self, page, mock_driver):
        mock_driver.find_elements.return_value = []
        assert page.get_element_count(By.CSS_SELECTOR, '.none') == 0
