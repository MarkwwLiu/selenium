# Selenium 自動化測試專案

使用 **Selenium + Python unittest** 搭配 **Page Object Model (POM)** 設計模式的自動化測試專案。

---

## 專案結構

```
selenium/
├── config/                     # 設定檔
│   ├── __init__.py
│   └── settings.py             # 集中管理 URL、等待時間、報告路徑等設定
├── pages/                      # Page Object Model（頁面物件）
│   ├── __init__.py
│   ├── base_page.py            # 基礎頁面：共用的瀏覽器操作方法
│   └── home_page.py            # 首頁頁面：封裝首頁的元素定位與操作
├── tests/                      # 測試案例
│   ├── __init__.py
│   ├── base_test.py            # 基礎測試：WebDriver 初始化與關閉
│   ├── test_home_page.py       # 首頁測試（終端機輸出）
│   └── test_home_page_report.py # 首頁測試（產生 HTML 報告）
├── reports/                    # 測試報告輸出目錄
│   └── .gitkeep
├── img/                        # 文件截圖
│   ├── selenium_unittest.png
│   └── selenium_unittest_beautiful_report.png
├── requirements.txt            # Python 依賴套件
├── .gitignore
└── README.md
```

---

## 設計模式說明

### Page Object Model (POM)

本專案採用 **Page Object Model** 設計模式，將「頁面操作」與「測試邏輯」分離：

| 層級 | 檔案 | 職責 |
|------|------|------|
| **Config** | `config/settings.py` | 集中管理所有可配置參數（URL、等待時間等） |
| **Base Page** | `pages/base_page.py` | 封裝共用的瀏覽器操作（開啟頁面、尋找元素、等待元素） |
| **Page Object** | `pages/home_page.py` | 定義特定頁面的元素定位器 (Locators) 與操作方法 |
| **Base Test** | `tests/base_test.py` | 處理 WebDriver 的初始化與關閉 |
| **Test Case** | `tests/test_home_page.py` | 撰寫測試斷言，只關注「要驗證什麼」 |

**好處：**
- 當頁面 UI 變動時，只需修改對應的 Page Object，不需改動測試案例
- 測試案例可讀性更高，更容易維護
- 共用的邏輯不重複撰寫

---

## 環境需求

- Python 3.8+
- Google Chrome 瀏覽器

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

此指令會安裝：
- `selenium` - 瀏覽器自動化框架
- `webdriver-manager` - 自動下載對應版本的 ChromeDriver
- `BeautifulReport` - 產生 HTML 格式的測試報告

---

## 執行測試

### 方式一：終端機輸出結果

```sh
python3 -m tests.test_home_page
```

執行後會在終端機顯示測試結果：

![終端機測試結果](img/selenium_unittest.png)

---

### 方式二：產生 HTML 測試報告

```sh
python3 -m tests.test_home_page_report
```

執行後會在 `reports/` 目錄下產生 HTML 報告檔案。

![HTML 報告樣式](img/selenium_unittest_beautiful_report.png)

---

## 設定說明

所有可配置的參數集中在 `config/settings.py`：

```python
# 測試目標網站
BASE_URL = 'https://shareboxnow.com/'

# 瀏覽器設定
IMPLICIT_WAIT = 10       # 隱式等待秒數

# 報告設定
REPORT_FILENAME = 'Demo_BeautifulReport'
REPORT_DESCRIPTION = 'Selenium 自動化測試報告'
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

在 `tests/` 目錄下建立測試檔案，繼承 `BaseTest`：

```python
# tests/test_login.py
from tests.base_test import BaseTest
from pages.login_page import LoginPage

class TestLogin(BaseTest):
    def setUp(self):
        self.login_page = LoginPage(self.driver)

    def test_login_success(self):
        self.login_page.enter_username('user@example.com')
        self.login_page.enter_password('password123')
        self.login_page.click_login()
        # 斷言...
```
