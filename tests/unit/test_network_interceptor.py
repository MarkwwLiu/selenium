"""
utils/network_interceptor.py 單元測試
"""

from unittest.mock import MagicMock, patch
import pytest

from utils.network_interceptor import NetworkInterceptor


@pytest.fixture
def mock_driver():
    return MagicMock()


@pytest.fixture
def interceptor(mock_driver):
    return NetworkInterceptor(mock_driver)


class TestInit:
    @pytest.mark.positive
    def test_default_state(self, mock_driver):
        ni = NetworkInterceptor(mock_driver)
        assert ni.driver is mock_driver
        assert ni._requests == []
        assert ni._responses == []
        assert ni._mock_rules == []
        assert ni._capturing is False


class TestStartCapture:
    @pytest.mark.positive
    def test_enables_network(self, interceptor, mock_driver):
        interceptor.start_capture()
        mock_driver.execute_cdp_cmd.assert_called_with('Network.enable', {})
        assert interceptor._capturing is True

    @pytest.mark.positive
    def test_clears_previous(self, interceptor, mock_driver):
        interceptor._requests = [{'url': 'old'}]
        interceptor.start_capture()
        assert interceptor._requests == []


class TestStopCapture:
    @pytest.mark.positive
    def test_disables_network(self, interceptor, mock_driver):
        interceptor._capturing = True
        interceptor.stop_capture()
        assert interceptor._capturing is False
        mock_driver.execute_cdp_cmd.assert_called_with('Network.disable', {})

    @pytest.mark.positive
    def test_handles_cdp_error(self, interceptor, mock_driver):
        mock_driver.execute_cdp_cmd.side_effect = Exception('CDP error')
        mock_driver.execute_script.return_value = []
        interceptor.stop_capture()  # 不應拋出例外


class TestGetRequests:
    @pytest.mark.positive
    def test_returns_list(self, interceptor, mock_driver):
        mock_driver.execute_script.return_value = [
            {'type': 'fetch', 'url': 'https://api.com/data', 'method': 'GET'},
        ]
        result = interceptor.get_requests()
        assert len(result) == 1

    @pytest.mark.positive
    def test_handles_js_error(self, interceptor, mock_driver):
        mock_driver.execute_script.side_effect = Exception('no window')
        interceptor._requests = [{'url': 'cached'}]
        result = interceptor.get_requests()
        assert len(result) == 1


class TestGetRequestsByUrl:
    @pytest.mark.positive
    def test_matching(self, interceptor, mock_driver):
        mock_driver.execute_script.return_value = []
        interceptor._requests = [
            {'url': 'https://api.com/users', 'method': 'GET'},
            {'url': 'https://api.com/posts', 'method': 'GET'},
            {'url': 'https://cdn.com/image.png', 'method': 'GET'},
        ]
        result = interceptor.get_requests_by_url('*api.com*')
        assert len(result) == 2

    @pytest.mark.negative
    def test_no_match(self, interceptor, mock_driver):
        mock_driver.execute_script.return_value = []
        interceptor._requests = [{'url': 'https://other.com'}]
        result = interceptor.get_requests_by_url('*api.com*')
        assert result == []


class TestHasRequest:
    @pytest.mark.positive
    def test_true(self, interceptor, mock_driver):
        mock_driver.execute_script.return_value = []
        interceptor._requests = [{'url': 'https://api.com/data'}]
        assert interceptor.has_request('*api.com*') is True

    @pytest.mark.negative
    def test_false(self, interceptor, mock_driver):
        mock_driver.execute_script.return_value = []
        interceptor._requests = []
        assert interceptor.has_request('*api.com*') is False


class TestClear:
    @pytest.mark.positive
    def test_clears_all(self, interceptor, mock_driver):
        interceptor._requests = [{'url': 'test'}]
        interceptor._responses = [{'status': 200}]
        interceptor.clear()
        assert interceptor._requests == []
        assert interceptor._responses == []

    @pytest.mark.positive
    def test_handles_js_error(self, interceptor, mock_driver):
        mock_driver.execute_script.side_effect = Exception('err')
        interceptor.clear()  # 不應拋出例外


class TestMockResponse:
    @pytest.mark.positive
    def test_adds_rule(self, interceptor, mock_driver):
        interceptor.mock_response('*/api/*', body='{"ok":true}', status=200)
        assert len(interceptor._mock_rules) == 1
        assert interceptor._mock_rules[0]['status'] == 200

    @pytest.mark.positive
    def test_with_headers(self, interceptor, mock_driver):
        interceptor.mock_response('*/api/*', headers={'X-Custom': 'val'})
        rule = interceptor._mock_rules[0]
        header_names = [h['name'] for h in rule['headers']]
        assert 'X-Custom' in header_names


class TestClearMocks:
    @pytest.mark.positive
    def test_clears_rules(self, interceptor, mock_driver):
        interceptor._mock_rules = [{'pattern': '*'}]
        interceptor.clear_mocks()
        assert interceptor._mock_rules == []

    @pytest.mark.positive
    def test_handles_cdp_error(self, interceptor, mock_driver):
        mock_driver.execute_cdp_cmd.side_effect = Exception('err')
        interceptor.clear_mocks()  # 不應拋出例外


class TestNetworkControl:
    @pytest.mark.positive
    def test_set_offline(self, interceptor, mock_driver):
        interceptor.set_offline(True)
        mock_driver.execute_cdp_cmd.assert_called_once()
        args = mock_driver.execute_cdp_cmd.call_args
        assert args[0][0] == 'Network.emulateNetworkConditions'
        assert args[0][1]['offline'] is True

    @pytest.mark.positive
    def test_throttle(self, interceptor, mock_driver):
        interceptor.throttle(download_kbps=500, upload_kbps=200, latency_ms=100)
        args = mock_driver.execute_cdp_cmd.call_args
        assert args[0][1]['latency'] == 100
        assert args[0][1]['offline'] is False

    @pytest.mark.positive
    def test_reset_network(self, interceptor, mock_driver):
        interceptor.reset_network()
        args = mock_driver.execute_cdp_cmd.call_args
        assert args[0][1]['offline'] is False
        assert args[0][1]['latency'] == 0

    @pytest.mark.positive
    def test_simulate_3g(self, interceptor, mock_driver):
        interceptor.simulate_3g()
        args = mock_driver.execute_cdp_cmd.call_args
        assert args[0][1]['latency'] == 100

    @pytest.mark.positive
    def test_simulate_slow_3g(self, interceptor, mock_driver):
        interceptor.simulate_slow_3g()
        args = mock_driver.execute_cdp_cmd.call_args
        assert args[0][1]['latency'] == 200


class TestBlockUrls:
    @pytest.mark.positive
    def test_blocks(self, interceptor, mock_driver):
        interceptor.block_urls(['*.ads.com*'])
        calls = mock_driver.execute_cdp_cmd.call_args_list
        assert calls[0][0][0] == 'Network.setBlockedURLs'
        assert calls[1][0][0] == 'Network.enable'

    @pytest.mark.positive
    def test_unblock(self, interceptor, mock_driver):
        interceptor.unblock_urls()
        args = mock_driver.execute_cdp_cmd.call_args
        assert args[0][1]['urls'] == []
