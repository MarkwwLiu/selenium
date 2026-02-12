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
| Allure 報告 | `python run.py --allure` |
| 指定環境 | 加 `--env staging` 或 `TEST_ENV=prod` |
| 失敗重跑 | 加 `--reruns 2 --reruns-delay 3` |
| 平行執行 | `python run.py --parallel` 或 `-n 4` |
| 匯出腳本 | `python export_test.py <測試檔> -o output.py` |
| Makefile | `make test` / `make smoke` / `make lint` / `make export FILE=...` |

---

## Step 8：使用進階工具

### 檔案上傳

```python
# BasePage 內建方法
page.upload_file(By.ID, 'file-input', '/path/to/document.pdf')
page.upload_files(By.ID, 'file-input', ['/path/a.pdf', '/path/b.jpg'])
```

### 拖曳放置

```python
page.drag_and_drop(By.ID, 'item', By.ID, 'drop-zone')
page.drag_and_drop_by_offset(By.ID, 'slider', 100, 0)
```

### Cookie 管理（跳過重複登入）

```python
def test_with_saved_login(cookie_manager, driver):
    # 首次登入後保存 Cookie
    cookie_manager.save_cookies('cookies/login_state.json')

    # 下次直接載入，不用重新登入
    driver.get('https://example.com')
    cookie_manager.load_cookies('cookies/login_state.json')
    driver.refresh()
```

### Console Log 擷取

```python
def test_no_js_errors(console_capture):
    # ... 執行頁面操作 ...

    # 檢查頁面有沒有 JavaScript 錯誤
    console_capture.assert_no_errors()

    # 或手動查看
    errors = console_capture.get_errors()
    warnings = console_capture.get_warnings()
```

### Soft Assert（不中斷收集失敗）

```python
def test_dashboard(soft_assert, driver):
    soft_assert.equal(driver.title, '儀表板', '標題不正確')
    soft_assert.true(is_menu_visible, '選單應可見')
    soft_assert.contains(page_text, '歡迎', '應包含歡迎訊息')
    soft_assert.greater(item_count, 0, '應有至少一筆資料')

    # 最後統一回報所有失敗
    soft_assert.assert_all()
```

### HTML 表格解析

```python
def test_user_table(table_parser):
    # 解析整張表格
    data = table_parser.parse(By.ID, 'user-table')
    # data = [{'姓名': '王小明', '年齡': '25'}, ...]

    # 搜尋特定列
    admins = table_parser.find_rows(By.ID, 'user-table', 角色='管理員')

    # 取得特定欄位所有值
    names = table_parser.get_column_values(By.ID, 'user-table', '姓名')
```

### 視覺回歸（截圖比對）

```python
@pytest.mark.visual
def test_homepage_visual(visual_regression):
    # 首次執行自動建立 baseline，後續執行比對差異
    result = visual_regression.check('homepage', threshold=0.01)
    assert result['match'], f'UI 差異 {result["diff_ratio"]:.1%}'

    # UI 改版後更新 baseline
    # visual_regression.update_baseline('homepage')
```

### 多環境切換

```sh
# 命令列指定環境
pytest tests/ --env staging

# 環境變數
TEST_ENV=prod pytest tests/
```

```python
def test_with_env(env_config):
    print(env_config['base_url'])   # https://staging.example.com
    print(env_config['env_name'])   # staging
```

### 失敗重跑

```sh
# 失敗自動重跑 2 次，間隔 3 秒
pytest tests/ --reruns 2 --reruns-delay 3
```

---

## Step 9：匯出拋棄式腳本

測試寫好後，可以把任何一個測試檔匯出成獨立腳本，不需要整個框架就能跑：

```sh
# 匯出 demo_search 的測試
python export_test.py scenarios/demo_search/tests/test_search.py

# 指定輸出路徑 + 無頭模式
python export_test.py scenarios/demo_search/tests/test_search.py \
    -o ~/Desktop/run_search.py --headless

# 透過 Makefile
make export FILE=scenarios/demo_search/tests/test_search.py
```

匯出的腳本會自動：
- 內嵌 BasePage 完整程式碼
- 內嵌 Page Object（SearchPage 等）
- 內嵌測試資料（JSON → Python dict）
- 內嵌 Driver 建立邏輯
- 保留所有測試案例和 fixture

直接執行：
```sh
pytest exported_test_search.py -v
python exported_test_search.py
```

適合用途：分享給同事、丟到其他機器跑、一次性驗證、快速 demo。

---

## 重點觀念

1. **核心不動** — `pages/`、`utils/`、`config/` 是基地，不要改
2. **情境獨立** — 每個任務產生一個 `scenarios/<名稱>/`，互不影響
3. **自動快照** — `open()`、`click()`、`input_text()` 會自動存截圖 + HTML + 狀態
4. **參數化** — 正向/反向/邊界用 `@pytest.mark` 分類，用 JSON/CSV 驅動資料
5. **結果集中** — 截圖、日誌、快照、報告全在 `results/` 目錄
