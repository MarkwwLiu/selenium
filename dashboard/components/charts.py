"""
圖表元件

提供 NiceGUI 圖表元件，用於顯示測試統計。
"""

from nicegui import ui


def result_pie_chart(passed: int, failed: int, error: int, skipped: int):
    """測試結果圓餅圖。"""
    chart = ui.chart({
        'chart': {'type': 'pie'},
        'title': {'text': '測試結果分佈'},
        'series': [{
            'name': '測試數',
            'data': [
                {'name': f'通過 ({passed})', 'y': passed, 'color': '#4CAF50'},
                {'name': f'失敗 ({failed})', 'y': failed, 'color': '#F44336'},
                {'name': f'錯誤 ({error})', 'y': error, 'color': '#FF9800'},
                {'name': f'跳過 ({skipped})', 'y': skipped, 'color': '#9E9E9E'},
            ],
        }],
        'plotOptions': {
            'pie': {
                'dataLabels': {
                    'enabled': True,
                    'format': '{point.name}: {point.y}',
                },
            },
        },
    }).classes('w-full max-w-md')
    return chart


def history_bar_chart(history: list):
    """歷史執行長條圖。"""
    if not history:
        ui.label('尚無歷史紀錄').classes('text-gray-500')
        return

    # 取最近 10 筆
    recent = history[-10:]
    categories = [h.run_id for h in recent]

    chart = ui.chart({
        'chart': {'type': 'bar'},
        'title': {'text': '最近執行紀錄'},
        'xAxis': {'categories': categories, 'title': {'text': '執行 ID'}},
        'yAxis': {'title': {'text': '測試數'}},
        'series': [
            {'name': '通過', 'data': [h.passed for h in recent], 'color': '#4CAF50'},
            {'name': '失敗', 'data': [h.failed for h in recent], 'color': '#F44336'},
            {'name': '錯誤', 'data': [h.error for h in recent], 'color': '#FF9800'},
            {'name': '跳過', 'data': [h.skipped for h in recent], 'color': '#9E9E9E'},
        ],
        'plotOptions': {
            'bar': {'stacking': 'normal'},
        },
    }).classes('w-full')
    return chart


def stat_cards(passed: int, failed: int, error: int, skipped: int, total: int):
    """統計數字卡片列。"""
    with ui.row().classes('w-full gap-4 flex-wrap'):
        _stat_card('總計', total, 'bg-blue-100 text-blue-800')
        _stat_card('通過', passed, 'bg-green-100 text-green-800')
        _stat_card('失敗', failed, 'bg-red-100 text-red-800')
        _stat_card('錯誤', error, 'bg-orange-100 text-orange-800')
        _stat_card('跳過', skipped, 'bg-gray-100 text-gray-800')


def _stat_card(label: str, value: int, color_class: str):
    """單一統計卡片。"""
    with ui.card().classes(f'p-4 min-w-[120px] {color_class}'):
        ui.label(label).classes('text-sm font-medium')
        ui.label(str(value)).classes('text-3xl font-bold')


def pass_rate_label(passed: int, total: int):
    """通過率標籤。"""
    if total == 0:
        rate = 0.0
    else:
        rate = passed / total * 100

    color = 'green' if rate >= 80 else 'orange' if rate >= 50 else 'red'
    ui.label(f'通過率: {rate:.1f}%').classes(f'text-2xl font-bold text-{color}-600')
