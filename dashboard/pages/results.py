"""
測試結果儀表板頁面

顯示最近一次執行結果、統計圖表、歷史紀錄。
"""

import os
import sys
from nicegui import ui

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from dashboard.components import test_runner, charts


def content():
    """結果儀表板頁面內容。"""

    ui.label('測試結果').classes('text-2xl font-bold mb-4')

    session = test_runner.get_current_session()
    history = test_runner.get_history()

    if not session and not history:
        with ui.card().classes('w-full p-8 text-center'):
            ui.icon('info', size='xl').classes('text-gray-400')
            ui.label('尚未執行任何測試').classes('text-xl text-gray-500 mt-2')
            ui.label('請先至「執行測試」頁面啟動測試。').classes('text-gray-400')
        return

    # 使用最新的 session（可能是 current 或 history 最後一筆）
    latest = session if session else history[-1] if history else None

    if latest:
        # === 摘要卡片 ===
        with ui.card().classes('w-full p-4 mb-4'):
            with ui.row().classes('items-center gap-4'):
                ui.label(f'執行 ID: {latest.run_id}').classes('font-semibold')
                _status_badge(latest.status)
                if latest.started_at:
                    ui.label(f'開始: {latest.started_at}').classes('text-sm text-gray-500')
                if latest.finished_at:
                    ui.label(f'結束: {latest.finished_at}').classes('text-sm text-gray-500')

            with ui.row().classes('text-sm text-gray-500 mt-1 gap-4'):
                ui.label(f'路徑: {latest.test_path}')
                ui.label(f'瀏覽器: {latest.browser}')
                ui.label(f'環境: {latest.env}')
                if latest.markers:
                    ui.label(f'標記: {latest.markers}')

        # === 統計 + 圓餅圖 ===
        with ui.row().classes('w-full gap-4 flex-wrap mb-4'):
            with ui.column().classes('flex-1'):
                charts.stat_cards(
                    latest.passed, latest.failed, latest.error,
                    latest.skipped, latest.total,
                )
                with ui.row().classes('mt-4'):
                    charts.pass_rate_label(latest.passed, latest.total)

            with ui.column().classes('flex-1'):
                if latest.total > 0:
                    charts.result_pie_chart(
                        latest.passed, latest.failed,
                        latest.error, latest.skipped,
                    )

        # === 失敗測試詳情 ===
        failed_tests = [r for r in latest.results if r.outcome in ('failed', 'error')]
        if failed_tests:
            with ui.card().classes('w-full p-4 mb-4'):
                ui.label(f'失敗測試 ({len(failed_tests)})').classes(
                    'text-lg font-semibold text-red-600 mb-2'
                )
                for r in failed_tests:
                    with ui.expansion(r.name, icon='error').classes('w-full text-red-600'):
                        ui.label(f'結果: {r.outcome} | 耗時: {r.duration:.2f}s').classes(
                            'text-sm text-gray-600'
                        )
                        if r.message:
                            ui.label(r.message).classes('text-sm text-red-500 mt-1')
                        if r.longrepr:
                            ui.code(r.longrepr).classes('w-full mt-2')

        # === 全部結果表格 ===
        if latest.results:
            with ui.card().classes('w-full p-4 mb-4'):
                ui.label('完整結果').classes('text-lg font-semibold mb-2')
                _result_table(latest.results)

    # === 歷史紀錄 ===
    if history:
        with ui.card().classes('w-full p-4'):
            ui.label('歷史紀錄').classes('text-lg font-semibold mb-2')
            charts.history_bar_chart(history)

            ui.separator().classes('my-4')

            columns = [
                {'name': 'run_id', 'label': '執行 ID', 'field': 'run_id', 'align': 'left'},
                {'name': 'status', 'label': '狀態', 'field': 'status', 'align': 'center'},
                {'name': 'total', 'label': '總計', 'field': 'total', 'align': 'right'},
                {'name': 'passed', 'label': '通過', 'field': 'passed', 'align': 'right'},
                {'name': 'failed', 'label': '失敗', 'field': 'failed', 'align': 'right'},
                {'name': 'started_at', 'label': '開始時間', 'field': 'started_at', 'align': 'left'},
                {'name': 'test_path', 'label': '路徑', 'field': 'test_path', 'align': 'left'},
            ]

            rows = []
            for h in reversed(history):
                rows.append({
                    'run_id': h.run_id,
                    'status': h.status,
                    'total': h.total,
                    'passed': h.passed,
                    'failed': h.failed,
                    'started_at': h.started_at,
                    'test_path': h.test_path,
                })

            ui.table(columns=columns, rows=rows, row_key='run_id').classes('w-full')


def _status_badge(status: str):
    """狀態徽章。"""
    colors = {
        'idle': 'bg-gray-200 text-gray-700',
        'running': 'bg-blue-200 text-blue-700',
        'finished': 'bg-green-200 text-green-700',
        'error': 'bg-red-200 text-red-700',
    }
    css = colors.get(status, 'bg-gray-200 text-gray-700')
    ui.label(status.upper()).classes(f'px-2 py-1 rounded text-xs font-bold {css}')


def _result_table(results: list):
    """渲染結果表格。"""
    columns = [
        {'name': 'nodeid', 'label': '測試 ID', 'field': 'nodeid', 'align': 'left', 'sortable': True},
        {'name': 'outcome', 'label': '結果', 'field': 'outcome', 'align': 'center', 'sortable': True},
        {'name': 'duration', 'label': '耗時(秒)', 'field': 'duration', 'align': 'right', 'sortable': True},
    ]

    rows = []
    for r in results:
        rows.append({
            'nodeid': r.nodeid,
            'outcome': r.outcome,
            'duration': f'{r.duration:.2f}',
        })

    ui.table(columns=columns, rows=rows, row_key='nodeid').classes('w-full')
