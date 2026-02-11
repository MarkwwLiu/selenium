"""
截圖工具

測試失敗時自動擷取瀏覽器畫面，方便除錯追蹤。
"""

import os
from datetime import datetime


def take_screenshot(driver, save_dir, test_name):
    """
    擷取當前瀏覽器畫面並儲存為 PNG。

    Args:
        driver: WebDriver 實例
        save_dir: 截圖儲存目錄
        test_name: 測試方法名稱（用於檔名）

    Returns:
        截圖檔案的完整路徑
    """
    os.makedirs(save_dir, exist_ok=True)
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f'{test_name}_{timestamp}.png'
    filepath = os.path.join(save_dir, filename)
    driver.save_screenshot(filepath)
    return filepath
