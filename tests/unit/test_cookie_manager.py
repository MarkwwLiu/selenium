"""
utils/cookie_manager.py 單元測試
"""

import json
import os
import tempfile
from unittest.mock import MagicMock
import pytest

from utils.cookie_manager import CookieManager


@pytest.fixture
def mock_driver():
    return MagicMock()


@pytest.fixture
def cm(mock_driver):
    return CookieManager(mock_driver)


class TestGetCookie:
    @pytest.mark.positive
    def test_found(self, cm, mock_driver):
        mock_driver.get_cookie.return_value = {'name': 'token', 'value': 'abc'}
        result = cm.get_cookie('token')
        assert result['value'] == 'abc'
        mock_driver.get_cookie.assert_called_once_with('token')

    @pytest.mark.negative
    def test_not_found(self, cm, mock_driver):
        mock_driver.get_cookie.return_value = None
        assert cm.get_cookie('missing') is None


class TestGetAllCookies:
    @pytest.mark.positive
    def test_returns_list(self, cm, mock_driver):
        cookies = [{'name': 'a', 'value': '1'}, {'name': 'b', 'value': '2'}]
        mock_driver.get_cookies.return_value = cookies
        assert cm.get_all_cookies() == cookies


class TestAddCookie:
    @pytest.mark.positive
    def test_simple(self, cm, mock_driver):
        cm.add_cookie('token', 'abc123')
        mock_driver.add_cookie.assert_called_once_with({'name': 'token', 'value': 'abc123'})

    @pytest.mark.positive
    def test_with_kwargs(self, cm, mock_driver):
        cm.add_cookie('session', 'xyz', domain='.example.com', secure=True)
        expected = {'name': 'session', 'value': 'xyz', 'domain': '.example.com', 'secure': True}
        mock_driver.add_cookie.assert_called_once_with(expected)


class TestDeleteCookie:
    @pytest.mark.positive
    def test_delete(self, cm, mock_driver):
        cm.delete_cookie('token')
        mock_driver.delete_cookie.assert_called_once_with('token')


class TestDeleteAllCookies:
    @pytest.mark.positive
    def test_delete_all(self, cm, mock_driver):
        cm.delete_all_cookies()
        mock_driver.delete_all_cookies.assert_called_once()


class TestSaveCookies:
    @pytest.mark.positive
    def test_saves_file(self, cm, mock_driver):
        mock_driver.get_cookies.return_value = [{'name': 'a', 'value': '1'}]
        with tempfile.TemporaryDirectory() as tmpdir:
            path = os.path.join(tmpdir, 'cookies.json')
            result = cm.save_cookies(path)
            assert result == path
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert data == [{'name': 'a', 'value': '1'}]


class TestLoadCookies:
    @pytest.mark.positive
    def test_loads_file(self, cm, mock_driver):
        cookies = [{'name': 'a', 'value': '1'}, {'name': 'b', 'value': '2'}]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(cookies, f)
            path = f.name
        try:
            cm.load_cookies(path)
            assert mock_driver.add_cookie.call_count == 2
        finally:
            os.unlink(path)

    @pytest.mark.positive
    def test_skips_bad_cookie(self, cm, mock_driver):
        """無法加入的 cookie 應被跳過。"""
        cookies = [{'name': 'ok', 'value': '1'}, {'name': 'bad', 'value': '2'}]
        mock_driver.add_cookie.side_effect = [None, Exception('cross-domain')]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(cookies, f)
            path = f.name
        try:
            cm.load_cookies(path)  # 不應拋出例外
        finally:
            os.unlink(path)

    @pytest.mark.positive
    def test_removes_sameSite(self, cm, mock_driver):
        cookies = [{'name': 'a', 'value': '1', 'sameSite': 'Lax'}]
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(cookies, f)
            path = f.name
        try:
            cm.load_cookies(path)
            added = mock_driver.add_cookie.call_args[0][0]
            assert 'sameSite' not in added
        finally:
            os.unlink(path)


class TestHasCookie:
    @pytest.mark.positive
    def test_exists(self, cm, mock_driver):
        mock_driver.get_cookie.return_value = {'name': 'token', 'value': 'abc'}
        assert cm.has_cookie('token') is True

    @pytest.mark.negative
    def test_not_exists(self, cm, mock_driver):
        mock_driver.get_cookie.return_value = None
        assert cm.has_cookie('missing') is False


class TestGetCookieValue:
    @pytest.mark.positive
    def test_found(self, cm, mock_driver):
        mock_driver.get_cookie.return_value = {'name': 'token', 'value': 'abc'}
        assert cm.get_cookie_value('token') == 'abc'

    @pytest.mark.negative
    def test_not_found(self, cm, mock_driver):
        mock_driver.get_cookie.return_value = None
        assert cm.get_cookie_value('missing') is None
