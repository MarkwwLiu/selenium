"""
PageSnapshot 單元測試
"""

import json
import os
from unittest.mock import MagicMock
import pytest

from utils.page_snapshot import PageSnapshot


def _make_state(**overrides):
    """每次回傳一個新的 state dict，避免 mutable 共用問題。"""
    state = {
        'url': 'https://example.com',
        'title': 'Test',
        'scroll_y': 0,
        'viewport': {'width': 1920, 'height': 1080},
        'form_values': {'email': '', 'password': ''},
        'visible_element_count': 50,
        'alert_present': False,
    }
    state.update(overrides)
    return state


@pytest.fixture
def mock_driver():
    driver = MagicMock()
    driver.page_source = '<html><body>test</body></html>'
    # save_screenshot 實際建立空檔案
    def _save_screenshot(path):
        with open(path, 'wb') as f:
            f.write(b'fake_png')
        return True
    driver.save_screenshot.side_effect = _save_screenshot
    # 每次回傳新的 dict 避免共用參照
    driver.execute_script.side_effect = lambda *a, **kw: _make_state()
    return driver


@pytest.fixture
def snapshot(mock_driver, tmp_path):
    return PageSnapshot(mock_driver, str(tmp_path))


class TestTake:
    def test_creates_files(self, snapshot, tmp_path):
        snapshot.take('open')
        files = os.listdir(str(tmp_path))
        assert any('screenshot.png' in f for f in files)
        assert any('page.html' in f for f in files)
        assert any('state.json' in f for f in files)

    def test_step_counter_increments(self, snapshot):
        snapshot.take('step1')
        snapshot.take('step2')
        assert snapshot._step_counter == 2

    def test_returns_state_dict(self, snapshot):
        state = snapshot.take('open')
        assert state['label'] == 'open'
        assert state['step'] == '001'
        assert 'timestamp' in state
        assert 'screenshot' in state
        assert 'html' in state

    def test_html_content_saved(self, snapshot, tmp_path, mock_driver):
        snapshot.take('test')
        html_files = [f for f in os.listdir(str(tmp_path)) if f.endswith('_page.html')]
        assert len(html_files) == 1
        content = (tmp_path / html_files[0]).read_text(encoding='utf-8')
        assert content == mock_driver.page_source

    def test_state_json_saved(self, snapshot, tmp_path):
        snapshot.take('test')
        json_files = [f for f in os.listdir(str(tmp_path)) if f.endswith('_state.json')]
        assert len(json_files) == 1
        with open(tmp_path / json_files[0], 'r', encoding='utf-8') as f:
            state = json.load(f)
        assert state['url'] == 'https://example.com'

    def test_auto_numbering_without_label(self, snapshot, tmp_path):
        snapshot.take()
        files = os.listdir(str(tmp_path))
        # 沒有 label 時，prefix 只有 step_id '001'，檔名為 001_screenshot.png
        assert any(f == '001_screenshot.png' for f in files)


class TestHistory:
    def test_get_history(self, snapshot):
        snapshot.take('a')
        snapshot.take('b')
        history = snapshot.get_history()
        assert len(history) == 2
        assert history[0]['label'] == 'a'
        assert history[1]['label'] == 'b'

    def test_history_is_copy(self, snapshot):
        snapshot.take('a')
        history = snapshot.get_history()
        history.clear()
        assert len(snapshot.get_history()) == 1


class TestDiff:
    def test_diff_url_changed(self, snapshot, mock_driver):
        states = [
            _make_state(url='https://example.com/page1', title='Page 1', form_values={}),
            _make_state(url='https://example.com/page2', title='Page 2', form_values={}),
        ]
        mock_driver.execute_script.side_effect = states
        snapshot.take('step1')
        snapshot.take('step2')

        diff = snapshot.diff(0, 1)
        assert diff['url_changed'] is True
        assert diff['title_changed'] is True

    def test_diff_form_changes(self, snapshot, mock_driver):
        states = [
            _make_state(form_values={'email': ''}),
            _make_state(form_values={'email': 'user@mail.com'}),
        ]
        mock_driver.execute_script.side_effect = states
        snapshot.take('before')
        snapshot.take('after')

        diff = snapshot.diff(0, 1)
        assert 'email' in diff['form_changes']
        assert diff['form_changes']['email']['before'] == ''
        assert diff['form_changes']['email']['after'] == 'user@mail.com'

    def test_diff_out_of_range(self, snapshot):
        diff = snapshot.diff(0, 1)
        assert 'error' in diff


class TestTimeline:
    def test_save_timeline(self, snapshot, tmp_path):
        snapshot.take('a')
        snapshot.take('b')
        filepath = snapshot.save_timeline()
        assert os.path.exists(filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            timeline = json.load(f)
        assert timeline['total_steps'] == 2
        assert len(timeline['steps']) == 2
