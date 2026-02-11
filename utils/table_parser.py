"""
HTML Table 解析工具

將網頁上的 HTML 表格解析為結構化資料，
適用於後台管理系統、報表頁面等場景。
"""

from selenium.webdriver.common.by import By
from selenium.webdriver.remote.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


class TableParser:
    """
    HTML Table 解析器。

    支援透過 WebDriver 定位表格，或直接傳入表格 WebElement。

    Usage:
        parser = TableParser(driver)
        data = parser.parse(By.ID, 'data-table')
        # data = [{'姓名': '王小明', '年齡': '25'}, {'姓名': '李小華', '年齡': '30'}]

        # 也可以直接傳入 WebElement
        table_el = driver.find_element(By.ID, 'data-table')
        data = parser.parse_element(table_el)
    """

    def __init__(self, driver: WebDriver):
        self.driver = driver

    def parse(self, by, value):
        """
        定位並解析 HTML 表格，回傳 list[dict]。

        每個 dict 的 key 為表頭文字，value 為儲存格文字。
        """
        table = self.driver.find_element(by, value)
        return self.parse_element(table)

    def parse_element(self, table_element):
        """
        解析傳入的 table WebElement，回傳 list[dict]。
        """
        headers = self._get_headers(table_element)
        rows = self._get_body_rows(table_element)

        result = []
        for row in rows:
            cells = row.find_elements(By.TAG_NAME, 'td')
            if not cells:
                continue
            row_data = {}
            for i, cell in enumerate(cells):
                key = headers[i] if i < len(headers) else f'col_{i}'
                row_data[key] = cell.text
            result.append(row_data)

        return result

    def get_headers(self, by, value):
        """取得表格的表頭文字列表。"""
        table = self.driver.find_element(by, value)
        return self._get_headers(table)

    def get_row_count(self, by, value):
        """取得表格的資料列數量（不含表頭）。"""
        table = self.driver.find_element(by, value)
        rows = self._get_body_rows(table)
        return len(rows)

    def get_column_values(self, by, value, column):
        """
        取得指定欄位的所有值。

        Args:
            column: 欄位名稱（str）或欄位索引（int）
        """
        data = self.parse(by, value)
        if isinstance(column, int):
            headers = self.get_headers(by, value)
            if column < len(headers):
                column = headers[column]
            else:
                return []
        return [row.get(column, '') for row in data]

    def find_rows(self, by, value, **conditions):
        """
        搜尋符合條件的列。

        Usage:
            rows = parser.find_rows(By.ID, 'table', 姓名='王小明')
            rows = parser.find_rows(By.ID, 'table', 狀態='啟用', 角色='管理員')
        """
        data = self.parse(by, value)
        result = []
        for row in data:
            match = all(row.get(k) == v for k, v in conditions.items())
            if match:
                result.append(row)
        return result

    def get_cell(self, by, value, row_index, column):
        """
        取得指定儲存格的文字。

        Args:
            row_index: 資料列索引（0-based，不含表頭）
            column: 欄位名稱（str）或欄位索引（int）
        """
        data = self.parse(by, value)
        if row_index >= len(data):
            raise IndexError(f'列索引 {row_index} 超出範圍（共 {len(data)} 列）')
        row = data[row_index]
        if isinstance(column, int):
            headers = self.get_headers(by, value)
            if column < len(headers):
                column = headers[column]
            else:
                raise IndexError(f'欄索引 {column} 超出範圍')
        return row.get(column, '')

    def _get_headers(self, table_element):
        """提取表頭文字。"""
        headers = []
        # 先找 thead > tr > th
        thead = table_element.find_elements(By.TAG_NAME, 'thead')
        if thead:
            th_elements = thead[0].find_elements(By.TAG_NAME, 'th')
            headers = [th.text for th in th_elements]
        if not headers:
            # 找第一列的 th
            first_row = table_element.find_elements(By.TAG_NAME, 'tr')
            if first_row:
                th_elements = first_row[0].find_elements(By.TAG_NAME, 'th')
                headers = [th.text for th in th_elements]
        return headers

    def _get_body_rows(self, table_element):
        """提取資料列（排除表頭列）。"""
        tbody = table_element.find_elements(By.TAG_NAME, 'tbody')
        if tbody:
            return tbody[0].find_elements(By.TAG_NAME, 'tr')
        # 沒有 tbody，跳過第一列（表頭）
        all_rows = table_element.find_elements(By.TAG_NAME, 'tr')
        if all_rows:
            first_row = all_rows[0]
            if first_row.find_elements(By.TAG_NAME, 'th'):
                return all_rows[1:]
        return all_rows
