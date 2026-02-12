# 使用指南

---

## 安裝

```sh
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

前提：機器上需要有 Chrome（或 Firefox / Edge）。

---

## 驗證框架

```sh
pytest tests/unit/ -v
```

116 個 unit test 全部綠燈 = 框架正常。

---

## 建立測試情境

```sh
python generate_scenario.py <名稱> --url <URL>
```

範例：
```sh
python generate_scenario.py login_test --url https://example.com/login
```

產生：
```
scenarios/login_test/
├── conftest.py    ← fixtures
├── pages/         ← Page Object
├── tests/         ← 測試案例
├── test_data/     ← 測試資料
└── results/       ← 輸出
```

---

## 寫 Page Object

繼承 `BasePage`，放在情境的 `pages/`：

```python
from pages.base_page import BasePage
from selenium.webdriver.common.by import By

class LoginPage(BasePage):
    EMAIL = (By.ID, 'email')
    PASSWORD = (By.ID, 'password')
    SUBMIT = (By.ID, 'login-btn')

    def login(self, email, password):
        self.input_text(*self.EMAIL, email)
        self.input_text(*self.PASSWORD, password)
        self.click(*self.SUBMIT)
```

---

## 寫測試

放在情境的 `tests/`，用 `@pytest.mark` 分類：

```python
class TestLogin:
    @pytest.mark.positive
    def test_valid_login(self, login_page):
        login_page.login('user@mail.com', 'Pass1234')
        assert 'dashboard' in login_page.get_current_url()

    @pytest.mark.negative
    def test_empty_email(self, login_page):
        login_page.login('', 'Pass1234')
        assert login_page.get_error() != ''
```

---

## 執行測試

```sh
# 全部
pytest scenarios/<名稱>/tests/ -v

# 依分類
pytest scenarios/<名稱>/tests/ -m positive
pytest scenarios/<名稱>/tests/ -m negative
pytest scenarios/<名稱>/tests/ -m boundary

# 無頭模式
pytest scenarios/<名稱>/tests/ -v --headless-mode

# HTML 報告
pytest scenarios/<名稱>/tests/ --html=scenarios/<名稱>/results/report.html
```

---

## 常用指令速查

| 目的 | 指令 |
|------|------|
| 安裝依賴 | `make install` |
| 驗證框架 | `make unit` |
| 建立情境 | `python generate_scenario.py <名稱> --url <URL>` |
| 全部測試 | `make test` |
| 冒煙測試 | `make smoke` |
| 指定情境 | `make scenario S=<名稱>` |
| 平行執行 | `make parallel` |
| 失敗重跑 | `pytest tests/ --reruns 2 --reruns-delay 3` |
| 匯出腳本 | `make export FILE=<測試檔>` |
| 程式碼檢查 | `make lint` |
| 格式化 | `make format` |
| 指定瀏覽器 | `make test BROWSER=firefox` |
| 指定環境 | `make test ENV=staging` |

---

## 測試資料驅動

用 JSON 管理測試資料，搭配 `@pytest.mark.parametrize`：

```json
[
    {"email": "user@mail.com", "password": "Pass1234", "expected": true, "id": "正向-合法帳密"},
    {"email": "", "password": "Pass1234", "expected": false, "id": "反向-空帳號"}
]
```

```python
from utils.data_loader import load_test_data
CASES = load_test_data('test_data/login.json', fields=['email', 'password', 'expected'])

@pytest.mark.parametrize('email, password, expected', CASES)
def test_login(self, page, email, password, expected):
    ...
```

---

## 匯出拋棄式腳本

將測試檔打包成獨立腳本，不需要整個框架：

```sh
python export_test.py scenarios/demo_search/tests/test_search.py
python export_test.py <測試檔> -o output.py --headless
```

匯出的 `.py` 包含 BasePage + Page Object + 測試資料 + Driver，可直接執行。

---

## 進階功能

| 功能 | fixture / 工具 | 範例 |
|------|----------------|------|
| Cookie 管理 | `cookie_manager` | `cookie_manager.save_cookies('path')` |
| Console Log | `console_capture` | `console_capture.assert_no_errors()` |
| 軟斷言 | `soft_assert` | `soft_assert.equal(a, b)` → `soft_assert.assert_all()` |
| 表格解析 | `table_parser` | `table_parser.parse(By.ID, 'table')` |
| 視覺回歸 | `visual_regression` | `visual_regression.check('name', threshold=0.01)` |
| 網路攔截 | `network_interceptor` | `network_interceptor.mock_response(...)` |
| 資料工廠 | `data_factory` | `data_factory.user()` / `data_factory.form_data(...)` |
| Slack 通知 | `SlackNotifier` | 設定 `SLACK_WEBHOOK` 環境變數 |
| Email 通知 | `EmailNotifier` | 設定 `SMTP_HOST` 等環境變數 |
| 多環境 | `--env staging` | `pytest tests/ --env staging` |
