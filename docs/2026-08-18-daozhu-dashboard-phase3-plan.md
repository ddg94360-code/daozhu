# 道樞儀表板第三期 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在開源套件儀表板加上看板聊天窗（規則＋可選 LLM）、內閣模板／可選模型五階段發言、心鏡外掛本機 tianji。

**Architecture:** FastAPI 薄層繼續直 import `daily`。新模組 `web/router.py`（規則）、`web/llm.py`（可選 OpenAI 相容）、`web/speech.py`（模板）、`web/tianji_bridge.py`（可選路徑 import）。不複製 tianji 引擎、不裝新套件、不打外網做測試。

**Tech Stack:** Python 3.10+、FastAPI、pytest、stdlib `urllib`（LLM）、vanilla HTML/CSS/JS

**Spec:** [docs/2026-08-18-daozhu-dashboard-phase3-design.md](2026-08-18-daozhu-dashboard-phase3-design.md)

## Global Constraints

- 工作目錄 `c:\Galaxy\daozhu`。不改 Type_moon、不 push、不開 PR、不裝新套件。
- 網頁不直接 replace JSON。舊 MCP 模糊字串工具契約不變。
- 缺 POST body 仍 422。500 message 固定「內部錯誤」。
- 時間凍結只 patch `memory_store._wall_clock`。
- 看板／內閣使用者輸入不當 innerHTML。
- 繁體中文 UI 與 docstring。公開函數要有型別標註。

---

## File map

| 路徑 | 職責 |
|------|------|
| `web/router.py` | 規則意圖 → intent+slots |
| `web/llm.py` | 可選 chat completions；沒 key 回 None |
| `web/speech.py` | 出席名單 → 五階段模板正文 |
| `web/tianji_bridge.py` | 可選 import 本機 engines |
| `web/app.py` | `/api/chat` `/api/cabinet/convene` `/api/xinjing/status` `/api/xinjing/cast` |
| `web/static/index.html`／`app.js`／`app.css` | 聊天卡 |
| `web/static/cabinet.html`／`cabinet.js` | 開會鈕＋body |
| `web/static/xinjing.html`／`xinjing.js` | 真抽鈕＋狀態 |
| `web/tests/test_phase3.py` | 第三期契約 |
| README／CHANGELOG | 一行說明 |

---

### Task 1: 規則路由＋聊天 API

**Files:** Create `web/router.py`；Modify `web/app.py`；Test `web/tests/test_phase3.py`

**Produces:** `router.parse(text: str) -> dict`；`POST /api/chat`

- [ ] 測試：「午餐吃了 150」intent=expense amount=150 item 含午餐
- [ ] 測試：「今天好煩」intent=mood
- [ ] 測試：空白 400；聽不懂 200 ok=false
- [ ] 實作 parse＋chat 路由寫 daily
- [ ] pytest 綠後繼續（本會話一次做完，各 task 結束可暫不單獨 commit）

### Task 2: 模板會議

**Files:** Create `web/speech.py`；Modify `web/app.py` `web/cabinet.py`（不改關鍵詞）

**Produces:** `speech.fill(preview: dict) -> list[dict]`；`POST /api/cabinet/convene`

- [ ] 測試：人際題五階段 body 非空；preview 仍空 body
- [ ] persist true 寫入決策

### Task 3: tianji 橋

**Files:** Create `web/tianji_bridge.py`；Modify `web/app.py`

**Produces:** `available() -> bool`；`cast(mode, **kw) -> dict`；status／cast 路由

- [ ] 測試：未設 env → status false、cast 503
- [ ] 測試：tmp 假 engines.tarot → 200 三張

### Task 4: 三頁畫面＋文件

**Files:** 靜態檔、README、CHANGELOG

- [ ] 看板聊天卡、內閣開會、心鏡真抽
- [ ] 全套 pytest 綠

---

## Self-review

| Spec | Task |
|------|------|
| 聊天規則＋可選 LLM | 1 |
| 會議模板＋persist | 2 |
| tianji 外掛 | 3 |
| 畫面／文件 | 4 |
