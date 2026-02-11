"""
Soft Assertions 工具

允許測試在遇到斷言失敗時繼續執行，
最後一次性回報所有失敗項目，不會在第一個失敗就中斷。
"""

import traceback


class SoftAssert:
    """
    軟斷言工具：收集所有斷言失敗，最後統一回報。

    Usage:
        soft = SoftAssert()
        soft.equal(title, '首頁', '標題不正確')
        soft.true(is_visible, '元素應該可見')
        soft.contains('hello', 'ell', '應包含子字串')
        soft.assert_all()  # 如果有失敗會 raise AssertionError
    """

    def __init__(self):
        self._failures = []

    def _record_failure(self, message, details=''):
        """記錄一筆斷言失敗。"""
        # 取得呼叫位置（跳過內部方法）
        stack = traceback.extract_stack()
        caller = stack[-3] if len(stack) >= 3 else stack[-1]
        location = f'{caller.filename}:{caller.lineno}'
        entry = {
            'message': message,
            'details': details,
            'location': location,
        }
        self._failures.append(entry)

    def equal(self, actual, expected, message=''):
        """斷言兩值相等。"""
        if actual != expected:
            msg = message or f'預期 {expected!r}，實際 {actual!r}'
            self._record_failure(msg, f'actual={actual!r}, expected={expected!r}')

    def not_equal(self, actual, not_expected, message=''):
        """斷言兩值不相等。"""
        if actual == not_expected:
            msg = message or f'不預期的值: {actual!r}'
            self._record_failure(msg, f'actual={actual!r}')

    def true(self, condition, message=''):
        """斷言條件為真。"""
        if not condition:
            msg = message or '預期為 True，實際為 False'
            self._record_failure(msg)

    def false(self, condition, message=''):
        """斷言條件為假。"""
        if condition:
            msg = message or '預期為 False，實際為 True'
            self._record_failure(msg)

    def is_none(self, value, message=''):
        """斷言值為 None。"""
        if value is not None:
            msg = message or f'預期為 None，實際為 {value!r}'
            self._record_failure(msg)

    def is_not_none(self, value, message=''):
        """斷言值不為 None。"""
        if value is None:
            msg = message or '預期不為 None'
            self._record_failure(msg)

    def contains(self, container, item, message=''):
        """斷言 container 包含 item。"""
        if item not in container:
            msg = message or f'{container!r} 不包含 {item!r}'
            self._record_failure(msg, f'container={container!r}, item={item!r}')

    def not_contains(self, container, item, message=''):
        """斷言 container 不包含 item。"""
        if item in container:
            msg = message or f'{container!r} 不應包含 {item!r}'
            self._record_failure(msg)

    def greater(self, a, b, message=''):
        """斷言 a > b。"""
        if not (a > b):
            msg = message or f'預期 {a!r} > {b!r}'
            self._record_failure(msg)

    def less(self, a, b, message=''):
        """斷言 a < b。"""
        if not (a < b):
            msg = message or f'預期 {a!r} < {b!r}'
            self._record_failure(msg)

    @property
    def failure_count(self):
        """取得失敗數量。"""
        return len(self._failures)

    @property
    def failures(self):
        """取得所有失敗紀錄。"""
        return list(self._failures)

    def assert_all(self):
        """
        檢查所有累積的斷言結果，有失敗則拋出 AssertionError。

        應在測試結尾呼叫此方法。
        """
        if not self._failures:
            return

        lines = [f'Soft Assert 共有 {len(self._failures)} 個失敗:']
        for i, f in enumerate(self._failures, 1):
            lines.append(f'  {i}. {f["message"]}')
            if f['details']:
                lines.append(f'     {f["details"]}')
            lines.append(f'     at {f["location"]}')

        raise AssertionError('\n'.join(lines))
