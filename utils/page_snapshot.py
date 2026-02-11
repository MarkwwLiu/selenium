"""
頁面快照工具

每次動作後自動儲存頁面狀態（截圖 + HTML + 元素清單 + URL），
方便事後分析、擴充測試情境、比對前後差異。
"""

import json
import os
from datetime import datetime


class PageSnapshot:
    """
    頁面快照管理器。

    綁定一個 output 目錄，每次 take() 都會存：
      - {step}_screenshot.png
      - {step}_page.html
      - {step}_state.json（URL、title、可見元素數、表單值等）

    Usage:
        snapshot = PageSnapshot(driver, 'scenarios/login_test/results/snapshots')
        snapshot.take('01_open_page')
        # ... 做一些操作 ...
        snapshot.take('02_fill_form')
        # ... 提交 ...
        snapshot.take('03_after_submit')
    """

    def __init__(self, driver, output_dir):
        self.driver = driver
        self.output_dir = output_dir
        self._step_counter = 0
        self._history = []
        os.makedirs(output_dir, exist_ok=True)

    def take(self, label=''):
        """
        擷取當前頁面的完整快照。

        Args:
            label: 步驟標籤（如 'open_page'、'fill_form'），
                   留空則自動編號。

        Returns:
            dict: 快照摘要
        """
        self._step_counter += 1
        step_id = f'{self._step_counter:03d}'
        prefix = f'{step_id}_{label}' if label else step_id
        timestamp = datetime.now().isoformat()

        # 截圖
        screenshot_path = os.path.join(self.output_dir, f'{prefix}_screenshot.png')
        self.driver.save_screenshot(screenshot_path)

        # 儲存 HTML
        html_path = os.path.join(self.output_dir, f'{prefix}_page.html')
        with open(html_path, 'w', encoding='utf-8') as f:
            f.write(self.driver.page_source)

        # 收集頁面狀態
        state = self._collect_state()
        state['step'] = step_id
        state['label'] = label
        state['timestamp'] = timestamp
        state['screenshot'] = os.path.basename(screenshot_path)
        state['html'] = os.path.basename(html_path)

        # 儲存狀態 JSON
        state_path = os.path.join(self.output_dir, f'{prefix}_state.json')
        with open(state_path, 'w', encoding='utf-8') as f:
            json.dump(state, f, ensure_ascii=False, indent=2)

        self._history.append(state)
        return state

    def _collect_state(self):
        """用 JS 收集當前頁面狀態。"""
        return self.driver.execute_script("""
            return {
                url: window.location.href,
                title: document.title,
                scroll_y: window.scrollY,
                viewport: {
                    width: window.innerWidth,
                    height: window.innerHeight
                },
                form_values: (function() {
                    var vals = {};
                    document.querySelectorAll('input, select, textarea').forEach(function(el) {
                        var key = el.id || el.name || '';
                        if (!key) return;
                        if (el.type === 'checkbox' || el.type === 'radio') {
                            vals[key] = el.checked;
                        } else {
                            vals[key] = el.value || '';
                        }
                    });
                    return vals;
                })(),
                visible_element_count: document.querySelectorAll('*').length,
                alert_present: false
            };
        """)

    def save_timeline(self):
        """
        將所有快照串成時間軸 JSON，方便一覽測試流程。

        Returns:
            str: timeline JSON 檔案路徑
        """
        filepath = os.path.join(self.output_dir, 'timeline.json')
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump({
                'total_steps': len(self._history),
                'steps': self._history,
            }, f, ensure_ascii=False, indent=2)
        return filepath

    def get_history(self):
        """取得所有快照歷史。"""
        return list(self._history)

    def diff(self, step_a, step_b):
        """
        比較兩個步驟之間的差異。

        Args:
            step_a: 步驟索引（0-based）
            step_b: 步驟索引（0-based）

        Returns:
            dict: 差異摘要
        """
        if step_a >= len(self._history) or step_b >= len(self._history):
            return {'error': '步驟索引超出範圍'}

        a = self._history[step_a]
        b = self._history[step_b]

        changes = {
            'url_changed': a.get('url') != b.get('url'),
            'title_changed': a.get('title') != b.get('title'),
            'form_changes': {},
        }

        # 比對表單值
        vals_a = a.get('form_values', {})
        vals_b = b.get('form_values', {})
        all_keys = set(list(vals_a.keys()) + list(vals_b.keys()))
        for key in all_keys:
            va = vals_a.get(key)
            vb = vals_b.get(key)
            if va != vb:
                changes['form_changes'][key] = {'before': va, 'after': vb}

        return changes
