"""
視覺回歸比對頁面

瀏覽 baseline / 最新截圖 / diff 圖片，並排比對。
"""

import os
import sys
import base64
from nicegui import ui

ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from config.settings import BASELINES_DIR, DIFFS_DIR, SCREENSHOTS_DIR


def content():
    """視覺回歸比對頁面內容。"""

    ui.label('視覺回歸比對').classes('text-2xl font-bold mb-4')

    # 掃描 baselines
    baselines = _scan_images(BASELINES_DIR)
    diffs = _scan_images(DIFFS_DIR)
    screenshots = _scan_images(SCREENSHOTS_DIR)

    # 也掃描 scenarios 底下的 baselines / diffs
    scenarios_dir = os.path.join(ROOT_DIR, 'scenarios')
    if os.path.isdir(scenarios_dir):
        for name in os.listdir(scenarios_dir):
            if name.startswith(('_', '.')):
                continue
            results_dir = os.path.join(scenarios_dir, name, 'results')
            baselines.update(_scan_images(os.path.join(results_dir, 'baselines'), prefix=name))
            diffs.update(_scan_images(os.path.join(results_dir, 'diffs'), prefix=name))

    if not baselines and not diffs and not screenshots:
        with ui.card().classes('w-full p-8 text-center'):
            ui.icon('image_not_supported', size='xl').classes('text-gray-400')
            ui.label('尚無視覺回歸資料').classes('text-xl text-gray-500 mt-2')
            ui.label('執行帶有 @pytest.mark.visual 標記的測試來產生 baseline。').classes(
                'text-gray-400'
            )
        return

    # === Baseline 瀏覽 ===
    all_names = sorted(set(list(baselines.keys()) + list(diffs.keys())))

    if all_names:
        with ui.card().classes('w-full p-4 mb-4'):
            ui.label('比對項目').classes('text-lg font-semibold mb-2')
            selected = ui.select(
                label='選擇項目',
                options=all_names,
                value=all_names[0] if all_names else None,
            ).classes('w-64')

        comparison_area = ui.column().classes('w-full')

        def show_comparison():
            comparison_area.clear()
            name = selected.value
            if not name:
                return

            with comparison_area:
                with ui.row().classes('w-full gap-4 flex-wrap'):
                    # Baseline
                    with ui.card().classes('flex-1 p-4'):
                        ui.label('Baseline（基準）').classes('font-semibold text-blue-600 mb-2')
                        if name in baselines:
                            _show_image(baselines[name])
                        else:
                            ui.label('無 baseline').classes('text-gray-400')

                    # Diff
                    with ui.card().classes('flex-1 p-4'):
                        ui.label('Diff（差異）').classes('font-semibold text-red-600 mb-2')
                        if name in diffs:
                            _show_image(diffs[name])
                        else:
                            ui.label('無差異圖').classes('text-gray-400')

        selected.on_value_change(lambda: show_comparison())
        show_comparison()

    # === 截圖瀏覽 ===
    if screenshots:
        with ui.card().classes('w-full p-4 mt-4'):
            ui.label(f'失敗截圖 ({len(screenshots)})').classes('text-lg font-semibold mb-2')

            with ui.row().classes('gap-4 flex-wrap'):
                for name, path in sorted(screenshots.items()):
                    with ui.card().classes('p-2 w-72'):
                        ui.label(name).classes('text-sm font-medium mb-1 truncate')
                        _show_image(path)


def _scan_images(directory: str, prefix: str = '') -> dict:
    """
    掃描目錄中的 PNG 圖片。

    Returns:
        {display_name: full_path, ...}
    """
    images = {}
    if not directory or not os.path.isdir(directory):
        return images

    for fname in os.listdir(directory):
        if not fname.lower().endswith('.png'):
            continue
        display_name = fname.replace('.png', '')
        if prefix:
            display_name = f'{prefix}/{display_name}'
        images[display_name] = os.path.join(directory, fname)

    return images


def _show_image(file_path: str):
    """顯示本地圖片。"""
    if not os.path.exists(file_path):
        ui.label('檔案不存在').classes('text-red-400')
        return

    try:
        with open(file_path, 'rb') as f:
            data = base64.b64encode(f.read()).decode('utf-8')
        ui.image(f'data:image/png;base64,{data}').classes('w-full rounded border')
    except Exception as e:
        ui.label(f'讀取失敗: {e}').classes('text-red-400')
