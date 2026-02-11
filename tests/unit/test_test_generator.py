"""
test_generator 單元測試
"""

import json
import os
import pytest

from utils.test_generator import (
    _get_values_for_input,
    _to_var_name,
    generate_test_data,
    generate_page_object,
    generate_test_file,
)


class TestToVarName:
    def test_basic(self):
        assert _to_var_name('email') == 'email'

    def test_with_special_chars(self):
        assert _to_var_name('user-name') == 'user_name'

    def test_with_spaces(self):
        assert _to_var_name('first name') == 'first_name'

    def test_starts_with_digit(self):
        result = _to_var_name('123abc')
        assert result.startswith('field_')
        assert not result[0].isdigit()

    def test_empty_string(self):
        result = _to_var_name('')
        assert result.startswith('field_')

    def test_consecutive_specials(self):
        assert _to_var_name('a--b__c') == 'a_b_c'

    def test_uppercase_to_lower(self):
        assert _to_var_name('UserName') == 'username'


class TestGetValuesForInput:
    def test_text_type(self):
        pos, neg, bnd = _get_values_for_input({'type': 'text'})
        assert len(pos) > 0
        assert '' in neg
        assert any(len(v) > 200 for v in bnd)

    def test_email_type(self):
        pos, neg, bnd = _get_values_for_input({'type': 'email'})
        assert any('@' in v for v in pos)
        assert '' in neg
        assert any('not-an-email' == v for v in neg)

    def test_password_type(self):
        pos, neg, bnd = _get_values_for_input({'type': 'password'})
        assert len(pos) > 0
        assert '' in neg

    def test_number_type(self):
        pos, neg, bnd = _get_values_for_input({'type': 'number'})
        assert '42' in pos
        assert 'abc' in neg

    def test_unknown_type_falls_back_to_text(self):
        pos, neg, bnd = _get_values_for_input({'type': 'unknown_type'})
        text_pos, _, _ = _get_values_for_input({'type': 'text'})
        assert pos == text_pos

    def test_maxlength_adds_boundary(self):
        _, _, bnd = _get_values_for_input({'type': 'text', 'maxlength': 10})
        assert 'a' * 10 in bnd      # 等於上限
        assert 'a' * 11 in bnd      # 超過上限
        assert 'a' * 9 in bnd       # 差一個

    def test_minlength_adds_boundary(self):
        _, _, bnd = _get_values_for_input({'type': 'text', 'minlength': 5})
        assert 'a' * 5 in bnd       # 等於下限
        assert 'a' * 4 in bnd       # 差一個

    def test_min_max_number(self):
        _, _, bnd = _get_values_for_input({'type': 'number', 'min': '1', 'max': '100'})
        assert '1' in bnd
        assert '0' in bnd           # min - 1
        assert '100' in bnd
        assert '101' in bnd         # max + 1

    def test_required_adds_empty_to_negative(self):
        _, neg, _ = _get_values_for_input({'type': 'text', 'required': True})
        assert '' in neg

    def test_deduplication(self):
        _, _, bnd = _get_values_for_input({'type': 'text', 'maxlength': 255})
        # 'a' * 255 出現在基礎 boundary 和 maxlength boundary，應去重
        assert bnd.count('a' * 255) == 1


class TestGenerateTestData:
    def test_basic(self):
        constraints = [
            {
                'locator': {'by': 'id', 'value': 'email'},
                'type': 'email',
                'name': 'email',
                'required': True,
            }
        ]
        result = generate_test_data(constraints)
        assert 'email' in result
        assert 'positive' in result['email']
        assert 'negative' in result['email']
        assert 'boundary' in result['email']

    def test_uses_locator_value_as_fallback_name(self):
        constraints = [
            {
                'locator': {'by': 'css', 'value': '.input-field'},
                'type': 'text',
                'name': '',
            }
        ]
        result = generate_test_data(constraints)
        assert '.input-field' in result

    def test_output_to_file(self, tmp_path):
        constraints = [
            {
                'locator': {'by': 'id', 'value': 'name'},
                'type': 'text',
                'name': 'name',
            }
        ]
        output_path = str(tmp_path / 'data' / 'test.json')
        generate_test_data(constraints, output_path=output_path)
        assert os.path.exists(output_path)

        with open(output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert 'name' in data


class TestGeneratePageObject:
    def test_generates_file(self, tmp_path):
        report = {
            'url': 'https://example.com/login',
            'inputs': [
                {'locator': {'by': 'id', 'value': 'email'}, 'name': 'email', 'id': 'email', 'placeholder': 'Email'},
                {'locator': {'by': 'id', 'value': 'password'}, 'name': 'password', 'id': 'password', 'placeholder': ''},
            ],
            'buttons': [
                {'locator': {'by': 'css', 'value': '.btn-submit'}, 'name': '', 'id': '', 'text': 'Login'},
            ],
            'selects': [],
            'textareas': [],
        }
        output = str(tmp_path / 'pages' / 'login_page.py')
        generate_page_object(report, 'login_test', output)
        assert os.path.exists(output)

        content = open(output, 'r', encoding='utf-8').read()
        assert 'class LoginTestPage(BasePage)' in content
        assert 'EMAIL' in content
        assert 'PASSWORD' in content
        assert 'BTN_LOGIN' in content
        assert 'def fill_email' in content
        assert 'def click_login' in content
        assert 'def open_page' in content

    def test_class_name_from_scenario_name(self, tmp_path):
        report = {'url': '', 'inputs': [], 'buttons': [], 'selects': [], 'textareas': []}
        output = str(tmp_path / 'page.py')
        generate_page_object(report, 'user_registration', output)
        content = open(output, 'r', encoding='utf-8').read()
        assert 'class UserRegistrationPage' in content


class TestGenerateTestFile:
    def test_generates_file(self, tmp_path):
        test_data = {
            'email': {
                'locator': {'by': 'id', 'value': 'email'},
                'type': 'email',
                'required': True,
                'positive': ['user@mail.com'],
                'negative': ['', 'bad'],
                'boundary': ['a@b.co'],
            }
        }
        output = str(tmp_path / 'tests' / 'test_login.py')
        generate_test_file(test_data, 'LoginPage', 'pages.login_page', output)
        assert os.path.exists(output)

        content = open(output, 'r', encoding='utf-8').read()
        assert 'from pages.login_page import LoginPage' in content
        assert 'def test_email_positive' in content
        assert 'def test_email_negative' in content
        assert 'def test_email_boundary' in content
        assert '@pytest.mark.positive' in content
        assert '@pytest.mark.negative' in content
        assert '@pytest.mark.boundary' in content
