"""
utils/table_parser.py 單元測試
"""

from unittest.mock import MagicMock
import pytest
from selenium.webdriver.common.by import By

from utils.table_parser import TableParser


def _make_element(text='', tag_name='td', children=None):
    """建立 mock WebElement。"""
    el = MagicMock()
    el.text = text
    el.tag_name = tag_name
    el.find_elements.return_value = children or []
    return el


def _build_table_with_thead(headers, rows):
    """建立帶有 thead 的 mock table element。"""
    th_elements = [_make_element(h, 'th') for h in headers]
    thead = MagicMock()
    thead.find_elements.return_value = th_elements

    body_rows = []
    for row_data in rows:
        cells = [_make_element(cell, 'td') for cell in row_data]
        tr = MagicMock()
        tr.find_elements.return_value = cells
        body_rows.append(tr)

    tbody = MagicMock()
    tbody.find_elements.return_value = body_rows

    table = MagicMock()

    def find_elements_side_effect(by, tag):
        if tag == 'thead':
            return [thead]
        if tag == 'tbody':
            return [tbody]
        return []

    table.find_elements.side_effect = find_elements_side_effect
    return table


def _build_table_no_thead(header_texts, rows):
    """建立沒有 thead、第一列為 th 的 mock table。"""
    header_row = MagicMock()
    th_elements = [_make_element(h, 'th') for h in header_texts]
    header_row.find_elements.side_effect = lambda by, tag: th_elements if tag == 'th' else []

    body_rows = []
    for row_data in rows:
        cells = [_make_element(cell, 'td') for cell in row_data]
        tr = MagicMock()
        tr.find_elements.side_effect = lambda by, tag, c=cells: c if tag == 'td' else []
        body_rows.append(tr)

    all_rows = [header_row] + body_rows

    table = MagicMock()

    def find_elements_side_effect(by, tag):
        if tag == 'thead':
            return []
        if tag == 'tbody':
            return []
        if tag == 'tr':
            return all_rows
        return []

    table.find_elements.side_effect = find_elements_side_effect
    return table


@pytest.fixture
def mock_driver():
    return MagicMock()


@pytest.fixture
def parser(mock_driver):
    return TableParser(mock_driver)


class TestParseElement:
    @pytest.mark.positive
    def test_basic_table(self, parser):
        table = _build_table_with_thead(
            ['姓名', '年齡'],
            [['王小明', '25'], ['李小華', '30']]
        )
        result = parser.parse_element(table)
        assert len(result) == 2
        assert result[0]['姓名'] == '王小明'
        assert result[1]['年齡'] == '30'

    @pytest.mark.boundary
    def test_extra_columns(self, parser):
        """儲存格比表頭多時用 col_N。"""
        table = _build_table_with_thead(
            ['A'],
            [['1', '2']]
        )
        result = parser.parse_element(table)
        assert result[0]['A'] == '1'
        assert result[0]['col_1'] == '2'

    @pytest.mark.boundary
    def test_empty_row(self, parser):
        """沒有 td 的列被跳過。"""
        table = _build_table_with_thead(['A'], [])
        result = parser.parse_element(table)
        assert result == []


class TestParse:
    @pytest.mark.positive
    def test_locates_and_parses(self, parser, mock_driver):
        table = _build_table_with_thead(['X'], [['1']])
        mock_driver.find_element.return_value = table
        result = parser.parse(By.ID, 'tbl')
        mock_driver.find_element.assert_called_once_with(By.ID, 'tbl')
        assert len(result) == 1


class TestGetHeaders:
    @pytest.mark.positive
    def test_with_thead(self, parser, mock_driver):
        table = _build_table_with_thead(['A', 'B'], [])
        mock_driver.find_element.return_value = table
        headers = parser.get_headers(By.ID, 'tbl')
        assert headers == ['A', 'B']

    @pytest.mark.positive
    def test_no_thead(self, parser, mock_driver):
        table = _build_table_no_thead(['X', 'Y'], [])
        mock_driver.find_element.return_value = table
        headers = parser.get_headers(By.ID, 'tbl')
        assert headers == ['X', 'Y']


class TestGetRowCount:
    @pytest.mark.positive
    def test_count(self, parser, mock_driver):
        table = _build_table_with_thead(['A'], [['1'], ['2'], ['3']])
        mock_driver.find_element.return_value = table
        assert parser.get_row_count(By.ID, 'tbl') == 3


class TestGetColumnValues:
    @pytest.mark.positive
    def test_by_name(self, parser, mock_driver):
        table = _build_table_with_thead(['姓名', '年齡'], [['A', '1'], ['B', '2']])
        mock_driver.find_element.return_value = table
        values = parser.get_column_values(By.ID, 'tbl', '姓名')
        assert values == ['A', 'B']

    @pytest.mark.positive
    def test_by_index(self, parser, mock_driver):
        table = _build_table_with_thead(['姓名', '年齡'], [['A', '1'], ['B', '2']])
        mock_driver.find_element.return_value = table
        values = parser.get_column_values(By.ID, 'tbl', 0)
        assert values == ['A', 'B']

    @pytest.mark.boundary
    def test_index_out_of_range(self, parser, mock_driver):
        table = _build_table_with_thead(['A'], [['1']])
        mock_driver.find_element.return_value = table
        values = parser.get_column_values(By.ID, 'tbl', 99)
        assert values == []


class TestFindRows:
    @pytest.mark.positive
    def test_match(self, parser, mock_driver):
        table = _build_table_with_thead(
            ['姓名', '狀態'],
            [['A', '啟用'], ['B', '停用'], ['C', '啟用']]
        )
        mock_driver.find_element.return_value = table
        rows = parser.find_rows(By.ID, 'tbl', **{'狀態': '啟用'})
        assert len(rows) == 2

    @pytest.mark.negative
    def test_no_match(self, parser, mock_driver):
        table = _build_table_with_thead(['姓名'], [['A']])
        mock_driver.find_element.return_value = table
        rows = parser.find_rows(By.ID, 'tbl', **{'姓名': 'Z'})
        assert rows == []


class TestGetCell:
    @pytest.mark.positive
    def test_by_column_name(self, parser, mock_driver):
        table = _build_table_with_thead(['A', 'B'], [['x', 'y']])
        mock_driver.find_element.return_value = table
        assert parser.get_cell(By.ID, 'tbl', 0, 'B') == 'y'

    @pytest.mark.positive
    def test_by_column_index(self, parser, mock_driver):
        table = _build_table_with_thead(['A', 'B'], [['x', 'y']])
        mock_driver.find_element.return_value = table
        assert parser.get_cell(By.ID, 'tbl', 0, 0) == 'x'

    @pytest.mark.negative
    def test_row_out_of_range(self, parser, mock_driver):
        table = _build_table_with_thead(['A'], [['x']])
        mock_driver.find_element.return_value = table
        with pytest.raises(IndexError, match='列索引'):
            parser.get_cell(By.ID, 'tbl', 5, 'A')

    @pytest.mark.negative
    def test_column_index_out_of_range(self, parser, mock_driver):
        table = _build_table_with_thead(['A'], [['x']])
        mock_driver.find_element.return_value = table
        with pytest.raises(IndexError, match='欄索引'):
            parser.get_cell(By.ID, 'tbl', 0, 99)
