"""
情境管理頁面

瀏覽、建立、管理測試情境。
"""

import os
import sys
import subprocess
from nicegui import ui

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from dashboard.components.test_runner import discover_scenarios, discover_tests


def content():
    """情境管理頁面內容。"""

    ui.label('情境管理').classes('text-2xl font-bold mb-4')

    # === 建立新情境 ===
    with ui.card().classes('w-full p-4 mb-4'):
        ui.label('建立新情境').classes('text-lg font-semibold mb-2')

        with ui.row().classes('gap-4 items-end'):
            new_name = ui.input(
                label='情境名稱',
                placeholder='my_test（英文、底線）',
            ).classes('w-48')

            new_url = ui.input(
                label='目標 URL',
                placeholder='https://example.com/login',
            ).classes('w-64')

            create_btn = ui.button('建立', icon='add').props('color=primary')

        create_log = ui.label('').classes('text-sm mt-2')

        def on_create():
            name = new_name.value.strip()
            url = new_url.value.strip()

            if not name:
                ui.notify('請輸入情境名稱', type='warning')
                return

            if not name.replace('_', '').isalnum():
                ui.notify('名稱只能包含英文和底線', type='warning')
                return

            try:
                args = [sys.executable, 'generate_scenario.py', name]
                if url:
                    args.extend(['--url', url])

                result = subprocess.run(
                    args,
                    cwd=ROOT_DIR,
                    capture_output=True,
                    text=True,
                    timeout=10,
                )

                if result.returncode == 0:
                    ui.notify(f'情境 {name} 建立成功', type='positive')
                    create_log.text = result.stdout
                    refresh_list()
                else:
                    ui.notify(f'建立失敗: {result.stderr or result.stdout}', type='negative')
                    create_log.text = result.stderr or result.stdout

            except Exception as e:
                ui.notify(f'建立失敗: {e}', type='negative')

        create_btn.on_click(on_create)

    # === 情境列表 ===
    scenario_container = ui.column().classes('w-full')

    def refresh_list():
        scenario_container.clear()
        scenarios = discover_scenarios()

        with scenario_container:
            if not scenarios:
                ui.label('尚無情境（_template 除外）').classes('text-gray-500')
                return

            ui.label(f'現有情境 ({len(scenarios)})').classes('text-lg font-semibold mb-2')

            for s in scenarios:
                with ui.card().classes('w-full p-4 mb-2'):
                    with ui.row().classes('items-center gap-4 w-full'):
                        # 情境名稱
                        ui.label(s['name']).classes('text-lg font-semibold')

                        # URL
                        if s['url']:
                            ui.link(s['url'], s['url'], new_tab=True).classes('text-sm text-blue-500')
                        else:
                            ui.label('(未設定 URL)').classes('text-sm text-gray-400')

                        ui.space()

                        # 測試狀態
                        if s['has_tests']:
                            ui.badge('有測試', color='green').props('outline')
                        else:
                            ui.badge('無測試', color='orange').props('outline')

                    # 路徑
                    ui.label(s['path']).classes('text-xs text-gray-400 mt-1')

                    # 目錄結構預覽
                    with ui.row().classes('gap-2 mt-2'):
                        _dir_badge(s['path'], 'pages')
                        _dir_badge(s['path'], 'tests')
                        _dir_badge(s['path'], 'test_data')
                        _dir_badge(s['path'], 'results')

                    # 測試項目列表
                    if s['has_tests']:
                        tests_path = os.path.join(s['path'], 'tests')
                        test_files = [
                            f for f in os.listdir(tests_path)
                            if f.startswith('test_') and f.endswith('.py')
                        ] if os.path.isdir(tests_path) else []

                        if test_files:
                            with ui.expansion('測試檔案', icon='description').classes('mt-2'):
                                for tf in sorted(test_files):
                                    ui.label(f'  {tf}').classes('text-sm font-mono')

    refresh_list()

    # 重新整理按鈕
    with ui.row().classes('mt-4'):
        ui.button('重新整理', icon='refresh', on_click=refresh_list).props('flat')


def _dir_badge(base_path: str, dirname: str):
    """顯示子目錄是否存在的徽章。"""
    exists = os.path.isdir(os.path.join(base_path, dirname))
    color = 'green' if exists else 'grey'
    icon = 'check_circle' if exists else 'cancel'
    ui.badge(dirname, color=color).props('outline')
