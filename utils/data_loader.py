"""
測試資料載入器

支援從 JSON / CSV / Python dict 載入測試資料，
搭配 @pytest.mark.parametrize 使用。
"""

import csv
import json
import os
import pytest


def load_json(file_path):
    """
    從 JSON 檔案載入測試資料。

    JSON 格式（list of dicts）：
        [
            {"email": "user@mail.com", "password": "Pass1234", "expected": true, "id": "正向-合法帳密"},
            {"email": "", "password": "Pass1234", "expected": false, "id": "反向-空帳號"}
        ]

    Returns:
        list[dict]
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def load_csv(file_path):
    """
    從 CSV 檔案載入測試資料。

    CSV 格式（首行為欄位名）：
        email,password,expected,id
        user@mail.com,Pass1234,true,正向-合法帳密
        ,Pass1234,false,反向-空帳號

    Returns:
        list[dict]
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        data = []
        for row in reader:
            # 自動轉型 bool
            for key, val in row.items():
                if val.lower() in ('true', 'false'):
                    row[key] = val.lower() == 'true'
            data.append(row)
        return data


def to_params(data, fields, id_field='id'):
    """
    將 list[dict] 轉為 pytest.param 列表，可直接餵給 @parametrize。

    Args:
        data: load_json / load_csv 的回傳結果
        fields: 要取出的欄位名稱 list，例如 ['email', 'password', 'expected']
        id_field: 用於 pytest.param id 的欄位名（預設 'id'）

    Returns:
        list[pytest.param]

    Usage:
        data = load_json('test_data/login.json')
        LOGIN_CASES = to_params(data, ['email', 'password', 'expected'])

        @pytest.mark.parametrize('email, password, expected', LOGIN_CASES)
        def test_login(self, page, email, password, expected):
            ...
    """
    params = []
    for row in data:
        values = tuple(row.get(f, '') for f in fields)
        test_id = row.get(id_field, '')
        params.append(pytest.param(*values, id=test_id))
    return params


def load_test_data(file_path, fields, id_field='id'):
    """
    一步到位：讀取檔案 → 轉為 pytest.param 列表。

    自動偵測 .json 或 .csv。

    Usage:
        LOGIN_CASES = load_test_data(
            'scenarios/login_test/test_data/login.json',
            fields=['email', 'password', 'expected']
        )

        @pytest.mark.parametrize('email, password, expected', LOGIN_CASES)
        def test_login(self, page, email, password, expected):
            ...
    """
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.json':
        data = load_json(file_path)
    elif ext == '.csv':
        data = load_csv(file_path)
    else:
        raise ValueError(f'不支援的檔案格式: {ext}（支援 .json, .csv）')
    return to_params(data, fields, id_field)
