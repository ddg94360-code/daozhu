# 道樞儀表板第四期 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 內閣加深（三檔＋追問）、心鏡七個計算模式、stdlib 桌面殼、VS Code 側欄骨架、tianji 獨立抽套件。

**Architecture:** FastAPI 薄層繼續直 import `daily`。會議 depth／followup 加在 `speech.py`＋`app.py`。真算模式加在 `tianji_bridge.py`。桌面殼是 `web/desktop.py`。側欄是 `extension/` 靜態骨架。tianji 複製到 `c:\Galaxy\tianji` 獨立 git，daozhu 零 import。

**Tech Stack:** Python 3.10+、FastAPI、pytest、vanilla HTML/JS、VS Code extension.js（不下 npm）、stdlib webbrowser

**Spec:** [docs/2026-08-18-daozhu-dashboard-phase4-design.md](2026-08-18-daozhu-dashboard-phase4-design.md)

## Global Constraints

- 工作目錄 `c:\Galaxy\daozhu`（C3 另在 `c:\Galaxy\tianji`）。不改 Type_moon、不 push、不開 PR、不裝新套件、不 commit daozhu。
- 網頁不直接 replace JSON。舊 MCP 模糊字串工具契約不變。
- 缺 POST body 仍 422。500 message 固定「內部錯誤」。
- 看板／內閣使用者輸入不當 innerHTML。
- 繁體中文 UI 與 docstring。
- 聊天窗不當通用助手。不把 tianji 引擎複製進 daozhu。

---

## File map

| 路徑 | 職責 |
|------|------|
| `web/speech.py` | depth 模板＋followup 模板 |
| `web/app.py` | convene depth、followup 路由、cast 錯誤文案 |
| `web/tianji_bridge.py` | bazi／ziwei／meihua＋status.modes |
| `web/static/cabinet.html`／`cabinet.js` | depth select＋追問卡 |
| `web/static/xinjing.js` | 新模式參數 |
| `web/desktop.py` | stdlib 開瀏覽器＋同一 uvicorn |
| `extension/*` | VS Code 側欄 iframe |
| `web/tests/test_phase4.py` | 第四期契約 |
| `c:\Galaxy\tianji` | 獨立引擎 repo |

---

### Task 1: 內閣 depth＋followup

**Files:** Modify `web/speech.py` `web/app.py` `web/static/cabinet.html` `web/static/cabinet.js`；Test `web/tests/test_phase4.py`

- [x] 測試：flash 佔位、非法 depth 400、followup 200、preview 仍空
- [x] 實作 fill(depth=)＋followup＋路由＋畫面

### Task 2: 心鏡計算模式補完

**Files:** Modify `web/tianji_bridge.py` `web/app.py` `web/static/xinjing.js`

- [x] 測試：status 含 bazi；dream 400 不算命；假 bazi 200
- [x] 實作轉 gua 殼

### Task 3: 桌面殼＋側欄骨架

**Files:** Create `web/desktop.py` `extension/*`

- [x] 測試：desktop 可 import；package.json 有 sidebar；js 用 127.0.0.1
- [x] 實作

### Task 4: tianji 抽套件＋文件

**Files:** `c:\Galaxy\tianji`；README／CHANGELOG

- [x] 複製引擎、init git、README 警語
- [x] 全套 pytest 綠

---

## Self-review

| Spec | Task |
|------|------|
| C1 depth＋追問 | 1 |
| C2 七計算模式 | 2 |
| C5／C4 殼 | 3 |
| C3 開源抽套件 | 4 |
