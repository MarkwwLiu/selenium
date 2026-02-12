"""
utils/soft_assert.py 單元測試
"""

import pytest
from utils.soft_assert import SoftAssert


@pytest.fixture
def soft():
    return SoftAssert()


class TestInit:
    @pytest.mark.positive
    def test_empty_failures(self):
        soft = SoftAssert()
        assert soft.failure_count == 0
        assert soft.failures == []


class TestEqual:
    @pytest.mark.positive
    def test_pass(self, soft):
        soft.equal(1, 1)
        assert soft.failure_count == 0

    @pytest.mark.negative
    def test_fail(self, soft):
        soft.equal(1, 2)
        assert soft.failure_count == 1

    @pytest.mark.positive
    def test_custom_message(self, soft):
        soft.equal(1, 2, '數值不符')
        assert soft.failures[0]['message'] == '數值不符'


class TestNotEqual:
    @pytest.mark.positive
    def test_pass(self, soft):
        soft.not_equal(1, 2)
        assert soft.failure_count == 0

    @pytest.mark.negative
    def test_fail(self, soft):
        soft.not_equal(1, 1)
        assert soft.failure_count == 1


class TestTrue:
    @pytest.mark.positive
    def test_pass(self, soft):
        soft.true(True)
        assert soft.failure_count == 0

    @pytest.mark.negative
    def test_fail(self, soft):
        soft.true(False)
        assert soft.failure_count == 1


class TestFalse:
    @pytest.mark.positive
    def test_pass(self, soft):
        soft.false(False)
        assert soft.failure_count == 0

    @pytest.mark.negative
    def test_fail(self, soft):
        soft.false(True)
        assert soft.failure_count == 1


class TestIsNone:
    @pytest.mark.positive
    def test_pass(self, soft):
        soft.is_none(None)
        assert soft.failure_count == 0

    @pytest.mark.negative
    def test_fail(self, soft):
        soft.is_none('not none')
        assert soft.failure_count == 1


class TestIsNotNone:
    @pytest.mark.positive
    def test_pass(self, soft):
        soft.is_not_none('value')
        assert soft.failure_count == 0

    @pytest.mark.negative
    def test_fail(self, soft):
        soft.is_not_none(None)
        assert soft.failure_count == 1


class TestContains:
    @pytest.mark.positive
    def test_pass(self, soft):
        soft.contains('hello world', 'world')
        assert soft.failure_count == 0

    @pytest.mark.negative
    def test_fail(self, soft):
        soft.contains('hello', 'xyz')
        assert soft.failure_count == 1


class TestNotContains:
    @pytest.mark.positive
    def test_pass(self, soft):
        soft.not_contains('hello', 'xyz')
        assert soft.failure_count == 0

    @pytest.mark.negative
    def test_fail(self, soft):
        soft.not_contains('hello', 'ell')
        assert soft.failure_count == 1


class TestGreater:
    @pytest.mark.positive
    def test_pass(self, soft):
        soft.greater(5, 3)
        assert soft.failure_count == 0

    @pytest.mark.negative
    def test_fail(self, soft):
        soft.greater(3, 5)
        assert soft.failure_count == 1

    @pytest.mark.boundary
    def test_equal_values(self, soft):
        soft.greater(3, 3)
        assert soft.failure_count == 1


class TestLess:
    @pytest.mark.positive
    def test_pass(self, soft):
        soft.less(3, 5)
        assert soft.failure_count == 0

    @pytest.mark.negative
    def test_fail(self, soft):
        soft.less(5, 3)
        assert soft.failure_count == 1

    @pytest.mark.boundary
    def test_equal_values(self, soft):
        soft.less(3, 3)
        assert soft.failure_count == 1


class TestProperties:
    @pytest.mark.positive
    def test_failure_count(self, soft):
        soft.equal(1, 2)
        soft.true(False)
        assert soft.failure_count == 2

    @pytest.mark.positive
    def test_failures_is_copy(self, soft):
        soft.equal(1, 2)
        failures = soft.failures
        failures.clear()
        assert soft.failure_count == 1


class TestAssertAll:
    @pytest.mark.positive
    def test_no_failures(self, soft):
        soft.equal(1, 1)
        soft.assert_all()

    @pytest.mark.negative
    def test_with_failures(self, soft):
        soft.equal(1, 2)
        soft.true(False)
        with pytest.raises(AssertionError, match='2 個失敗'):
            soft.assert_all()

    @pytest.mark.positive
    def test_failure_details_in_message(self, soft):
        soft.equal('a', 'b', '值不符')
        with pytest.raises(AssertionError) as exc_info:
            soft.assert_all()
        assert '值不符' in str(exc_info.value)
