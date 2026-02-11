"""
日誌工具

提供結構化的日誌紀錄，同時輸出到終端機與日誌檔案。
"""

import os
import logging
from datetime import datetime


def setup_logger(name='selenium_test', log_dir=None):
    """
    建立並設定 Logger。

    Args:
        name: Logger 名稱
        log_dir: 日誌檔案目錄，None 則只輸出到終端機

    Returns:
        設定好的 Logger 實例
    """
    logger = logging.getLogger(name)

    # 避免重複加入 handler
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        fmt='%(asctime)s [%(levelname)s] %(name)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )

    # 終端機輸出（INFO 以上）
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    # 檔案輸出（DEBUG 以上）
    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        today = datetime.now().strftime('%Y%m%d')
        log_file = os.path.join(log_dir, f'test_{today}.log')
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger
