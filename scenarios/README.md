# scenarios/

每個子目錄是一個**獨立的測試情境模組**，使用根目錄的框架核心（`pages/base_page.py`、`conftest.py`），但測試案例、Page Object、結果互不影響。

## 目錄結構

```
scenarios/
├── _template/          ← 模板（產生器複製用）
│   ├── pages/          ← 情境專屬 Page Object
│   ├── tests/          ← 情境專屬測試
│   └── results/        ← 測試報告 & 截圖
├── login_test/         ← 範例：登入測試情境
│   ├── conftest.py
│   ├── pages/
│   ├── tests/
│   └── results/
└── ...
```

## 執行方式

```sh
# 跑特定情境
pytest scenarios/login_test/tests/ -v

# 只跑正向
pytest scenarios/login_test/tests/ -m positive

# 產出報告到情境目錄
pytest scenarios/login_test/tests/ --html=scenarios/login_test/results/report.html
```
