"""
utils/data_factory.py 單元測試
"""

import pytest
from utils.data_factory import DataFactory


@pytest.fixture
def factory():
    return DataFactory(locale='en_US', seed=42)


class TestUser:
    @pytest.mark.positive
    def test_returns_dict(self, factory):
        user = factory.user()
        assert isinstance(user, dict)
        for key in ('name', 'email', 'phone', 'address', 'birthday', 'username'):
            assert key in user

    @pytest.mark.positive
    def test_email_format(self, factory):
        user = factory.user()
        assert '@' in user['email']

    @pytest.mark.positive
    def test_seed_reproducible(self):
        """同 seed 建立的 factory，第一筆結果應一致。"""
        f1 = DataFactory(locale='en_US', seed=9999)
        user1 = f1.user()
        f2 = DataFactory(locale='en_US', seed=9999)
        user2 = f2.user()
        assert user1['email'] == user2['email']


class TestUsers:
    @pytest.mark.positive
    def test_returns_list(self, factory):
        users = factory.users(count=3)
        assert isinstance(users, list)
        assert len(users) == 3

    @pytest.mark.boundary
    def test_zero_count(self, factory):
        assert factory.users(count=0) == []


class TestPassword:
    @pytest.mark.positive
    def test_default_length(self, factory):
        pw = factory.password()
        assert len(pw) == 12

    @pytest.mark.positive
    def test_custom_length(self, factory):
        pw = factory.password(length=20)
        assert len(pw) == 20

    @pytest.mark.positive
    def test_no_upper(self, factory):
        pw = factory.password(length=50, upper=False, digits=False, special=False)
        assert pw == pw.lower()

    @pytest.mark.positive
    def test_with_special(self, factory):
        pw = factory.password(length=50, special=True)
        specials = set('!@#$%^&*')
        assert any(c in specials for c in pw)

    @pytest.mark.positive
    def test_with_digits(self, factory):
        pw = factory.password(length=50, digits=True)
        assert any(c.isdigit() for c in pw)


class TestWeakPassword:
    @pytest.mark.positive
    def test_returns_known(self, factory):
        known_weak = {'123456', 'password', 'abc', '1234', 'qwerty', '111111', 'aaa'}
        pw = factory.weak_password()
        assert pw in known_weak


class TestFormData:
    @pytest.mark.positive
    def test_default_fields(self, factory):
        data = factory.form_data()
        for key in ('name', 'email', 'phone', 'address'):
            assert key in data

    @pytest.mark.positive
    def test_custom_fields(self, factory):
        data = factory.form_data(fields=['name', 'company', 'url'])
        assert 'name' in data
        assert 'company' in data
        assert 'url' in data

    @pytest.mark.positive
    def test_unknown_field_fallback(self, factory):
        data = factory.form_data(fields=['unknown_xyz'])
        assert 'unknown_xyz' in data
        assert isinstance(data['unknown_xyz'], str)

    @pytest.mark.positive
    def test_all_known_fields(self, factory):
        all_fields = [
            'name', 'first_name', 'last_name', 'email', 'phone', 'address',
            'company', 'city', 'zip_code', 'country', 'url', 'text',
            'sentence', 'paragraph', 'date', 'number', 'credit_card',
            'password', 'username',
        ]
        data = factory.form_data(fields=all_fields)
        for field in all_fields:
            assert field in data


class TestFormDataBatch:
    @pytest.mark.positive
    def test_returns_list(self, factory):
        batch = factory.form_data_batch(count=3)
        assert len(batch) == 3


class TestBoundaryStrings:
    @pytest.mark.boundary
    def test_returns_list(self, factory):
        result = factory.boundary_strings()
        assert isinstance(result, list)
        assert len(result) > 10

    @pytest.mark.boundary
    def test_contains_empty(self, factory):
        result = factory.boundary_strings()
        assert '' in result

    @pytest.mark.boundary
    def test_contains_none(self, factory):
        result = factory.boundary_strings()
        assert None in result

    @pytest.mark.boundary
    def test_custom_max_length(self, factory):
        result = factory.boundary_strings(max_length=10)
        lengths = [len(s) for s in result if isinstance(s, str)]
        assert 10 in lengths  # 最大長度字串
        assert 11 in lengths  # 超過最大長度字串


class TestBoundaryNumbers:
    @pytest.mark.boundary
    def test_default(self, factory):
        result = factory.boundary_numbers()
        assert 0 in result
        assert 100 in result
        assert -1 in result

    @pytest.mark.boundary
    def test_custom_range(self, factory):
        result = factory.boundary_numbers(min_val=10, max_val=20)
        assert 10 in result
        assert 20 in result
        assert 9 in result   # min - 1
        assert 21 in result  # max + 1


class TestBoundaryEmails:
    @pytest.mark.boundary
    def test_returns_list(self, factory):
        result = factory.boundary_emails()
        assert isinstance(result, list)
        assert len(result) >= 8

    @pytest.mark.boundary
    def test_contains_empty(self, factory):
        result = factory.boundary_emails()
        assert '' in result


class TestDateRange:
    @pytest.mark.positive
    def test_returns_dict(self, factory):
        result = factory.date_range()
        for key in ('today', 'past', 'future', 'timestamp', 'iso'):
            assert key in result

    @pytest.mark.positive
    def test_custom_range(self, factory):
        result = factory.date_range(days_back=7, days_forward=7)
        assert result['today'] is not None
