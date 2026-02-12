# 請 AI 實作測試

如何請 AI（Claude）幫你實作自動化測試。

---

## 基本流程

```
1. 告訴 AI 你要測什麼（URL + 需求）
2. AI 規劃 → 你確認
3. AI 實作 → AI 自己跑測試 → AI 自己修問題
4. 測試全過 → 請你 Review
5. 你同意 → Merge to main
```

---

## 怎麼跟 AI 說

### 範例一：簡單

> 幫我測試 https://example.com/login 這個登入頁面

AI 會自動：
- 掃描頁面元素
- 產生 Page Object
- 產生正向/反向/邊界測試
- 跑測試，確認通過

### 範例二：詳細

> 幫我測試 https://example.com/login
> - 帳號欄位 id 是 email
> - 密碼欄位 id 是 password
> - 登入按鈕 id 是 submit-btn
> - 成功會跳轉到 /dashboard
> - 失敗會顯示 .error-message
> - 需要正向 3 組、反向 5 組、邊界 3 組

### 範例三：用現有情境

> 幫我在 scenarios/login_test/ 加幾個邊界測試

---

## AI 會做什麼

AI 收到需求後會：

1. **確認需求** — 跟你確認目標 URL、需要的選項、測試數量
2. **開分支** — `git checkout -b claude/<feature-name>`
3. **規劃** — 列出要做的事
4. **產生情境** — `generate_scenario.py` 產生骨架
5. **寫 Page Object** — 根據頁面元素
6. **寫測試案例** — 正向/反向/邊界，搭配 `@pytest.mark`
7. **跑測試** — `pytest scenarios/xxx/tests/ -v`
8. **修問題** — 失敗的話分析原因、修改、重跑（至少 3 次）
9. **提交** — 測試全過才 commit
10. **請你 Review** — 列出修改內容，等你確認

---

## AI 的行為規範

| 規則 | 說明 |
|------|------|
| 自己跑測試 | 不能只寫程式碼不執行 |
| 失敗要重試 | 至少 retry 3 次，每次分析原因 |
| 不能謊報完成 | 測試沒過不能說「完成」 |
| 提供選項 | 開始前要確認需求，提供選項讓你選 |
| 按流程走 | 完成後按 CLAUDE.md 的流程：commit → review → merge |

---

## 你需要提供什麼

| 資訊 | 必要？ | 範例 |
|------|--------|------|
| 目標 URL | 是 | `https://example.com/login` |
| 測試類型 | 否（預設全部） | 正向 / 反向 / 邊界 |
| 測試數量 | 否（AI 自動決定） | 正向 3 組、反向 5 組 |
| 元素 ID/selector | 否（AI 自動掃描） | `#email`, `.submit-btn` |
| 預期行為 | 建議提供 | 成功跳轉 /dashboard |
| 帳號密碼 | 視需求 | 測試帳號 |
| 特殊邏輯 | 視需求 | 驗證碼、兩步驟驗證 |

---

## 常見指令

```
# 新建測試
幫我測試 <URL>

# 加測試到現有情境
幫我在 scenarios/<名稱>/ 加 <N> 個 <類型> 測試

# 匯出
幫我把 scenarios/<名稱>/tests/<檔案> 匯出成獨立腳本

# 修改
幫我修改 scenarios/<名稱>/tests/<檔案> 的 <測試名稱>

# 重跑
幫我跑 scenarios/<名稱>/tests/ 的測試
```
