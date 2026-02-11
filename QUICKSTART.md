# 快速上手指南

新人拿到這個 repo，照著以下步驟走一遍即可上手。

---

## Step 1：環境安裝

```sh
# 建立虛擬環境
python3 -m venv venv
source venv/bin/activate

# 安裝依賴
pip3 install -r requirements.txt
```

**前提：** 機器上需要有 Chrome（或 Firefox / Edge）瀏覽器。

---

## Step 2：確認框架正常（跑單元測試）

```sh
pytest tests/unit/ -v
```

這 116 個測試**不需要瀏覽器**，用 Mock 驗證核心邏輯。
全部綠燈代表框架沒壞。

---

## Step 3：建立你的測試情境

假設你要測試 `https://example.com/login` 這個頁面：

```sh
python generate_scenario.py login_test --url https://example.com/login
```

會在 `scenarios/login_test/` 自動產生：

```
scenarios/login_test/
├── conftest.py       ← 已設好 URL 的 fixture（driver/logger/snapshot）
├── pytest.ini        ← 獨立的 pytest 設定
├── pages/            ← 你的 Page Object 放這裡
├── tests/            ← 你的測試案例放這裡
├── test_data/        ← JSON/CSV 測試資料放這裡
└── results/          ← 截圖、日誌、快照、報告都輸出在這
```

---

## Step 4：寫 Page Object

在 `scenarios/login_test/pages/` 建立你的 Page Object，繼承 `BasePage`：

```python
# scenarios/login_test/pages/login_page.py

from pages.base_page import BasePage
from selenium.webdriver.common.by import By


class LoginPage(BasePage):
    # Locators
    EMAIL_INPUT = (By.ID, 'email')
    PASSWORD_INPUT = (By.ID, 'password')
    LOGIN_BUTTON = (By.ID, 'login-btn')
    ERROR_MESSAGE = (By.CSS_SELECTOR, '.error-msg')

    def __init__(self, driver, url=''):
        super().__init__(driver)
        self.url = url

    def open_login(self):
        self.open(self.url)

    def login(self, email, password):
        self.input_text(*self.EMAIL_INPUT, email)
        self.input_text(*self.PASSWORD_INPUT, password)
        self.click(*self.LOGIN_BUTTON)

    def get_error(self):
        return self.get_element_text(*self.ERROR_MESSAGE)
```

`BasePage` 提供 30+ 現成方法，不需要自己處理等待、截圖、重試。

---

## Step 5：寫測試案例

在 `scenarios/login_test/tests/` 寫測試：

```python
# scenarios/login_test/tests/test_login.py

import pytest
from scenarios.login_test.pages.login_page import LoginPage


@pytest.fixture
def login_page(driver, scenario_url):
    page = LoginPage(driver, url=scenario_url)
    page.open_login()
    return page


class TestLogin:
    @pytest.mark.positive
    def test_valid_login(self, login_page):
        """正向：合法帳密應登入成功。"""
        login_page.login('user@mail.com', 'Pass1234')
        assert 'dashboard' in login_page.get_current_url()

    @pytest.mark.negative
    def test_empty_email(self, login_page):
        """反向：空帳號應顯示錯誤。"""
        login_page.login('', 'Pass1234')
        assert login_page.get_error() != ''

    @pytest.mark.boundary
    def test_long_email(self, login_page):
        """邊界：256 字元帳號。"""
        login_page.login('a' * 256 + '@mail.com', 'Pass1234')
        assert login_page.get_error() != ''
```

---

## Step 5b（進階）：用 JSON 驅動測試資料

把測試資料放在 `test_data/login.json`：

```json
[
    {"email": "user@mail.com", "password": "Pass1234", "expected": true, "id": "正向-合法帳密"},
    {"email": "", "password": "Pass1234", "expected": false, "id": "反向-空帳號"},
    {"email": "aaa...256字元", "password": "Pass1234", "expected": false, "id": "邊界-超長帳號"}
]
```

測試中載入：

```python
from utils.data_loader import load_test_data

CASES = load_test_data('test_data/login.json', fields=['email', 'password', 'expected'])

@pytest.mark.parametrize('email, password, expected', CASES)
def test_login(self, login_page, email, password, expected):
    login_page.login(email, password)
    if expected:
        assert 'dashboard' in login_page.get_current_url()
    else:
        assert login_page.get_error() != ''
```

---

## Step 6：執行測試

```sh
# 全部跑
pytest scenarios/login_test/tests/ -v

# 只跑正向
pytest scenarios/login_test/tests/ -m positive

# 只跑反向
pytest scenarios/login_test/tests/ -m negative

# 只跑邊界
pytest scenarios/login_test/tests/ -m boundary

# 無頭模式（不開瀏覽器視窗，適合 CI/CD）
pytest scenarios/login_test/tests/ -v --headless-mode

# 產出 HTML 報告
pytest scenarios/login_test/tests/ --html=scenarios/login_test/results/report.html
```

---

## Step 7：看結果

測試跑完後，所有輸出都在 `scenarios/login_test/results/`：

```
results/
├── report.html                          ← HTML 報告（需加 --html 參數）
├── scenario_login_test.log              ← 執行日誌
├── test_valid_login_FAIL.png            ← 失敗時自動截圖
└── snapshots/                           ← 每步快照
    └── test_valid_login/
        ├── 001_open_screenshot.png      ← 開啟頁面
        ├── 001_open_page.html           ← 當時的 HTML
        ├── 001_open_state.json          ← 當時的頁面狀態
        ├── 002_input_email_screenshot.png
        ├── 003_input_password_screenshot.png
        ├── 004_click_login-btn_screenshot.png
        └── timeline.json                ← 完整操作時間軸
```

---

## 常用指令速查

| 目的 | 指令 |
|------|------|
| 驗證框架 | `pytest tests/unit/ -v` |
| 建立情境 | `python generate_scenario.py <名稱> --url <URL>` |
| 跑全部測試 | `pytest scenarios/<名稱>/tests/ -v` |
| 只跑正向 | `pytest scenarios/<名稱>/tests/ -m positive` |
| 只跑反向 | `pytest scenarios/<名稱>/tests/ -m negative` |
| 只跑邊界 | `pytest scenarios/<名稱>/tests/ -m boundary` |
| 無頭模式 | 加 `--headless-mode` |
| HTML 報告 | 加 `--html=scenarios/<名稱>/results/report.html` |

---

## 重點觀念

1. **核心不動** — `pages/`、`utils/`、`config/` 是基地，不要改
2. **情境獨立** — 每個任務產生一個 `scenarios/<名稱>/`，互不影響
3. **自動快照** — `open()`、`click()`、`input_text()` 會自動存截圖 + HTML + 狀態
4. **參數化** — 正向/反向/邊界用 `@pytest.mark` 分類，用 JSON/CSV 驅動資料
5. **結果集中** — 截圖、日誌、快照、報告全在 `results/` 目錄
