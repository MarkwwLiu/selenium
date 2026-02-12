"""
utils/page_analyzer.py 單元測試
"""

import json
import os
import tempfile
from unittest.mock import MagicMock, patch
from io import StringIO
import pytest

from utils.page_analyzer import PageAnalyzer, SCAN_ELEMENTS_JS


@pytest.fixture
def mock_driver():
    driver = MagicMock()
    driver.page_source = '<html><body>test</body></html>'
    return driver


@pytest.fixture
def analyzer(mock_driver):
    return PageAnalyzer(mock_driver)


def _make_report():
    """建立假的分析報告。"""
    return {
        'url': 'https://example.com',
        'title': '測試頁面',
        'forms': [],
        'inputs': [
            {
                'locator': {'by': 'id', 'value': 'email'},
                'type': 'email',
                'name': 'email',
                'placeholder': '輸入 email',
                'required': True,
                'maxlength': 100,
                'minlength': 5,
                'pattern': '',
                'min': '',
                'max': '',
            },
        ],
        'buttons': [
            {'locator': {'by': 'id', 'value': 'submit'}, 'text': '送出'},
        ],
        'links': [],
        'selects': [
            {
                'locator': {'by': 'id', 'value': 'role'},
                'options': [
                    {'text': '管理員', 'value': 'admin', 'selected': False},
                    {'text': '使用者', 'value': 'user', 'selected': True},
                ],
            },
        ],
        'textareas': [
            {
                'locator': {'by': 'name', 'value': 'bio'},
                'type': 'textarea',
                'name': 'bio',
                'placeholder': '',
                'required': False,
                'maxlength': None,
                'minlength': None,
                'pattern': '',
                'min': '',
                'max': '',
            },
        ],
        'checkboxes': [],
        'radios': [],
        'images': [],
        'tables': [],
        'iframes': [],
    }


class TestInit:
    @pytest.mark.positive
    def test_stores_driver(self, analyzer, mock_driver):
        assert analyzer.driver is mock_driver


class TestAnalyze:
    @pytest.mark.positive
    def test_without_url(self, analyzer, mock_driver):
        mock_driver.execute_script.return_value = _make_report()
        report = analyzer.analyze()
        mock_driver.get.assert_not_called()
        assert 'analyzed_at' in report
        assert 'summary' in report

    @pytest.mark.positive
    def test_with_url(self, analyzer, mock_driver):
        mock_driver.execute_script.return_value = _make_report()
        report = analyzer.analyze('https://example.com')
        mock_driver.get.assert_called_once_with('https://example.com')
        assert report['summary']['inputs'] == 1

    @pytest.mark.positive
    def test_summary_counts(self, analyzer, mock_driver):
        mock_driver.execute_script.return_value = _make_report()
        report = analyzer.analyze()
        summary = report['summary']
        assert summary['inputs'] == 1
        assert summary['buttons'] == 1
        assert summary['selects'] == 1
        assert summary['textareas'] == 1


class TestSaveReport:
    @pytest.mark.positive
    def test_creates_file(self, analyzer):
        report = _make_report()
        with tempfile.TemporaryDirectory() as tmpdir:
            path = analyzer.save_report(report, tmpdir)
            assert os.path.exists(path)
            with open(path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            assert data['url'] == 'https://example.com'


class TestPrintSummary:
    @pytest.mark.positive
    def test_runs_without_error(self, analyzer, capsys):
        report = _make_report()
        report['analyzed_at'] = '2025-01-01T00:00:00'
        report['summary'] = {
            'forms': 0, 'inputs': 1, 'buttons': 1, 'links': 0,
            'selects': 1, 'textareas': 1, 'checkboxes': 0,
            'radios': 0, 'tables': 0, 'iframes': 0,
        }
        analyzer.print_summary(report)
        captured = capsys.readouterr()
        assert '頁面分析報告' in captured.out
        assert 'inputs' in captured.out


class TestGetInputConstraints:
    @pytest.mark.positive
    def test_extracts_inputs(self, analyzer):
        report = _make_report()
        constraints = analyzer.get_input_constraints(report)
        assert len(constraints) == 2  # 1 input + 1 textarea

    @pytest.mark.positive
    def test_input_fields(self, analyzer):
        report = _make_report()
        constraints = analyzer.get_input_constraints(report)
        email = constraints[0]
        assert email['type'] == 'email'
        assert email['required'] is True
        assert email['maxlength'] == 100

    @pytest.mark.positive
    def test_textarea_fields(self, analyzer):
        report = _make_report()
        constraints = analyzer.get_input_constraints(report)
        textarea = constraints[1]
        assert textarea['type'] == 'textarea'
        assert textarea['name'] == 'bio'
