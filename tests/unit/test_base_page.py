"""
BasePage 單元測試

用 Mock WebDriver 驗證 BasePage 所有方法的行為，
確保後續改動不破壞核心邏輯。
"""

import os
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


# === 等待策略 ===

class TestWaitStrategies:
    @pytest.mark.positive
    @patch('pages.base_page.WebDriverWait')
    def test_wait_for_element(self, MockWait, page):
        mock_el = MagicMock()
        MockWait.return_value.until.return_value = mock_el
        result = page.wait_for_element(By.ID, 'el')
        assert result is mock_el

    @pytest.mark.positive
    @patch('pages.base_page.WebDriverWait')
    def test_wait_for_visible(self, MockWait, page):
        mock_el = MagicMock()
        MockWait.return_value.until.return_value = mock_el
        result = page.wait_for_visible(By.ID, 'el')
        assert result is mock_el

    @pytest.mark.positive
    @patch('pages.base_page.WebDriverWait')
    def test_wait_for_clickable(self, MockWait, page):
        mock_el = MagicMock()
        MockWait.return_value.until.return_value = mock_el
        result = page.wait_for_clickable(By.ID, 'btn')
        assert result is mock_el

    @pytest.mark.positive
    @patch('pages.base_page.WebDriverWait')
    def test_wait_for_invisible(self, MockWait, page):
        MockWait.return_value.until.return_value = True
        result = page.wait_for_invisible(By.ID, 'spinner')
        assert result is True

    @pytest.mark.positive
    @patch('pages.base_page.WebDriverWait')
    def test_wait_for_text_present(self, MockWait, page):
        MockWait.return_value.until.return_value = True
        result = page.wait_for_text_present(By.ID, 'msg', 'hello')
        assert result is True

    @pytest.mark.positive
    @patch('pages.base_page.WebDriverWait')
    def test_wait_for_url_contains(self, MockWait, page):
        MockWait.return_value.until.return_value = True
        result = page.wait_for_url_contains('/dashboard')
        assert result is True


# === Alert ===

class TestAlert:
    @pytest.mark.positive
    @patch('pages.base_page.WebDriverWait')
    def test_accept_alert(self, MockWait, page, mock_driver):
        MockWait.return_value.until.return_value = True
        page.accept_alert()
        mock_driver.switch_to.alert.accept.assert_called_once()

    @pytest.mark.positive
    @patch('pages.base_page.WebDriverWait')
    def test_dismiss_alert(self, MockWait, page, mock_driver):
        MockWait.return_value.until.return_value = True
        page.dismiss_alert()
        mock_driver.switch_to.alert.dismiss.assert_called_once()

    @pytest.mark.positive
    @patch('pages.base_page.WebDriverWait')
    def test_get_alert_text(self, MockWait, page, mock_driver):
        MockWait.return_value.until.return_value = True
        mock_driver.switch_to.alert.text = '確認刪除？'
        result = page.get_alert_text()
        assert result == '確認刪除？'


# === 檔案上傳 ===

class TestUpload:
    @pytest.mark.positive
    def test_upload_file_absolute_path(self, page):
        mock_el = MagicMock()
        with patch.object(page, 'wait_for_element', return_value=mock_el):
            page.upload_file(By.ID, 'file', '/tmp/test.pdf')
        mock_el.send_keys.assert_called_once_with('/tmp/test.pdf')

    @pytest.mark.positive
    def test_upload_file_relative_path(self, page):
        mock_el = MagicMock()
        with patch.object(page, 'wait_for_element', return_value=mock_el):
            page.upload_file(By.ID, 'file', 'test.pdf')
        # 相對路徑會被轉成絕對路徑
        call_args = mock_el.send_keys.call_args[0][0]
        assert os.path.isabs(call_args)

    @pytest.mark.positive
    def test_upload_files(self, page):
        mock_el = MagicMock()
        with patch.object(page, 'wait_for_element', return_value=mock_el):
            page.upload_files(By.ID, 'file', ['/tmp/a.pdf', '/tmp/b.jpg'])
        mock_el.send_keys.assert_called_once_with('/tmp/a.pdf\n/tmp/b.jpg')

    @pytest.mark.positive
    def test_upload_files_relative_paths(self, page):
        mock_el = MagicMock()
        with patch.object(page, 'wait_for_element', return_value=mock_el):
            page.upload_files(By.ID, 'file', ['a.pdf', 'b.jpg'])
        call_args = mock_el.send_keys.call_args[0][0]
        for part in call_args.split('\n'):
            assert os.path.isabs(part)


# === 拖曳放置 ===

class TestDragAndDrop:
    @pytest.mark.positive
    @patch('pages.base_page.ActionChains')
    def test_drag_and_drop(self, MockAC, page):
        src = MagicMock()
        tgt = MagicMock()
        with patch.object(page, 'wait_for_visible', side_effect=[src, tgt]):
            page.drag_and_drop(By.ID, 'src', By.ID, 'tgt')
        MockAC.return_value.drag_and_drop.assert_called_once_with(src, tgt)

    @pytest.mark.positive
    @patch('pages.base_page.ActionChains')
    def test_drag_and_drop_by_offset(self, MockAC, page):
        mock_el = MagicMock()
        with patch.object(page, 'wait_for_visible', return_value=mock_el):
            page.drag_and_drop_by_offset(By.ID, 'slider', 100, 0)
        MockAC.return_value.drag_and_drop_by_offset.assert_called_once_with(mock_el, 100, 0)


# === 鍵盤操作 ===

class TestKeyboard:
    @pytest.mark.positive
    @patch('pages.base_page.ActionChains')
    def test_press_keys(self, MockAC, page):
        page.press_keys(Keys.ESCAPE)
        MockAC.return_value.send_keys.assert_called_once_with(Keys.ESCAPE)

    @pytest.mark.positive
    def test_send_keys_to_element(self, page):
        mock_el = MagicMock()
        with patch.object(page, 'wait_for_visible', return_value=mock_el):
            page.send_keys_to_element(By.ID, 'editor', Keys.CONTROL, 'c')
        mock_el.send_keys.assert_called_once_with(Keys.CONTROL, 'c')
