"""
多環境設定管理

支援 dev / staging / prod 等多個環境的設定切換。
透過環境變數 TEST_ENV 或 pytest 參數 --env 來選擇環境。

Usage:
    # 透過環境變數
    TEST_ENV=staging pytest tests/

    # 透過 pytest 參數（需搭配 conftest.py）
    pytest tests/ --env staging

    # 在程式碼中使用
    from config.environments import get_env_config
    config = get_env_config()
    driver.get(config['base_url'])
"""

import os


# === 環境設定定義 ===

ENVIRONMENTS = {
    'dev': {
        'base_url': 'http://localhost:3000',
        'api_url': 'http://localhost:8000/api',
        'timeout': 15,
        'headless': False,
        'description': '本地開發環境',
    },
    'staging': {
        'base_url': 'https://staging.example.com',
        'api_url': 'https://staging.example.com/api',
        'timeout': 20,
        'headless': True,
        'description': '預發佈測試環境',
    },
    'prod': {
        'base_url': 'https://www.example.com',
        'api_url': 'https://www.example.com/api',
        'timeout': 30,
        'headless': True,
        'description': '正式環境（唯讀測試）',
    },
}

# 預設環境
DEFAULT_ENV = 'dev'


def get_env_name():
    """
    取得當前環境名稱。

    優先順序：
    1. 環境變數 TEST_ENV
    2. 預設值 DEFAULT_ENV
    """
    return os.environ.get('TEST_ENV', DEFAULT_ENV)


def get_env_config(env_name=None):
    """
    取得指定環境的設定。

    Args:
        env_name: 環境名稱，None 則自動偵測。

    Returns:
        dict: 環境設定

    Raises:
        ValueError: 環境名稱不存在
    """
    name = env_name or get_env_name()
    if name not in ENVIRONMENTS:
        available = ', '.join(ENVIRONMENTS.keys())
        raise ValueError(f'未知的環境: {name!r}，可用環境: {available}')
    config = dict(ENVIRONMENTS[name])
    config['env_name'] = name
    return config


def list_environments():
    """列出所有可用環境。"""
    return list(ENVIRONMENTS.keys())


def register_environment(name, config):
    """
    動態註冊新環境。

    Usage:
        register_environment('qa', {
            'base_url': 'https://qa.example.com',
            'api_url': 'https://qa.example.com/api',
            'timeout': 20,
            'headless': True,
            'description': 'QA 環境',
        })
    """
    ENVIRONMENTS[name] = config
