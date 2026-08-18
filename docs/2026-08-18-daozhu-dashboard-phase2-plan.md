# 道樞儀表板第二期 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在開源套件把本機儀表板做成三頁：看板補完（筆記 CRUD／決策寫入／道藏只讀／感知條／500 handler）、內閣組閣預覽、心鏡 JSON 播放。

**Architecture:** FastAPI 薄層繼續直 import `daily`／`weekly`／`daozang`／`xinjing_render`。筆記加 id 與 by-id 函數；組閣與感知是純函數，不寫記憶。心鏡只呼叫現成 `render()`。

**Tech Stack:** 與第一期相同（Python 3.10+、FastAPI、pytest、vanilla HTML/CSS/JS）

**Spec:** [docs/2026-08-18-daozhu-dashboard-phase2-design.md](2026-08-18-daozhu-dashboard-phase2-design.md)

## Global Constraints

- 工作目錄 `c:\Galaxy\daozhu`。不改 Type_moon、不 push、不開 PR、不裝新套件。
- 網頁不直接 replace JSON。舊 MCP 模糊字串工具契約不變。
- 缺 POST body 仍 422。500 message 固定「內部錯誤」。
- 時間凍結只 patch `memory_store._wall_clock`。
- 看板頁無翻牌、無進場特效。使用者輸入不當 innerHTML。
- 繁體中文 UI 與 docstring。公開函數要有型別標註。

---

## File map

| 路徑 | 職責 |
|------|------|
| `mcp/daily.py` | 新筆記加 id；`mark_study_note_reviewed_by_id`／`delete_study_note_by_id` |
| `mcp/server.py` | 掛兩支 by-id |
| `mcp/tests/test_daily.py` | 追加 by-id 測試 |
| `web/perception.py` | 記憶 → 七層亮燈 |
| `web/cabinet.py` | 議題 → 出席／五階段 |
| `web/app.py` | 新路由、500 handler、三頁 FileResponse |
| `web/static/index.html` | 導覽＋感知＋筆記表單＋決策＋道藏 |
| `web/static/cabinet.html` | 內閣頁 |
| `web/static/xinjing.html` | 心鏡頁 |
| `web/static/app.css` | 導覽／感知／空卡樣式 |
| `web/static/app.js` | 看板新塊 |
| `web/static/cabinet.js` | 預覽 |
| `web/static/xinjing.js` | 載入示範／播放 |
| `web/tests/test_api.py` | 新契約；改筆記只讀斷言 |
| README／CHANGELOG | 第二期說明 |

---

### Task 1: 筆記 by-id

**Files:** `mcp/daily.py`、`mcp/server.py`、`mcp/tests/test_daily.py`

**Produces:** `add_study_note` 新列含 `id`；`mark_study_note_reviewed_by_id(note_id: str) -> dict`；`delete_study_note_by_id(note_id: str) -> dict`

- [ ] 測試：兩則同科目，by-id 只動一則；缺 id／已複習回 false；刪到回 1
- [ ] 實作：`add_study_note` 加 id；兩支 by-id 用 `map_update`／`filter_replace`
- [ ] MCP `_TOOLS` 加名
- [ ] `pytest mcp/tests/test_daily.py` 全過後 commit

---

### Task 2: 感知＋組閣純函數

**Files:** Create `web/perception.py`、`web/cabinet.py`；`web/tests/test_api.py` 或同檔測試

**Produces:** `perception.infer() -> dict`；`cabinet.preview(topic: str) -> dict`

- [ ] 空庫：情緒／任務／人際／精簡／語氣 off；disclaimer 存在
- [ ] 負向 mood → emotion on；到期筆記 → task on
- [ ] 「組員不做事該怎麼講」→ 儒家主＋縱橫家輔
- [ ] 「該不該接」→ 儒法道核心
- [ ] 空字串不在純函數驗證（由 HTTP 層 400）

---

### Task 3: HTTP 讀寫＋500

**Files:** `web/app.py`、`web/tests/test_api.py`

- [ ] 改 `test_notes_are_read_only_shape`：POST `/api/notes` 200 且 GET due 看得到
- [ ] 筆記 by-id 複習／刪；缺 id 404
- [ ] 決策 POST＋GET
- [ ] 道藏 GET 四人格
- [ ] perception GET
- [ ] cabinet preview POST
- [ ] xinjing examples／render／壞 JSON
- [ ] 缺 body 422
- [ ] 500：暫時 patch 一個內部呼叫 raise，回 `{error:internal}`
- [ ] `/cabinet` `/xinjing` 先 404，Task 4 再補頁

---

### Task 4: 三頁畫面

**Files:** 靜態檔＋`app.py` FileResponse

- [ ] 頂欄導覽三頁
- [ ] 看板：感知條、筆記 CRUD、決策表單、道藏四欄
- [ ] 內閣頁可預覽
- [ ] 心鏡頁可載入 tarot example 並得到 HTML
- [ ] `test_index_html` 仍過；加 cabinet／xinjing 含「道樞」

---

### Task 5: 文件

**Files:** `README.md`、`README.zh-TW.md`、`CHANGELOG.md`

- [ ] 儀表板一節改成三頁＋筆記可寫
- [ ] CHANGELOG Unreleased Added 第二期條目
- [ ] 全套 pytest 綠

---

## Self-review

| Spec | Task |
|------|------|
| 筆記 CRUD + id | 1, 3, 4 |
| 決策寫／道藏讀 | 3, 4 |
| 500 handler | 3 |
| 感知條 | 2, 3, 4 |
| 內閣預覽 | 2, 3, 4 |
| 心鏡 JSON | 3, 4 |
| 422 不改 | 3 |
| 舊 MCP 契約 | 1 |
