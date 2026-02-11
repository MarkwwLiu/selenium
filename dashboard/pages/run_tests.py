"""
測試執行頁面

選擇瀏覽器、環境、標記，啟動測試並即時顯示輸出。
"""

import os
import sys
from nicegui import ui, app

# 路徑設定
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from dashboard.components import test_runner
from config.environments import list_environments


def content():
    """測試執行頁面內容。"""

    ui.label('執行測試').classes('text-2xl font-bold mb-4')

    # === 參數設定區 ===
    with ui.card().classes('w-full p-4 mb-4'):
        ui.label('執行參數').classes('text-lg font-semibold mb-2')

        with ui.row().classes('w-full gap-4 flex-wrap items-end'):
            # 測試路徑
            test_path = ui.input(
                label='測試路徑',
                value='tests/',
                placeholder='tests/ 或 scenarios/xxx/tests/',
            ).classes('w-48')

            # 瀏覽器
            browser = ui.select(
                label='瀏覽器',
                options=['chrome', 'firefox', 'edge'],
                value='chrome',
            ).classes('w-36')

            # 環境
            envs = list_environments()
            env = ui.select(
                label='環境',
                options=envs,
                value='dev',
            ).classes('w-36')

            # 無頭模式
            headless = ui.checkbox('無頭模式', value=True)

        with ui.row().classes('w-full gap-4 flex-wrap items-end mt-2'):
            # 標記篩選
            markers = ui.input(
                label='標記篩選 (-m)',
                placeholder='smoke, positive, negative...',
            ).classes('w-48')

            # 額外參數
            extra_args = ui.input(
                label='額外參數',
                placeholder='--reruns 2 --reruns-delay 3',
            ).classes('w-64')

    # === 控制列 ===
    with ui.row().classes('gap-4 mb-4 items-center'):
        run_btn = ui.button('開始執行', icon='play_arrow').props('color=primary')
        status_label = ui.label('就緒').classes('text-gray-500')
        progress = ui.linear_progress(value=0, show_value=False).classes('w-64').props('rounded')
        progress.visible = False

    # === 統計卡片 ===
    stat_row = ui.row().classes('w-full gap-4 flex-wrap mb-4')

    # === 即時輸出 ===
    ui.label('執行輸出').classes('text-lg font-semibold mb-2')
    log_area = ui.log(max_lines=500).classes('w-full h-96')

    # === 結果表格 ===
    result_table_container = ui.column().classes('w-full mt-4')

    def update_ui():
        """從 session 更新 UI。"""
        session = test_runner.get_current_session()
        if not session:
            return

        # 更新狀態
        if session.status == 'running':
            status_label.text = f'執行中... ({session.total} 個測試)'
            status_label.classes(replace='text-blue-500')
            progress.visible = True
            run_btn.disable()
        elif session.status == 'finished':
            total = session.total or 1
            rate = session.passed / total * 100
            status_label.text = f'完成 — 通過率 {rate:.1f}% ({session.passed}/{session.total})'
            color = 'text-green-600' if session.failed == 0 else 'text-red-600'
            status_label.classes(replace=color)
            progress.visible = False
            run_btn.enable()
        elif session.status == 'error':
            status_label.text = '執行錯誤'
            status_label.classes(replace='text-red-600')
            progress.visible = False
            run_btn.enable()

        # 更新輸出
        if session.output_lines:
            latest = session.output_lines[-1] if session.output_lines else ''
            log_area.push(latest)

        # 更新統計卡片
        stat_row.clear()
        with stat_row:
            _mini_stat('總計', session.total, 'blue')
            _mini_stat('通過', session.passed, 'green')
            _mini_stat('失敗', session.failed, 'red')
            _mini_stat('錯誤', session.error, 'orange')
            _mini_stat('跳過', session.skipped, 'gray')

        # 完成後顯示結果表格
        if session.status == 'finished' and session.results:
            result_table_container.clear()
            with result_table_container:
                _render_result_table(session.results)

    def on_run():
        """點擊執行按鈕。"""
        if test_runner.is_running():
            ui.notify('已有測試正在執行中', type='warning')
            return

        log_area.clear()
        stat_row.clear()
        result_table_container.clear()

        try:
            test_runner.start_run(
                test_path=test_path.value,
                browser=browser.value,
                headless=headless.value,
                env=env.value,
                markers=markers.value,
                extra_args=extra_args.value,
                on_update=lambda: ui.timer(0.1, update_ui, once=True),
            )
            ui.notify('測試開始執行', type='positive')
        except RuntimeError as e:
            ui.notify(str(e), type='negative')

    run_btn.on_click(on_run)

    # 定時刷新 UI
    ui.timer(1.0, update_ui)


def _mini_stat(label: str, value: int, color: str):
    """迷你統計標籤。"""
    with ui.card().classes(f'px-4 py-2 bg-{color}-50'):
        ui.label(f'{label}: {value}').classes(f'text-{color}-700 font-semibold')


def _render_result_table(results: list):
    """渲染測試結果表格。"""
    ui.label('測試結果明細').classes('text-lg font-semibold mb-2')

    columns = [
        {'name': 'name', 'label': '測試名稱', 'field': 'name', 'align': 'left', 'sortable': True},
        {'name': 'outcome', 'label': '結果', 'field': 'outcome', 'align': 'center', 'sortable': True},
        {'name': 'duration', 'label': '耗時(秒)', 'field': 'duration', 'align': 'right', 'sortable': True},
        {'name': 'message', 'label': '訊息', 'field': 'message', 'align': 'left'},
    ]

    rows = []
    for r in results:
        rows.append({
            'name': r.name,
            'outcome': r.outcome,
            'duration': f'{r.duration:.2f}',
            'message': r.message or '',
        })

    table = ui.table(
        columns=columns,
        rows=rows,
        row_key='name',
    ).classes('w-full')

    return table
