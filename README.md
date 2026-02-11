# Selenium 自動化測試專案

使用 **Selenium + pytest** 搭配 **Page Object Model (POM)** 設計模式的自動化測試專案。

**功能特色：**
- Page Object Model 設計模式，頁面操作與測試邏輯分離
- **pytest** 測試框架，支援 fixture、marker、參數化等進階功能
- WebDriver Factory 支援 Chrome / Firefox / Edge + Headless 模式
- 測試失敗自動截圖，方便除錯追蹤
- 結構化日誌系統，同時輸出到終端機與檔案
- **pytest-html** 產生互動式 HTML 測試報告
- `run.py` 統一執行入口，支援命令列參數

---

## 專案結構

```
selenium/
├── config/                        # 設定檔
│   ├── __init__.py
│   └── settings.py                # 集中管理所有可配置參數
├── pages/                         # Page Object Model（頁面物件）
│   ├── __init__.py
│   ├── base_page.py               # 基礎頁面：共用的瀏覽器操作方法
│   └── home_page.py               # 首頁頁面：封裝首頁的元素定位與操作
├── tests/                         # 測試案例
│   ├── __init__.py
│   └── test_home_page.py          # 首頁測試
├── utils/                         # 工具模組
│   ├── __init__.py
│   ├── driver_factory.py          # WebDriver 工廠：多瀏覽器 + Headless
│   ├── screenshot.py              # 截圖工具：失敗時自動擷取畫面
│   └── logger.py                  # 日誌工具：結構化日誌紀錄
├── reports/                       # 測試報告輸出目錄
├── screenshots/                   # 失敗截圖輸出目錄
├── logs/                          # 日誌檔案目錄
├── conftest.py                    # pytest 共用 fixtures（driver, logger, 截圖）
├── pytest.ini                     # pytest 設定檔
├── run.py                         # 統一測試執行入口
├── requirements.txt               # Python 依賴套件
├── .gitignore
└── README.md
```

---

## 架構設計說明

### Page Object Model (POM)

將「頁面操作」與「測試邏輯」分離，提升維護性：

| 層級 | 檔案 | 職責 |
|------|------|------|
| **Config** | `config/settings.py` | 集中管理所有可配置參數 |
| **Utils** | `utils/driver_factory.py` | 根據設定建立對應瀏覽器的 WebDriver |
| **Utils** | `utils/screenshot.py` | 測試失敗時自動截圖 |
| **Utils** | `utils/logger.py` | 日誌紀錄（終端機 + 檔案） |
| **Base Page** | `pages/base_page.py` | 封裝共用的瀏覽器操作 |
| **Page Object** | `pages/home_page.py` | 定義頁面元素定位器與操作方法 |
| **Fixtures** | `conftest.py` | WebDriver 初始化 / 關閉 / 截圖 / 日誌 |
| **Test Case** | `tests/test_home_page.py` | 撰寫測試斷言，只關注「要驗證什麼」 |

### pytest Fixtures 架構

```
conftest.py
├── pytest_addoption()          # 註冊 --browser, --headless-mode 參數
├── logger (session scope)      # 整個 session 共用一個 Logger
├── driver (session scope)      # 整個 session 共用一個 WebDriver
├── pytest_runtest_makereport() # Hook：將測試結果附加到 item
└── test_lifecycle (autouse)    # 自動套用：紀錄開始/結束、失敗截圖
```

---

## 環境需求

- Python 3.8+
- 瀏覽器（至少安裝一種）：Google Chrome / Firefox / Microsoft Edge

---

## 安裝步驟

### 1. 建立虛擬環境（建議）

```sh
python3 -m venv venv
source venv/bin/activate   # macOS / Linux
# venv\Scripts\activate    # Windows
```

### 2. 安裝依賴套件

```sh
pip3 install -r requirements.txt
```

安裝的套件：
- `selenium` - 瀏覽器自動化框架
- `webdriver-manager` - 自動下載對應版本的瀏覽器驅動
- `pytest` - Python 測試框架
- `pytest-html` - 產生 HTML 格式的測試報告

---

## 執行測試

### 方式一：使用 `run.py`（推薦）

```sh
# 預設執行（Chrome，有畫面，終端機輸出）
python3 run.py

# 指定瀏覽器
python3 run.py --browser firefox
python3 run.py --browser edge

# 無頭模式（不顯示瀏覽器視窗，適用於 CI/CD）
python3 run.py --headless

# 產生 HTML 報告
python3 run.py --html

# 只跑 smoke 標籤的測試
python3 run.py -m smoke

# 只跑名稱含特定關鍵字的測試
python3 run.py -k "keyword"

# 組合使用
python3 run.py --browser firefox --headless --html
```

### 方式二：直接使用 pytest

```sh
# 執行所有測試
pytest

# 執行特定檔案
pytest tests/test_home_page.py

# 執行特定測試
pytest tests/test_home_page.py::TestHomePage::test_entry_title_is_correct

# 產生 HTML 報告
pytest --html=reports/report.html --self-contained-html

# 依標籤篩選
pytest -m smoke
pytest -m regression

# 依名稱篩選
pytest -k "title"

# 指定瀏覽器 + 無頭模式
pytest --browser firefox --headless-mode
```

---

## 設定說明

所有可配置的參數集中在 `config/settings.py`：

```python
# === 瀏覽器設定 ===
BROWSER = 'chrome'           # 支援: 'chrome', 'firefox', 'edge'
HEADLESS = False              # True = 無頭模式（適用於 CI/CD）
IMPLICIT_WAIT = 10            # 隱式等待秒數

# === 測試目標 ===
BASE_URL = 'https://shareboxnow.com/'

# === 截圖設定 ===
SCREENSHOT_ON_FAILURE = True  # 測試失敗時是否自動截圖

# === 日誌設定 ===
LOG_ENABLED = True            # 是否啟用日誌紀錄到檔案
```

---

## 功能說明

### 多瀏覽器支援

透過 `utils/driver_factory.py` 的 **WebDriver Factory** 模式，一行設定切換瀏覽器：

```python
# config/settings.py
BROWSER = 'firefox'  # 切換為 Firefox
```

或在命令列直接指定：

```sh
python3 run.py --browser edge
# 或
pytest --browser edge
```

### 測試標籤（Markers）

使用 `@pytest.mark` 為測試分類：

```python
@pytest.mark.smoke
def test_critical_feature(self, home_page):
    ...

@pytest.mark.regression
def test_edge_case(self, home_page):
    ...
```

執行時篩選：

```sh
pytest -m smoke            # 只跑冒煙測試
pytest -m "not regression" # 跳過迴歸測試
```

### 失敗自動截圖

測試失敗時，系統會自動擷取瀏覽器當前畫面，儲存到 `screenshots/` 目錄：

```
screenshots/
├── test_entry_title_is_correct_20240101_143022.png
└── test_entry_title_contains_keyword_20240101_143025.png
```

### 日誌系統

日誌同時輸出到終端機和 `logs/` 目錄的檔案中：

```
2024-01-01 14:30:20 [INFO] selenium_test - ===== 啟動測試 Session =====
2024-01-01 14:30:20 [INFO] selenium_test - 瀏覽器: chrome | Headless: False
2024-01-01 14:30:22 [INFO] selenium_test - WebDriver 初始化完成
2024-01-01 14:30:22 [INFO] selenium_test - ▶ 執行: test_entry_title_is_correct
2024-01-01 14:30:25 [INFO] selenium_test - ✔ 通過: test_entry_title_is_correct
```

### Headless 模式

無頭模式不會開啟瀏覽器視窗，適合在 CI/CD 環境中使用：

```sh
python3 run.py --headless
# 或
pytest --headless-mode
```

### HTML 報告

使用 `pytest-html` 產生互動式報告：

```sh
python3 run.py --html
# 或
pytest --html=reports/report.html --self-contained-html
```

---

## 如何新增測試

### 1. 新增頁面物件

在 `pages/` 目錄下建立新的 Page Object，繼承 `BasePage`：

```python
# pages/login_page.py
from selenium.webdriver.common.by import By
from pages.base_page import BasePage

class LoginPage(BasePage):
    USERNAME_INPUT = (By.ID, 'username')
    PASSWORD_INPUT = (By.ID, 'password')
    LOGIN_BUTTON = (By.CSS_SELECTOR, '.btn-login')

    def enter_username(self, username):
        self.find_element(*self.USERNAME_INPUT).send_keys(username)

    def enter_password(self, password):
        self.find_element(*self.PASSWORD_INPUT).send_keys(password)

    def click_login(self):
        self.find_element(*self.LOGIN_BUTTON).click()
```

### 2. 新增測試案例

在 `tests/` 目錄下建立測試檔案，使用 pytest fixture：

```python
# tests/test_login.py
import pytest
from pages.login_page import LoginPage

@pytest.fixture
def login_page(driver):
    page = LoginPage(driver)
    driver.get('https://example.com/login')
    return page

class TestLogin:
    @pytest.mark.smoke
    def test_login_success(self, login_page):
        login_page.enter_username('user@example.com')
        login_page.enter_password('password123')
        login_page.click_login()
        assert 'dashboard' in login_page.driver.current_url
```

所有新增的 `test_*.py` 都會被 pytest 自動發現並執行。
