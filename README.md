# Selenium 自動化測試框架

Selenium + pytest + Page Object Model 的自動化測試框架。
核心不動、情境獨立的雙層架構。

---

## 快速開始

```sh
# 安裝
python3 -m venv venv && source venv/bin/activate
pip3 install -r requirements.txt

# 驗證框架
pytest tests/unit/ -v

# 建立測試情境
python generate_scenario.py login_test --url https://example.com/login

# 執行測試
pytest scenarios/login_test/tests/ -v
```

---

## 專案結構

```
selenium/
├── pages/              ← BasePage + 共用 Page Object
├── utils/              ← 17 個工具模組
├── config/             ← 設定（瀏覽器/環境）
├── conftest.py         ← 根層級 fixtures
├── scenarios/          ← 獨立情境模組（每個任務一個）
├── tests/              ← 核心功能測試
├── generate_scenario.py← 情境產生器
├── export_test.py      ← 測試匯出器（拋棄式腳本）
├── Makefile            ← 統一指令入口
└── CLAUDE.md           ← AI 開發規範
```

---

## 文件導覽

| 文件 | 內容 |
|------|------|
| [docs/FLOW.md](docs/FLOW.md) | **流程圖** — 從 URL 到測試報告的完整流程 |
| [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) | **架構** — 雙層架構、核心模組、Fixture 一覽 |
| [docs/USAGE.md](docs/USAGE.md) | **使用指南** — 安裝、建立情境、寫測試、執行、進階功能 |
| [docs/AI_GUIDE.md](docs/AI_GUIDE.md) | **請 AI 實作** — 如何請 AI 幫你寫測試 |
| [CLAUDE.md](CLAUDE.md) | **AI 開發規範** — 開發流程、品質原則、測試規範 |

---

## 常用指令

```sh
make install          # 安裝依賴
make test             # 全部測試
make unit             # 單元測試
make smoke            # 冒煙測試
make scenario S=xxx   # 指定情境
make parallel         # 平行執行
make lint             # 程式碼檢查
make format           # 格式化
make export FILE=xxx  # 匯出拋棄式腳本
```
