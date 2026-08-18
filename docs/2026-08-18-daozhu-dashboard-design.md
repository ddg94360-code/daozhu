# 道樞記憶儀表板（第一期）設計

日期：2026-08-18
狀態：待實作（設計已對齊，實作須另開計畫）
範圍：開源套件 `c:\Galaxy\daozhu`；Type_moon 實例只透過 `DAOZHU_MEMORY_DIR` 共用記憶，不在第一期分叉一份前端。

遠期目標（本文件不實作）：獨立聊天窗、對話視覺薄皮（感知／內閣／萬象心鏡）、VS Code 側欄、桌面殼。第一期只做**本機網頁記憶儀表板**，看板＋日常寫入。

---

## 1. 問題與成功標準

道樞記憶層已有 MCP（stdio）＋ `local_memory/` JSON。日常記帳、勾採買、打健康必須走進對話。第一期要一個只聽本機的網頁，讀同一份 JSON、寫同一組 `daily.*`／`weekly.*`，讓少打字的動作離開聊天窗。

成功看起來像：

- `python -m web` 之後瀏覽器打開 `http://127.0.0.1:8765`，看得到週報條、支出、健康、提醒、採買、情緒、筆記（只讀）。
- 在網頁記一筆午餐，Claude Code 裡問「這個月花多少」數字一致；反過來對話記的，重新整理網頁也看得到。
- 空庫不炸；壞輸入 400 且只在該區塊顯示中文原因。
- 現有 `mcp/tests` 零改動仍全過。網頁測試走獨立目錄與可選依賴。

非目標（第一期不做）：

- 聊天、內閣會議畫面、萬象心鏡嵌進儀表板
- VS Code extension、Tauri／pywebview
- 遠端存取、帳密、多使用者、WebSocket
- 網頁新增／改／刪：學習筆記（含已複習）、決策日誌、道藏、整庫備份、已入帳支出、已寫情緒
- 改已存在的金額或提醒時間（刪了重加只開放採買）

---

## 2. 架構

三層，網頁是第二個入口，不是第二套記憶。

```
瀏覽器（先）／VS Code webview／桌面殼（後）
        │  HTTP，只打 127.0.0.1
        ▼
web/app.py     FastAPI：組 JSON、驗欄位、擋非本機
        │  直接 import mcp 模組，不經 MCP stdio
        ▼
mcp/daily.py · weekly.py · solarterm.py · memory_store.py
        │  原子寫 JSON
        ▼
local_memory/   與對話「午餐吃了 150」同一份檔
```

規則：

- **MCP `server.py` 第一期不改行為。** 若為網頁補 `check_shopping_by_id`／`remove_shopping_by_id`，可一併掛上 `_TOOLS`，但舊工具契約不變。
- **網頁不直接 `replace` JSON。** 每個寫入對應一個 `daily.*`（必要時在 `daily.py` 加「按 id」小函數，邏輯仍走 `map_update`／`filter_replace`）。
- **記憶目錄只認 `DAOZHU_MEMORY_DIR`。** 未設時仍是 `mcp/local_memory`。本機對 Type_moon 實況啟動時設成  
  `c:/Galaxy/Type_moon/.claude/daozhu-mcp/local_memory`。
- **並發：** 兩端幾乎同時寫可能互蓋（整檔 replace）。第一期單人本機接受，不上鎖。
- **網路：** 綁 `127.0.0.1:8765`。非本機來源拒絕。不為其他網域開 CORS。無登入——能連這台 loopback 即本人。

---

## 3. 目錄

只動開源套件。不新增 Node 專案；畫面不塞進程式字串。

```
c:\Galaxy\daozhu\
├── mcp/                      # 原樣；requirements 增加可選 fastapi+uvicorn+httpx
├── web/
│   ├── __init__.py
│   ├── __main__.py           # python -m web
│   ├── app.py                # 路由，薄
│   ├── static/
│   │   ├── index.html
│   │   ├── app.js
│   │   └── app.css           # 色票從 skills/daozhu/xinjing/xinjing_engine.html 抄
│   └── tests/                # FastAPI TestClient + isolated memory dir
└── docs/2026-08-18-daozhu-dashboard-design.md
```

`web/` 為可選能力：未裝 fastapi 時 MCP 與現有 CI job 不受影響。儀表板測試另開 CI job 或 extras，避免沒裝 web 依賴的環境失敗。

啟動：

```text
cd c:\Galaxy\daozhu
set DAOZHU_MEMORY_DIR=c:/Galaxy/Type_moon/.claude/daozhu-mcp/local_memory
python -m web
```

瀏覽器開 `http://127.0.0.1:8765`。不做系統服務、不開機自啟。README 中英各加一節「本機儀表板」。

---

## 4. 畫面

一頁七塊，不要多頁選單。窄螢幕直排，寬螢幕兩欄。頂欄：道樞、當前節氣（`solarterm.current_solar_term`）、記憶庫路徑（確認連的是哪一份庫）。

| 區塊 | 看見什麼 | 寫入 |
|------|----------|------|
| 週報條 | 近 7 日總支、均睡、運動次數、情緒三色、待複習數、精力一句；連續負向 ≥3 出關懷旗；本週決策筆數只作數字 | 無（`weekly_report` + `status`） |
| 支出 | 本月分類合計＋最近約 15 筆 | 項目＋金額＋可選分類 → `log_expense`；CSV 下載 |
| 健康 | 最近數次睡眠／運動／水 | 三欄可空、至少一項有值 → `log_health` |
| 提醒 | 未完成；到期置頂標紅 | 內容＋ISO 時間 → `add_reminder`；勾完成 → `mark_reminder_done`。第一期不做循環編輯、不改時間 |
| 採買 | 未勾在上、已勾在下不刪 | 加一列；按 **id** 勾／刪 |
| 情緒 | 最近數則＋正／中／負 | 一句話 → `log_mood`；關懷句（連續負向）顯示在該塊，不開對話 |
| 筆記 | 到期未複習置頂，其餘最近幾則，去重 | **無。** 不新增、不標已複習。複習仍走對話 |

視覺約束：沿用萬象心鏡（深底、紫字 `#9b8cff`、星點、正黑體）。這是工作面——無翻牌動畫、無每塊進場特效。數字對比必須可讀。色票與字體從 `xinjing_engine.html` 抄，不另發明品牌。

寫入成功後重抓該塊或 overview，不在前端假改資料。錯誤只在該塊底下顯示 `message`，不用 `alert`。

---

## 5. HTTP API

`GET /` → `web/static/index.html`。靜態檔只從 `web/static/` 提供。

讀（空庫回空陣列／零，不 404）：

| 路徑 | 背後 | 給畫面 |
|------|------|--------|
| `GET /api/overview` | `weekly.status` + `weekly.weekly_report` + `solarterm.current_solar_term` | 頂欄＋週報條 |
| `GET /api/expenses?month=` | `month_expense_summary` + 該月最近 15 筆（新的在前） | 分類合計＋列表 |
| `GET /api/health?limit=10` | `health` 新的在前 | 打卡列表 |
| `GET /api/reminders` | `pending_reminders`；每筆加 `due`（`datetime ≤ now`） | 前端到期置頂 |
| `GET /api/shopping` | `list_shopping` | 未勾／已勾分區 |
| `GET /api/moods?limit=15` | `mood_log` 新的在前 | 含 `classification` |
| `GET /api/notes` | `due_study_notes` + 最近數則（去重） | 只讀 |
| `GET /api/expenses.csv?month=` | `export_expenses_csv` | `text/csv` |

寫（成功 200 + 該 `daily.*` 原本回傳的 dict，與 MCP 同一形狀。網頁層不重算連續天數、分類、合計）：

| 路徑 | body | 呼叫 |
|------|------|------|
| `POST /api/expenses` | `{item, amount, category?}` | `log_expense` |
| `POST /api/health` | `{sleep_hours?, exercise?, water?}` 至少一項有值 | `log_health` |
| `POST /api/reminders` | `{content, datetime, recurring?}` | `add_reminder`；`datetime` 須能被 ISO 解析 |
| `POST /api/reminders/{id}/done` | 無 | `mark_reminder_done`；`matched: false` → 404 |
| `POST /api/shopping` | `{item}` | `add_shopping` |
| `POST /api/shopping/{id}/check` | 無 | `check_shopping_by_id`（若尚無則在 `daily.py` 新增） |
| `DELETE /api/shopping/{id}` | 無 | `remove_shopping_by_id`（若尚無則新增） |
| `POST /api/moods` | `{mood}` | `log_mood` |

沒有：`POST /api/notes`、mark reviewed、決策、道藏、backup、改金額。

採買／提醒的完成與刪除**必須按 id**。現有 `check_shopping`／`remove_shopping` 是模糊字串，網頁不得直接拿來對「咖啡」這種重複名。新增的 by-id 函數內部仍用 `map_update`／`filter_replace`。

---

## 6. 錯誤

統一 JSON：

```json
{ "error": "amount_invalid", "message": "金額必須是數字" }
```

| 情況 | HTTP | `error` |
|------|------|---------|
| 缺欄、空字串、金額非數字或 ≤0、提醒時間不是 ISO、健康三欄全空 | 400 | `invalid`（`message` 中文指那一欄） |
| 提醒／採買 id 不存在，或已完成／已勾 | 404 | `not_found` |
| 記憶目錄讀寫等意外 | 500 | `internal`（不把堆疊丟給瀏覽器；路徑可出現在伺服器日誌） |

非 loopback 來源：拒絕連線或 403，不處理業務。

---

## 7. 測試

- `mcp/tests`：現有套件維持原樣，CI 預設 job 不強制裝 fastapi。
- `web/tests`：FastAPI `TestClient`；記憶庫用暫存目錄 + `DAOZHU_MEMORY_DIR`（與 `mcp/tests/conftest.py` 的 `isolated_memory` 同一招）。時間凍結仍 patch `memory_store._wall_clock`。
- 至少覆蓋：overview 空庫 200；記一筆支出後 GET 看得到；壞金額 400；勾不存在的提醒 404；`POST /api/notes` 不存在（404／405）；購物 check／delete 只動對應 id。
- 若新增 `check_shopping_by_id`／`remove_shopping_by_id`，在 `mcp/tests` 補單元測試，並可註冊 MCP 工具。

---

## 8. 依賴與文件

- `mcp/requirements.txt` 或 extras：`fastapi`、`uvicorn`、測試用 `httpx`（TestClient）。版本釘在實作計畫裡，本設計不鎖死小版號。
- README.md ／ README.zh-TW.md 加「本機儀表板」：安裝 extras、啟動三行、`DAOZHU_MEMORY_DIR` 指向現有庫。
- CHANGELOG Unreleased：Added 儀表板；若有 by-id API 一併列出。
- CONTRIBUTING：Python 風格同樣適用 `web/`；新路由不得繞過 `daily`／`weekly`。

---

## 9. 以後怎麼長（不實作，只鎖定接縫）

- VS Code 側欄／桌面殼：開同一個 `http://127.0.0.1:8765`，不另寫 API。
- 聊天窗、心鏡皮：在 `web/app.py` 加路由與靜態頁，仍不碰 `memory_store` 寫入契約。
- 若日後要遠端，必須先加認證；本設計預設永遠本機。

---

## 10. 已否決

- Streamlit／Gradio：出活快，氣質與後續包殼都不合。
- React／Next 獨立前端：第一期過重。
- 把儀表板做進 Type_moon `.claude/` 而不進開源套件：違反「開源套件為主」。
- 第一期就做筆記寫入：已明確拿掉。
