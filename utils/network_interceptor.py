"""
網路攔截工具（Chrome DevTools Protocol）

透過 Selenium 4 的 CDP 功能攔截、修改、模擬網路請求。
僅支援 Chrome / Edge 瀏覽器。

Usage:
    from utils.network_interceptor import NetworkInterceptor

    interceptor = NetworkInterceptor(driver)

    # 記錄所有請求
    interceptor.start_capture()
    # ... 操作頁面 ...
    requests = interceptor.get_requests()
    interceptor.stop_capture()

    # 攔截特定 URL 回傳 mock 資料
    interceptor.mock_response(
        url_pattern='*/api/users*',
        body='{"users": []}',
        status=200,
    )

    # 模擬離線
    interceptor.set_offline(True)

    # 模擬慢速網路
    interceptor.throttle(download_kbps=500, upload_kbps=200, latency_ms=100)
"""

import json
import fnmatch
import threading
from selenium.webdriver.remote.webdriver import WebDriver


class NetworkInterceptor:
    """Chrome DevTools Protocol 網路攔截器。"""

    def __init__(self, driver: WebDriver):
        self.driver = driver
        self._requests = []
        self._responses = []
        self._mock_rules = []
        self._capturing = False
        self._lock = threading.Lock()

    # === 請求擷取 ===

    def start_capture(self):
        """開始擷取網路請求。"""
        self._requests.clear()
        self._responses.clear()
        self._capturing = True

        self.driver.execute_cdp_cmd('Network.enable', {})

        # 用 JS 攔截 fetch / XHR
        self.driver.execute_script("""
            window.__network_log = window.__network_log || [];
            (function() {
                // 攔截 fetch
                const origFetch = window.fetch;
                window.fetch = function(...args) {
                    const url = typeof args[0] === 'string' ? args[0] : args[0].url;
                    const method = (args[1] && args[1].method) || 'GET';
                    const entry = {type: 'fetch', url: url, method: method, timestamp: Date.now()};
                    window.__network_log.push(entry);
                    return origFetch.apply(this, args).then(resp => {
                        entry.status = resp.status;
                        return resp;
                    });
                };

                // 攔截 XMLHttpRequest
                const origOpen = XMLHttpRequest.prototype.open;
                const origSend = XMLHttpRequest.prototype.send;
                XMLHttpRequest.prototype.open = function(method, url) {
                    this.__entry = {type: 'xhr', url: url, method: method, timestamp: Date.now()};
                    window.__network_log.push(this.__entry);
                    return origOpen.apply(this, arguments);
                };
                XMLHttpRequest.prototype.send = function() {
                    this.addEventListener('load', function() {
                        if (this.__entry) this.__entry.status = this.status;
                    });
                    return origSend.apply(this, arguments);
                };
            })();
        """)

    def stop_capture(self):
        """停止擷取。"""
        self._capturing = False
        self._collect_js_logs()
        try:
            self.driver.execute_cdp_cmd('Network.disable', {})
        except Exception:
            pass

    def get_requests(self) -> list[dict]:
        """
        取得已擷取的請求列表。

        Returns:
            [{'type': 'fetch|xhr', 'url': '...', 'method': '...', 'status': 200, 'timestamp': ...}, ...]
        """
        self._collect_js_logs()
        return list(self._requests)

    def get_requests_by_url(self, pattern: str) -> list[dict]:
        """
        以 URL 模式篩選請求（支援 * 萬用字元）。

        Args:
            pattern: URL 模式，如 '*/api/users*'
        """
        return [r for r in self.get_requests() if fnmatch.fnmatch(r.get('url', ''), pattern)]

    def has_request(self, pattern: str) -> bool:
        """是否有符合模式的請求。"""
        return len(self.get_requests_by_url(pattern)) > 0

    def wait_for_request(self, pattern: str, timeout: int = 10) -> dict | None:
        """
        等待出現符合模式的請求。

        Args:
            pattern: URL 模式
            timeout: 超時秒數

        Returns:
            符合的請求 dict 或 None
        """
        import time
        deadline = time.time() + timeout
        while time.time() < deadline:
            matches = self.get_requests_by_url(pattern)
            if matches:
                return matches[-1]
            time.sleep(0.3)
        return None

    def clear(self):
        """清除所有已擷取的請求。"""
        with self._lock:
            self._requests.clear()
            self._responses.clear()
        try:
            self.driver.execute_script('window.__network_log = [];')
        except Exception:
            pass

    def _collect_js_logs(self):
        """從瀏覽器收集 JS 攔截的請求紀錄。"""
        try:
            logs = self.driver.execute_script(
                'var logs = window.__network_log || []; window.__network_log = []; return logs;'
            )
            if logs:
                with self._lock:
                    self._requests.extend(logs)
        except Exception:
            pass

    # === Mock 回應 ===

    def mock_response(
        self,
        url_pattern: str,
        body: str = '{}',
        status: int = 200,
        headers: dict = None,
    ):
        """
        對符合 URL 模式的請求回傳 mock 資料。

        透過 Fetch.enable + requestPaused 攔截。

        Args:
            url_pattern: URL 模式（支援 CDP 的 * 萬用字元）
            body: 回應 body
            status: HTTP 狀態碼
            headers: 額外 response headers
        """
        import base64

        self.driver.execute_cdp_cmd('Fetch.enable', {
            'patterns': [{'urlPattern': url_pattern, 'requestStage': 'Request'}],
        })

        encoded_body = base64.b64encode(body.encode('utf-8')).decode('utf-8')

        response_headers = [
            {'name': 'Content-Type', 'value': 'application/json'},
            {'name': 'Access-Control-Allow-Origin', 'value': '*'},
        ]
        if headers:
            for k, v in headers.items():
                response_headers.append({'name': k, 'value': v})

        self._mock_rules.append({
            'pattern': url_pattern,
            'body': encoded_body,
            'status': status,
            'headers': response_headers,
        })

    def clear_mocks(self):
        """清除所有 mock 規則。"""
        self._mock_rules.clear()
        try:
            self.driver.execute_cdp_cmd('Fetch.disable', {})
        except Exception:
            pass

    # === 網路狀態控制 ===

    def set_offline(self, offline: bool = True):
        """
        模擬離線/上線。

        Args:
            offline: True=離線, False=上線
        """
        self.driver.execute_cdp_cmd('Network.emulateNetworkConditions', {
            'offline': offline,
            'latency': 0,
            'downloadThroughput': -1,
            'uploadThroughput': -1,
        })

    def throttle(
        self,
        download_kbps: int = 1000,
        upload_kbps: int = 500,
        latency_ms: int = 50,
    ):
        """
        模擬慢速網路。

        預設模擬:
            - 3G: throttle(750, 250, 100)
            - 慢 3G: throttle(400, 150, 200)
            - WiFi: throttle(4000, 3000, 10)

        Args:
            download_kbps: 下載速度 (KB/s)
            upload_kbps: 上傳速度 (KB/s)
            latency_ms: 延遲 (ms)
        """
        self.driver.execute_cdp_cmd('Network.emulateNetworkConditions', {
            'offline': False,
            'latency': latency_ms,
            'downloadThroughput': download_kbps * 1024 / 8,
            'uploadThroughput': upload_kbps * 1024 / 8,
        })

    def reset_network(self):
        """恢復正常網路。"""
        self.driver.execute_cdp_cmd('Network.emulateNetworkConditions', {
            'offline': False,
            'latency': 0,
            'downloadThroughput': -1,
            'uploadThroughput': -1,
        })

    # === 預設模擬情境 ===

    def simulate_3g(self):
        """模擬 3G 網路。"""
        self.throttle(download_kbps=750, upload_kbps=250, latency_ms=100)

    def simulate_slow_3g(self):
        """模擬慢速 3G。"""
        self.throttle(download_kbps=400, upload_kbps=150, latency_ms=200)

    # === 請求阻擋 ===

    def block_urls(self, patterns: list[str]):
        """
        阻擋符合模式的 URL（例如阻擋第三方追蹤）。

        Args:
            patterns: URL 模式列表，如 ['*.google-analytics.com*', '*.facebook.com*']
        """
        self.driver.execute_cdp_cmd('Network.setBlockedURLs', {
            'urls': patterns,
        })
        self.driver.execute_cdp_cmd('Network.enable', {})

    def unblock_urls(self):
        """取消所有 URL 阻擋。"""
        self.driver.execute_cdp_cmd('Network.setBlockedURLs', {'urls': []})
