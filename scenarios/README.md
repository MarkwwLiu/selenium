# scenarios/ — 獨立情境模組

每個子目錄是一個**完全獨立的測試情境**，使用根目錄的核心框架，但測試案例、Page Object、結果互不影響。

## 建立新情境

```sh
python generate_scenario.py <名稱> --url <目標URL>
```

## 產生的目錄結構

```
scenarios/<名稱>/
├── conftest.py       # fixture: driver / logger / snapshot / analyzer / waiter
├── pytest.ini        # 獨立 pytest 設定
├── pages/            # 情境專屬 Page Object（繼承 BasePage）
├── tests/            # 情境專屬測試案例
├── test_data/        # JSON / CSV 測試資料
└── results/          # 輸出（截圖 / 日誌 / 快照 / HTML 報告）
    └── snapshots/    # 每步操作的截圖+HTML+狀態
```

## 執行

```sh
pytest scenarios/<名稱>/tests/ -v            # 全部
pytest scenarios/<名稱>/tests/ -m positive    # 正向
pytest scenarios/<名稱>/tests/ -m negative    # 反向
pytest scenarios/<名稱>/tests/ -m boundary    # 邊界

# HTML 報告
pytest scenarios/<名稱>/tests/ --html=scenarios/<名稱>/results/report.html
```

## 可用 Fixture

| Fixture | Scope | 說明 |
|---------|-------|------|
| `driver` | session | WebDriver |
| `logger` | session | 日誌（寫入 results/） |
| `waiter` | session | 進階等待工具 |
| `analyzer` | session | 頁面元素分析器 |
| `snapshot` | function | 快照管理器（存到 results/snapshots/） |
| `scenario_url` | function | 情境目標 URL |

## 現有情境

| 目錄 | 說明 |
|------|------|
| `_template/` | 模板（產生器複製用，不要直接執行） |
| `demo_search/` | 範例：Google 搜尋測試（正向/反向/邊界 + JSON 資料驅動） |
