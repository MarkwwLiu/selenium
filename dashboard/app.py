#!/usr/bin/env python3
"""
Selenium 測試管理儀表板

基於 NiceGUI 的 Web UI，提供：
- 測試執行（選擇瀏覽器、環境、標記，即時查看輸出）
- 結果儀表板（統計圖表、失敗詳情、歷史紀錄）
- 視覺回歸比對（baseline / diff 並排）
- 情境管理（瀏覽、建立測試情境）

使用方式:
    python dashboard/app.py
    python -m dashboard.app
"""

import os
import sys

# 確保專案根目錄在 sys.path
ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from nicegui import ui

from dashboard.pages import run_tests, results, visual_diff, scenarios


# === 頁面定義 ===

@ui.page('/')
def page_home():
    _layout('首頁')
    with ui.column().classes('w-full max-w-6xl mx-auto p-4'):
        ui.label('Selenium 測試管理儀表板').classes('text-3xl font-bold mb-2')
        ui.label('統一管理測試執行、結果分析、視覺比對與情境配置。').classes(
            'text-gray-500 mb-6'
        )

        with ui.row().classes('gap-6 flex-wrap'):
            _nav_card(
                '執行測試',
                '選擇瀏覽器、環境與標記，啟動測試並即時查看輸出。',
                'play_arrow',
                '/run',
                'primary',
            )
            _nav_card(
                '測試結果',
                '查看統計圖表、失敗詳情與歷史紀錄。',
                'assessment',
                '/results',
                'green',
            )
            _nav_card(
                '視覺比對',
                '瀏覽 baseline 與 diff 截圖，並排比對。',
                'compare',
                '/visual',
                'purple',
            )
            _nav_card(
                '情境管理',
                '瀏覽與建立測試情境模組。',
                'folder_open',
                '/scenarios',
                'orange',
            )


@ui.page('/run')
def page_run():
    _layout('執行測試')
    with ui.column().classes('w-full max-w-6xl mx-auto p-4'):
        run_tests.content()


@ui.page('/results')
def page_results():
    _layout('測試結果')
    with ui.column().classes('w-full max-w-6xl mx-auto p-4'):
        results.content()


@ui.page('/visual')
def page_visual():
    _layout('視覺比對')
    with ui.column().classes('w-full max-w-6xl mx-auto p-4'):
        visual_diff.content()


@ui.page('/scenarios')
def page_scenarios():
    _layout('情境管理')
    with ui.column().classes('w-full max-w-6xl mx-auto p-4'):
        scenarios.content()


# === 共用版面 ===

def _layout(active: str = ''):
    """共用導航列。"""
    with ui.header().classes('bg-blue-800 text-white'):
        with ui.row().classes('w-full items-center gap-4'):
            ui.label('Selenium Dashboard').classes('text-lg font-bold cursor-pointer').on(
                'click', lambda: ui.navigate.to('/')
            )
            ui.space()
            _nav_btn('首頁', '/', 'home', active)
            _nav_btn('執行測試', '/run', 'play_arrow', active)
            _nav_btn('測試結果', '/results', 'assessment', active)
            _nav_btn('視覺比對', '/visual', 'compare', active)
            _nav_btn('情境管理', '/scenarios', 'folder_open', active)


def _nav_btn(label: str, path: str, icon: str, active: str):
    """導航按鈕。"""
    is_active = label == active
    btn = ui.button(label, icon=icon, on_click=lambda: ui.navigate.to(path))
    btn.props('flat text-color=white')
    if is_active:
        btn.classes('bg-blue-700')


def _nav_card(title: str, desc: str, icon: str, path: str, color: str):
    """首頁導航卡片。"""
    with ui.card().classes('p-6 w-64 cursor-pointer hover:shadow-lg transition-shadow').on(
        'click', lambda: ui.navigate.to(path)
    ):
        ui.icon(icon, size='xl').classes(f'text-{color}-500')
        ui.label(title).classes('text-xl font-bold mt-2')
        ui.label(desc).classes('text-sm text-gray-500 mt-1')


# === 啟動 ===

if __name__ in {'__main__', '__mp_main__'}:
    ui.run(
        title='Selenium 測試管理',
        host='0.0.0.0',
        port=8080,
        reload=False,
    )
