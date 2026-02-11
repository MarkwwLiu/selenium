"""
data_loader 單元測試
"""

import json
import os
import pytest

from utils.data_loader import load_json, load_csv, to_params, load_test_data


@pytest.fixture
def tmp_dir(tmp_path):
    return tmp_path


@pytest.fixture
def json_file(tmp_dir):
    data = [
        {'email': 'user@mail.com', 'password': 'Pass1234', 'expected': True, 'id': '正向-合法'},
        {'email': '', 'password': 'Pass1234', 'expected': False, 'id': '反向-空帳號'},
    ]
    filepath = tmp_dir / 'test.json'
    filepath.write_text(json.dumps(data, ensure_ascii=False), encoding='utf-8')
    return str(filepath)


@pytest.fixture
def csv_file(tmp_dir):
    content = 'email,password,expected,id\nuser@mail.com,Pass1234,true,正向-合法\n,Pass1234,false,反向-空帳號\n'
    filepath = tmp_dir / 'test.csv'
    filepath.write_text(content, encoding='utf-8')
    return str(filepath)


class TestLoadJson:
    def test_load_json(self, json_file):
        data = load_json(json_file)
        assert len(data) == 2
        assert data[0]['email'] == 'user@mail.com'
        assert data[0]['expected'] is True
        assert data[1]['expected'] is False

    def test_load_json_preserves_types(self, json_file):
        data = load_json(json_file)
        assert isinstance(data[0]['expected'], bool)
        assert isinstance(data[0]['email'], str)


class TestLoadCsv:
    def test_load_csv(self, csv_file):
        data = load_csv(csv_file)
        assert len(data) == 2
        assert data[0]['email'] == 'user@mail.com'

    def test_csv_bool_conversion(self, csv_file):
        data = load_csv(csv_file)
        assert data[0]['expected'] is True
        assert data[1]['expected'] is False

    def test_csv_empty_field(self, csv_file):
        data = load_csv(csv_file)
        assert data[1]['email'] == ''


class TestToParams:
    def test_basic(self):
        data = [
            {'email': 'a@b.com', 'pass': '123', 'id': 'test-1'},
            {'email': 'c@d.com', 'pass': '456', 'id': 'test-2'},
        ]
        params = to_params(data, ['email', 'pass'])
        assert len(params) == 2
        assert params[0].values == ('a@b.com', '123')
        assert params[1].values == ('c@d.com', '456')

    def test_with_id(self):
        data = [{'name': 'Alice', 'id': 'case-alice'}]
        params = to_params(data, ['name'])
        assert params[0].id == 'case-alice'

    def test_custom_id_field(self):
        data = [{'name': 'Bob', 'case_name': 'bob-test'}]
        params = to_params(data, ['name'], id_field='case_name')
        assert params[0].id == 'bob-test'

    def test_missing_field_returns_empty(self):
        data = [{'email': 'a@b.com', 'id': 'test'}]
        params = to_params(data, ['email', 'missing_field'])
        assert params[0].values == ('a@b.com', '')


class TestLoadTestData:
    def test_load_json(self, json_file):
        params = load_test_data(json_file, fields=['email', 'password'])
        assert len(params) == 2

    def test_load_csv(self, csv_file):
        params = load_test_data(csv_file, fields=['email', 'password'])
        assert len(params) == 2

    def test_unsupported_format(self, tmp_dir):
        filepath = tmp_dir / 'test.xml'
        filepath.write_text('<data/>')
        with pytest.raises(ValueError, match='不支援的檔案格式'):
            load_test_data(str(filepath), fields=['email'])
