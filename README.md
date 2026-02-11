# Selenium 自動化測試框架

使用 **Selenium + pytest + Page Object Model** 的自動化測試框架。
提供「基地核心」+「獨立情境模組」的雙層架構，核心不動、每個測試任務自動產生獨立模組。

---

## 專案結構

```
selenium/
│
├── 🔧 核心框架（基地，不動）
│   ├── pages/
│   │   ├── base_page.py              # 基礎頁面：30+ 共用操作方法 + 自動快照
│   │   └── home_page.py              # 範例 Page Object
│   ├── utils/
│   │   ├── driver_factory.py         # WebDriver 工廠（Chrome/Firefox/Edge）
│   │   ├── screenshot.py             # 截圖工具
│   │   ├── logger.py                 # 日誌工具
│   │   ├── retry.py                  # 重試裝飾器（處理不穩定元素）
│   │   ├── data_loader.py            # 測試資料載入器（JSON/CSV → @parametrize）
│   │   ├── waiter.py                 # 進階等待工具（AJAX/元素穩定/屬性變化）
│   │   ├── page_analyzer.py          # 頁面元素分析器（自動掃描 + locator 產生）
│   │   ├── page_snapshot.py          # 頁面快照（截圖+HTML+狀態+時間軸）
│   │   └── test_generator.py         # 測試案例自動產生器
│   ├── config/
│   │   └── settings.py               # 全域設定（瀏覽器/等待/截圖/日誌）
│   ├── conftest.py                   # 根層級 pytest fixtures
│   ├── pytest.ini                    # pytest 設定 + markers
│   └── generate_scenario.py          # 情境模組產生器
│
├── tests/                             # 根層級測試（核心功能驗證用）
│
└── scenarios/                         # 獨立情境模組（每個任務一個）
    ├── _template/                     # 模板（產生器複製用）
    │   ├── conftest.py                # 完整 fixture 配置
    │   ├── pytest.ini                 # 獨立 pytest 設定
    │   ├── pages/                     # 情境專屬 Page Object
    │   ├── tests/                     # 情境專屬測試
    │   ├── test_data/                 # JSON/CSV 測試資料
    │   └── results/                   # 截圖/日誌/快照/報告
    └── demo_search/                   # 範例情境
        ├── conftest.py
        ├── pages/search_page.py
        ├── tests/test_search.py
        ├── test_data/search.json
        └── results/
```

---

## 工作流程

### 給 URL → 自動產生完整測試

```
┌─────────────────────────────────────────────────────┐
│  1. 輸入 URL                                         │
│     https://example.com/login                        │
└──────────────┬──────────────────────────────────────┘
               ▼
┌─────────────────────────────────────────────────────┐
│  2. PageAnalyzer 自動掃描頁面                         │
│     ├─ JS 注入掃描所有互動元素                         │
│     ├─ input / button / select / checkbox / radio    │
│     ├─ link / table / textarea / iframe              │
│     ├─ 自動產生最佳 locator                           │
│     │   (id > name > data-testid > css > xpath)      │
│     └─ 提取驗證限制                                   │
│        (required / maxlength / pattern / min / max)  │
└──────────────┬──────────────────────────────────────┘
               ▼
┌─────────────────────────────────────────────────────┐
│  3. TestGenerator 自動推測測試資料                     │
│     ├─ email  → 正向: user@example.com               │
│     │           反向: 空值, @no-local                 │
│     │           邊界: 256 字元                        │
│     ├─ password → 正向: P@ssw0rd123                  │
│     │             反向: 空值                          │
│     │             邊界: 1 字元, 128 字元              │
│     └─ number → 正向: 42                             │
│                 反向: abc                             │
│                 邊界: min-1, max+1                    │
└──────────────┬──────────────────────────────────────┘
               ▼
┌─────────────────────────────────────────────────────┐
│  4. 自動產生檔案到 scenarios/xxx/                      │
│     ├─ pages/xxx_page.py     ← Page Object 骨架      │
│     ├─ tests/test_xxx.py     ← pytest 測試檔案       │
│     ├─ test_data/data.json   ← 正向/反向/邊界資料     │
│     └─ results/              ← 輸出目錄              │
└──────────────┬──────────────────────────────────────┘
               ▼
┌─────────────────────────────────────────────────────┐
│  5. 執行測試，每步自動快照                             │
│     ├─ open   → 001_open_screenshot.png              │
│     ├─ input  → 002_input_email_screenshot.png       │
│     ├─ click  → 003_click_submit_screenshot.png      │
│     ├─ 每步同時存 HTML + 表單狀態 JSON                │
│     └─ 產出 timeline.json（完整操作時間軸）            │
└─────────────────────────────────────────────────────┘
```

---

## 快速開始

### 安裝

```sh
python3 -m venv venv
source venv/bin/activate
pip3 install -r requirements.txt
```

### 執行根層級測試

```sh
pytest                                    # 全部
pytest -m smoke                           # 冒煙測試
pytest --browser firefox --headless-mode  # Firefox 無頭模式
python3 run.py --html                     # HTML 報告
```

### 建立新情境模組

```sh
python generate_scenario.py login_test --url https://example.com/login
```

產生結果：
```
scenarios/login_test/
├── conftest.py       ← driver/logger/snapshot/analyzer fixture
├── pytest.ini
├── pages/
├── tests/
├── test_data/
└── results/
```

### 執行情境測試

```sh
pytest scenarios/login_test/tests/ -v            # 全部
pytest scenarios/login_test/tests/ -m positive    # 只跑正向
pytest scenarios/login_test/tests/ -m negative    # 只跑反向
pytest scenarios/login_test/tests/ -m boundary    # 只跑邊界

# 產出 HTML 報告到情境目錄
pytest scenarios/login_test/tests/ --html=scenarios/login_test/results/report.html
```

---

## 核心工具一覽

### BasePage 方法（pages/base_page.py）

| 分類 | 方法 |
|------|------|
| **導航** | `open()` `refresh()` `go_back()` `get_title()` `get_current_url()` |
| **查找** | `find_element()` `find_elements()` `is_element_present()` |
| **等待** | `wait_for_element()` `wait_for_visible()` `wait_for_clickable()` `wait_for_invisible()` `wait_for_text_present()` `wait_for_url_contains()` |
| **互動** | `click()` `input_text()` `clear_and_type()` `get_element_text()` `get_element_attribute()` `get_input_value()` |
| **下拉** | `select_by_value()` `select_by_text()` `select_by_index()` |
| **勾選** | `is_selected()` `set_checkbox()` |
| **滾動** | `scroll_to_element()` `scroll_to_bottom()` `scroll_to_top()` |
| **框架** | `switch_to_iframe()` `switch_to_default()` `switch_to_window()` |
| **彈窗** | `accept_alert()` `dismiss_alert()` `get_alert_text()` |
| **滑鼠** | `hover()` `double_click()` `right_click()` |
| **JS** | `execute_js()` `js_click()` |
| **狀態** | `is_enabled()` `is_displayed()` `get_elements_text()` `get_element_count()` |
| **快照** | `enable_snapshot()` — open/click/input/select 自動觸發快照 |

### 工具模組（utils/）

| 工具 | 用途 | 使用方式 |
|------|------|----------|
| **page_analyzer.py** | 掃描頁面所有互動元素，產生結構化報告 | `analyzer.analyze(url)` → JSON |
| **page_snapshot.py** | 每步存截圖+HTML+狀態，支援差異比對 | `snapshot.take('label')` / `snapshot.diff(0, 1)` |
| **test_generator.py** | 根據元素限制自動產生測試值+程式碼 | `generate_test_data()` / `generate_page_object()` |
| **data_loader.py** | JSON/CSV → pytest.param 列表 | `load_test_data('data.json', ['email', 'pass'])` |
| **retry.py** | 重試裝飾器，處理不穩定元素 | `@retry(max_attempts=3)` / `@retry_on_stale` |
| **waiter.py** | 進階等待（AJAX/元素穩定/屬性變化） | `waiter.wait_for_ajax()` / `waiter.wait_for_stable()` |

### Markers

| Marker | 用途 | 執行 |
|--------|------|------|
| `@pytest.mark.smoke` | 冒煙測試 | `pytest -m smoke` |
| `@pytest.mark.regression` | 迴歸測試 | `pytest -m regression` |
| `@pytest.mark.positive` | 正向測試 | `pytest -m positive` |
| `@pytest.mark.negative` | 反向測試 | `pytest -m negative` |
| `@pytest.mark.boundary` | 邊界測試 | `pytest -m boundary` |

---

## 情境模組 Fixture 一覽

每個情境的 `conftest.py` 自動提供：

| Fixture | Scope | 說明 |
|---------|-------|------|
| `driver` | session | WebDriver 實例 |
| `logger` | session | 日誌寫入情境 `results/` |
| `waiter` | session | 進階等待工具 |
| `analyzer` | session | 頁面元素分析器 |
| `snapshot` | function | 快照管理器，存到 `results/snapshots/` |
| `scenario_url` | function | 情境目標 URL |
| `test_lifecycle` | autouse | 自動紀錄 + 失敗截圖 |

---

## 參數化測試（正向 / 反向 / 邊界）

### 方式一：直接寫在程式碼

```python
POSITIVE_CASES = [
    pytest.param('user@mail.com', 'Pass1234', True, id='正向-合法帳密'),
]
NEGATIVE_CASES = [
    pytest.param('', 'Pass1234', False, id='反向-空帳號'),
]
BOUNDARY_CASES = [
    pytest.param('a' * 256, 'Pass1234', False, id='邊界-帳號256字元'),
]

class TestLogin:
    @pytest.mark.positive
    @pytest.mark.parametrize('email, password, expected', POSITIVE_CASES)
    def test_positive(self, page, email, password, expected): ...

    @pytest.mark.negative
    @pytest.mark.parametrize('email, password, expected', NEGATIVE_CASES)
    def test_negative(self, page, email, password, expected): ...

    @pytest.mark.boundary
    @pytest.mark.parametrize('email, password, expected', BOUNDARY_CASES)
    def test_boundary(self, page, email, password, expected): ...
```

### 方式二：從 JSON/CSV 載入

```json
[
    {"email": "user@mail.com", "password": "Pass1234", "expected": true, "id": "正向-合法帳密"},
    {"email": "", "password": "Pass1234", "expected": false, "id": "反向-空帳號"}
]
```

```python
from utils.data_loader import load_test_data

LOGIN_CASES = load_test_data('test_data/login.json', fields=['email', 'password', 'expected'])

@pytest.mark.parametrize('email, password, expected', LOGIN_CASES)
def test_login(self, page, email, password, expected): ...
```

---

## 快照輸出結構

啟用快照後，`results/snapshots/` 每個測試會有：

```
results/snapshots/test_login[user@mail.com]/
├── 001_open_screenshot.png
├── 001_open_page.html
├── 001_open_state.json            # {url, title, form_values, ...}
├── 002_input_email_screenshot.png
├── 002_input_email_page.html
├── 002_input_email_state.json
├── 003_click_submit_screenshot.png
├── 003_click_submit_page.html
├── 003_click_submit_state.json
└── timeline.json                  # 完整操作時間軸
```

---

## 設定檔（config/settings.py）

```python
BROWSER = 'chrome'            # 'chrome' / 'firefox' / 'edge'
HEADLESS = False              # True = 無頭模式（CI/CD）
IMPLICIT_WAIT = 10            # 隱式等待秒數
BASE_URL = 'https://...'      # 根層級測試目標
TEARDOWN_WAIT = 3             # 每個測試結束後等待
SCREENSHOT_ON_FAILURE = True  # 失敗時自動截圖
LOG_ENABLED = True            # 啟用日誌
```
