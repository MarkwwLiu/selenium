# 專案架構

---

## 雙層架構

```
selenium/
│
├── 核心框架（不動）        ← 所有情境共用
│   ├── pages/             ← BasePage + 共用 Page Object
│   ├── utils/             ← 工具模組（15 個）
│   ├── config/            ← 設定（瀏覽器/環境）
│   └── conftest.py        ← 根層級 fixtures
│
└── 情境模組（獨立）        ← 每個測試任務一個
    └── scenarios/
        └── <name>/
            ├── pages/     ← 情境專屬 Page Object
            ├── tests/     ← 測試案例
            ├── test_data/ ← 測試資料
            └── results/   ← 輸出（截圖/日誌/報告）
```

**原則：核心不動，情境獨立。**

---

## 核心模組

### pages/ — 頁面物件

| 檔案 | 說明 |
|------|------|
| `base_page.py` | 基礎頁面，30+ 共用方法（等待、點擊、輸入、截圖、快照） |
| `home_page.py` | 範例 Page Object |

所有 Page Object 繼承 `BasePage`，不需要自己處理等待和重試。

### utils/ — 工具模組

| 工具 | 用途 |
|------|------|
| `driver_factory.py` | WebDriver 工廠（Chrome/Firefox/Edge） |
| `screenshot.py` | 截圖 |
| `logger.py` | 日誌 |
| `retry.py` | 重試裝飾器 |
| `data_loader.py` | JSON/CSV 測試資料載入 |
| `waiter.py` | 進階等待（AJAX/元素穩定/屬性變化） |
| `page_analyzer.py` | 頁面元素自動掃描 |
| `page_snapshot.py` | 操作快照（截圖+HTML+狀態） |
| `test_generator.py` | 測試案例自動產生 |
| `cookie_manager.py` | Cookie 管理 |
| `console_capture.py` | 瀏覽器 Console Log 擷取 |
| `soft_assert.py` | 軟斷言 |
| `table_parser.py` | HTML 表格解析 |
| `visual_regression.py` | 視覺回歸（截圖比對） |
| `notifier.py` | Slack / Email 通知 |
| `network_interceptor.py` | 網路攔截 / Mock / 限速（CDP） |
| `data_factory.py` | Faker 測試資料工廠 |

### config/ — 設定

| 檔案 | 說明 |
|------|------|
| `settings.py` | 全域設定（瀏覽器、等待、截圖、日誌） |
| `environments.py` | 多環境切換（dev/staging/prod） |

---

## Fixture 架構

根層級 `conftest.py` 提供所有 fixtures，情境的 `conftest.py` 繼承並擴充：

| Fixture | Scope | 說明 |
|---------|-------|------|
| `driver` | session | WebDriver 實例 |
| `logger` | session | 日誌 |
| `waiter` | session | 進階等待 |
| `analyzer` | session | 頁面分析器 |
| `snapshot` | function | 操作快照 |
| `cookie_manager` | session | Cookie 管理 |
| `console_capture` | function | Console Log |
| `soft_assert` | function | 軟斷言 |
| `table_parser` | session | 表格解析 |
| `visual_regression` | session | 視覺回歸 |
| `network_interceptor` | session | 網路攔截 |
| `data_factory` | function | Faker 資料工廠 |
| `env_config` | session | 環境設定 |
| `scenario_url` | function | 情境 URL |
| `test_lifecycle` | autouse | 自動紀錄+失敗截圖 |

---

## 輔助工具

| 檔案 | 說明 |
|------|------|
| `generate_scenario.py` | 情境模組產生器 |
| `export_test.py` | 測試匯出器（拋棄式腳本） |
| `run.py` | 執行器（報告/平行） |
| `Makefile` | 統一指令入口 |
| `.pre-commit-config.yaml` | 程式碼品質 hooks |
