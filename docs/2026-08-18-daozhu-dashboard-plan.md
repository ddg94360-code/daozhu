# 道樞記憶儀表板 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在開源套件 `c:\Galaxy\daozhu` 加一個只聽 `127.0.0.1:8765` 的本機網頁，讀寫與 MCP 同一份 `local_memory/`，完成第一期記憶儀表板（看板＋日常寫入，筆記只讀）。

**Architecture:** FastAPI 薄層直接 `import daily / weekly / solarterm / memory_store`，不經 MCP stdio。採買勾／刪按 id，缺的 by-id 函數加在 `mcp/daily.py` 並掛上 MCP。前端單頁靜態檔，色票抄萬象心鏡。現有 `mcp/tests` 契約不變。

**Tech Stack:** Python 3.10+、FastAPI、uvicorn、httpx（TestClient）、既有 pytest + `isolated_memory`、vanilla HTML/CSS/JS

**Spec:** [docs/2026-08-18-daozhu-dashboard-design.md](2026-08-18-daozhu-dashboard-design.md)

## Global Constraints

- 工作目錄是開源套件 `c:\Galaxy\daozhu`（獨立 git repo），不是 Type_moon。
- 網頁不直接 `memory_store.replace` JSON；每個寫入對應一個 `daily.*`。
- 記憶目錄只認環境變數 `DAOZHU_MEMORY_DIR`；未設時為 `mcp/local_memory`。
- 綁 `127.0.0.1:8765`；非 loopback 拒絕；不開跨域 CORS；無登入。
- 第一期沒有：筆記寫入／已複習、決策寫入、道藏、backup、改金額、改提醒時間、聊天、心鏡嵌入、VS Code／桌面殼。
- 錯誤形狀一律 `{"error": "<code>", "message": "<中文>"}`。400=`invalid`，404=`not_found`，500=`internal`。
- 成功寫入回傳該 `daily.*` 原本的 dict，網頁層不重算分類／連續天數／合計。
- 時間凍結只 patch `memory_store._wall_clock`，不 patch `datetime.now` 或 `daily.now`。
- 現有 `mcp/tests` 必須零改動仍全過（可**新增**測試檔／用例，不可改舊斷言）。
- 預設 CI job（`mcp` + `requirements.txt`）不因沒裝 fastapi 而失敗。
- 繁體中文 UI 與 docstring；公開 Python 函數要有型別標註。
- 色票從 `skills/daozhu/xinjing/xinjing_engine.html` 抄：底 `#0d0a1a`／`#1a1438`，字 `#e8e0ff`，紫 `#9b8cff`，輔 `#6f6394`，字體 `"Microsoft JhengHei","PingFang TC",serif`。無翻牌動畫、無每塊進場特效。

---

## File map

| 路徑 | 職責 |
|------|------|
| `mcp/daily.py` | 新增 `check_shopping_by_id(item_id: str) -> dict`、`remove_shopping_by_id(item_id: str) -> dict` |
| `mcp/server.py` | `_TOOLS` 加兩支 by-id 工具；舊工具不動 |
| `mcp/tests/test_daily.py` | 加 by-id 單元測試（舊測試不改） |
| `mcp/pyproject.toml` | extras `web` = fastapi、uvicorn、httpx |
| `mcp/requirements-web.txt` | 釘版本的 web extras，給 CI 第二 job 與本機 `pip install -r` |
| `web/__init__.py` | 套件標記 |
| `web/__main__.py` | `python -m web` → uvicorn 127.0.0.1:8765 |
| `web/app.py` | FastAPI app、loopback 中介、全部路由 |
| `web/static/index.html` | 一頁七塊骨架 |
| `web/static/app.css` | 心鏡色票工作面 |
| `web/static/app.js` | fetch、表單、區塊重繪 |
| `web/tests/conftest.py` | sys.path + isolated_memory + TestClient |
| `web/tests/test_api.py` | API 契約測試 |
| `.github/workflows/test.yml` | 加可選 `dashboard` job |
| `README.md` / `README.zh-TW.md` / `CHANGELOG.md` / `CONTRIBUTING.md` | 儀表板一節 |

Import 規則：`web/app.py` 啟動時把 `mcp/` 加進 `sys.path`（與 `mcp/tests/conftest.py` 同一招），然後 `import daily, weekly, solarterm, memory_store`。不要把 `mcp` 改成可安裝 package 當本計畫的一部分。

---

### Task 1: 採買按 id 勾／刪

**Files:**
- Modify: `mcp/daily.py`（`remove_shopping` 之後、情緒日記一節之前）
- Modify: `mcp/server.py`（`_TOOLS` 採買區）
- Modify: `mcp/tests/test_daily.py`（檔尾追加，不改舊測試）

**Interfaces:**
- Consumes: `store.map_update`、`store.filter_replace`、既有 shopping 記錄形狀 `{id, item, checked}`
- Produces:
  - `daily.check_shopping_by_id(item_id: str) -> dict` — 成功 `{"matched": True}`；id 不存在或已勾 `{"matched": False}`（不寫檔）
  - `daily.remove_shopping_by_id(item_id: str) -> dict` — 刪到回 `{"removed": 1}`，否則 `{"removed": 0}`
  - MCP 名：`daozhu_check_shopping_by_id`、`daozhu_remove_shopping_by_id`

- [ ] **Step 1: Write the failing tests**

在 `mcp/tests/test_daily.py` 檔尾追加（沿用檔內既有 `import daily` 與 `isolated_memory`）：

```python
def test_check_shopping_by_id_only_touches_that_row(isolated_memory):
    a = daily.add_shopping("咖啡")["record"]
    b = daily.add_shopping("咖啡")["record"]
    assert daily.check_shopping_by_id(a["id"])["matched"] is True
    items = {r["id"]: r for r in daily.list_shopping()}
    assert items[a["id"]]["checked"] is True
    assert items[b["id"]]["checked"] is False


def test_check_shopping_by_id_missing_or_already_checked(isolated_memory):
    rec = daily.add_shopping("牛奶")["record"]
    assert daily.check_shopping_by_id("no-such")["matched"] is False
    assert daily.check_shopping_by_id(rec["id"])["matched"] is True
    assert daily.check_shopping_by_id(rec["id"])["matched"] is False
    assert len(daily.list_shopping()) == 1


def test_remove_shopping_by_id_only_deletes_that_row(isolated_memory):
    a = daily.add_shopping("雞蛋")["record"]
    b = daily.add_shopping("雞蛋")["record"]
    assert daily.remove_shopping_by_id(a["id"])["removed"] == 1
    left = daily.list_shopping()
    assert len(left) == 1
    assert left[0]["id"] == b["id"]
    assert daily.remove_shopping_by_id("no-such")["removed"] == 0
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `cd mcp && python -m pytest tests/test_daily.py::test_check_shopping_by_id_only_touches_that_row tests/test_daily.py::test_check_shopping_by_id_missing_or_already_checked tests/test_daily.py::test_remove_shopping_by_id_only_deletes_that_row -v`

Expected: FAIL — `check_shopping_by_id` / `remove_shopping_by_id` 未定義

- [ ] **Step 3: Implement the two functions**

在 `mcp/daily.py` 的 `remove_shopping` 之後插入：

```python
def check_shopping_by_id(item_id: str) -> dict:
    """按 id 標記已購，就地改 checked，不刪除。"""
    n = store.map_update(
        "shopping",
        lambda r: r.get("id") == item_id and not r.get("checked", False),
        lambda r: {**r, "checked": True},
    )
    return {"matched": n > 0}


def remove_shopping_by_id(item_id: str) -> dict:
    """按 id 刪除一筆採買。"""
    removed = store.filter_replace("shopping", lambda r: r.get("id") != item_id)
    return {"removed": removed}
```

`mcp/server.py` 的 `_TOOLS` 採買區改成：

```python
    "daozhu_add_shopping": daily.add_shopping,
    "daozhu_list_shopping": daily.list_shopping,
    "daozhu_check_shopping": daily.check_shopping,
    "daozhu_remove_shopping": daily.remove_shopping,
    "daozhu_check_shopping_by_id": daily.check_shopping_by_id,
    "daozhu_remove_shopping_by_id": daily.remove_shopping_by_id,
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd mcp && python -m pytest tests/test_daily.py tests/test_reminder_backup.py -v`

Expected: PASS（含舊的模糊字串 `check_shopping` 測試）

- [ ] **Step 5: Commit**

```bash
git add mcp/daily.py mcp/server.py mcp/tests/test_daily.py
git commit -m "feat(mcp): check and remove shopping items by id"
```

---

### Task 2: FastAPI 應用骨架與 loopback

**Files:**
- Create: `web/__init__.py`
- Create: `web/__main__.py`
- Create: `web/app.py`
- Create: `web/tests/conftest.py`
- Create: `web/tests/test_api.py`（本 task 只放骨架測試）
- Create: `mcp/requirements-web.txt`
- Modify: `mcp/pyproject.toml`（optional-dependencies）

**Interfaces:**
- Consumes: 無業務路由（本 task 只保證 app 起得來、本機可打、靜態目錄預留）
- Produces:
  - `web.app.app: FastAPI`
  - `web.app._mcp_on_path() -> None` — 把 `mcp/` 絕對路徑 insert 到 `sys.path[0]`（idempotent）
  - `GET /api/healthz` → `{"ok": true}`（存活探針，不是日用集健康打卡）
  - 非 loopback：middleware 回 403 `{"error":"forbidden","message":"僅限本機存取"}`

- [ ] **Step 1: Add web extras (no version lottery)**

`mcp/requirements-web.txt`：

```text
fastapi==0.116.1
uvicorn==0.35.0
httpx==0.28.1
```

`mcp/pyproject.toml` 的 optional-dependencies 改成：

```toml
[project.optional-dependencies]
yaml = ["pyyaml>=6.0"]
dev = ["ruff>=0.9", "pytest>=8"]
web = ["fastapi==0.116.1", "uvicorn==0.35.0", "httpx==0.28.1"]
```

本機：`pip install -r mcp/requirements-web.txt`（已有 pytest 則不必重裝 mcp/requirements.txt）。

`web/__init__.py` 內容為一個模組 docstring：`"""道樞本機記憶儀表板。"""`

- [ ] **Step 2: Write failing tests for healthz + forbidden**

`web/tests/conftest.py`：

```python
"""儀表板測試：隔離記憶庫 + FastAPI TestClient。"""
import os
import sys

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_MCP = os.path.join(_REPO, "mcp")
_WEB = os.path.join(_REPO, "web")
for p in (_WEB, _MCP):
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture()
def isolated_memory(tmp_path, monkeypatch):
    monkeypatch.setenv("DAOZHU_MEMORY_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def client(isolated_memory):
    from fastapi.testclient import TestClient

    from app import app

    with TestClient(app) as c:
        yield c
```

`web/tests/test_api.py`：

```python
def test_healthz_ok(client):
    r = client.get("/api/healthz")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_rejects_non_loopback(client):
    r = client.get("/api/healthz", headers={"X-Forwarded-For": "8.8.8.8"})
    # TestClient 預設 client.host 是 testclient；middleware 以 request.client.host 為準。
    # 本測試改打 ASGI scope，見下行輔助。
    assert r.status_code in (200, 403)
```

上面最後一則不夠硬。改成直接改 scope 的寫法（整則取代 `test_rejects_non_loopback`）：

```python
def test_rejects_non_loopback(isolated_memory):
    from fastapi.testclient import TestClient

    from app import app

    with TestClient(app) as c:
        r = c.get(
            "/api/healthz",
            client=("203.0.113.10", 50000),
        )
    assert r.status_code == 403
    body = r.json()
    assert body["error"] == "forbidden"
    assert "本機" in body["message"]
```

`TestClient.get(..., client=(host, port))` 是 Starlette 支援的覆寫。若實作時該 kwargs 在你裝的版本不存在，改用：

```python
async def _call():
    from app import app
    scope = {
        "type": "http",
        "asgi": {"version": "3.0"},
        "http_version": "1.1",
        "method": "GET",
        "scheme": "http",
        "path": "/api/healthz",
        "raw_path": b"/api/healthz",
        "query_string": b"",
        "headers": [],
        "client": ("203.0.113.10", 50000),
        "server": ("127.0.0.1", 8765),
    }
    messages = []

    async def receive():
        return {"type": "http.request", "body": b"", "more_body": False}

    async def send(message):
        messages.append(message)

    await app(scope, receive, send)
    start = next(m for m in messages if m["type"] == "http.response.start")
    assert start["status"] == 403
```

優先用 `TestClient(..., client=)`；只有該參數失效才用 ASGI scope。計畫驗收以 **403 + `error=forbidden`** 為準。

- [ ] **Step 3: Run tests to verify they fail**

Run: `cd /c/Galaxy/daozhu && python -m pytest web/tests/test_api.py -v`

Expected: FAIL — `No module named 'app'` 或 fastapi 未裝。先裝 `pip install -r mcp/requirements-web.txt` 後應變成 import app 失敗。

- [ ] **Step 4: Implement app skeleton**

`web/app.py`：

```python
"""道樞本機儀表板 HTTP 入口。只聽 loopback；業務一律轉 daily/weekly/solarterm。"""
from __future__ import annotations

import os
import sys

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MCP = os.path.join(_REPO, "mcp")
_STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


def _mcp_on_path() -> None:
    if _MCP not in sys.path:
        sys.path.insert(0, _MCP)


_mcp_on_path()

app = FastAPI(title="道樞儀表板", docs_url=None, redoc_url=None)


@app.middleware("http")
async def loopback_only(request: Request, call_next):
    host = (request.client.host if request.client else "") or ""
    if host not in {"127.0.0.1", "::1", "testclient", "localhost"}:
        return JSONResponse(
            {"error": "forbidden", "message": "僅限本機存取"},
            status_code=403,
        )
    return await call_next(request)


@app.get("/api/healthz")
def healthz() -> dict:
    return {"ok": True}


# 靜態目錄在 Task 5 才放 index.html；此處若目錄尚無檔案，先不要 mount 以免測試炸。
# Task 5 再加：if os.path.isdir(_STATIC): app.mount("/", StaticFiles(directory=_STATIC, html=True), name="static")
```

注意：`testclient` 必須列入允許名單，否則 TestClient 預設 host 會 403。真瀏覽器走 `127.0.0.1`。`X-Forwarded-For` **不要**當信任來源。

`web/__main__.py`：

```python
"""python -m web → http://127.0.0.1:8765"""
import uvicorn

from app import app


def main() -> None:
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `python -m pytest web/tests/test_api.py -v`

Expected: PASS

再跑：`cd mcp && python -m pytest tests/ -q`

Expected: PASS（與 web 無關）

- [ ] **Step 6: Commit**

```bash
git add web/__init__.py web/__main__.py web/app.py web/tests/conftest.py web/tests/test_api.py mcp/requirements-web.txt mcp/pyproject.toml
git commit -m "feat(web): FastAPI skeleton bound to loopback"
```

---

### Task 3: 讀 API

**Files:**
- Modify: `web/app.py`
- Modify: `web/tests/test_api.py`

**Interfaces:**
- Consumes: `weekly.status() -> dict`、`weekly.weekly_report() -> dict`、`solarterm.current_solar_term() -> dict`、`daily.month_expense_summary()`、`daily.export_expenses_csv(month: str = "")`、`daily.pending_reminders()`、`daily.list_shopping()`、`daily.due_study_notes()`、`daily.list_study_notes()`、`memory_store.all_records(name)`、`memory_store.now()`、`memory_store.base_dir()`
- Produces: 下列 GET 的 JSON 形狀（欄位名鎖死，前端 Task 5 依此畫）

`GET /api/overview` →

```python
{
  "status": <weekly.status() 原樣>,
  "report": <weekly.weekly_report() 原樣>,
  "solar_term": <solarterm.current_solar_term() 原樣>,
  "memory_dir": <memory_store.base_dir()>,
}
```

`GET /api/expenses?month=`（`month` 可省略，省略則用 `memory_store.now()[:7]`）→

```python
{
  "summary": <daily.month_expense_summary() 但若 query month 有值，先濾該月再聚合——見下方實作約束>,
  "recent": [/* 該月支出新到舊最多 15 筆，原 record 形狀 */],
}
```

實作約束：現成 `month_expense_summary()` 只做「本月」。當 query 提供 `month` 且等於本月，直接呼叫即可。當提供的 `month` **不是**本月：在 `app.py` 用 `memory_store.all_records("expenses")` 濾 `date.startswith(month)` 自組 `{"month", "total", "by_category", "currency"}`，**不要**改 `daily.month_expense_summary` 的契約。`currency` 用 `config.currency_symbol()`。

`GET /api/health?limit=10` → `{"records": [/* all_records("health") 反轉後 [:limit] */]}`。`limit` 預設 10，最小 1、最大 100。

`GET /api/reminders` → `{"records": [ {**r, "due": r.get("datetime","") <= memory_store.now()} for r in daily.pending_reminders() ]}`

`GET /api/shopping` → `{"records": daily.list_shopping()}`

`GET /api/moods?limit=15` → `{"records": [/* mood_log 新到舊 [:limit] */]}`。limit 預設 15，1–100。

`GET /api/notes` →

```python
{
  "due": daily.due_study_notes(),
  "recent": /* daily.list_study_notes() 已是最近 10 則新到舊；去掉已在 due 裡的（比對 date+subject+original） */
}
```

`GET /api/expenses.csv?month=` → `Response(content=daily.export_expenses_csv(month or ""), media_type="text/csv")`。`export_expenses_csv` 空字串 = 本月。

- [ ] **Step 1: Write the failing read tests**

追加到 `web/tests/test_api.py`：

```python
from datetime import datetime

import daily
import memory_store as store


def test_overview_empty_ok(client, isolated_memory):
    r = client.get("/api/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["status"]["status"] == "ok"
    assert body["report"]["expense_total"] == 0
    assert "current" in body["solar_term"]
    assert body["memory_dir"] == str(isolated_memory)


def test_expenses_lists_recent_after_log(client, isolated_memory):
    daily.log_expense("午餐", 150, "飲食")
    r = client.get("/api/expenses")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["total"] == 150
    assert body["summary"]["by_category"]["飲食"] == 150
    assert len(body["recent"]) == 1
    assert body["recent"][0]["item"] == "午餐"


def test_reminders_mark_due(client, isolated_memory, monkeypatch):
    monkeypatch.setattr(store, "_wall_clock", lambda: datetime.fromisoformat("2026-08-18T12:00:00"))
    daily.add_reminder("過期", "2026-08-18T10:00:00")
    daily.add_reminder("未來", "2026-08-19T10:00:00")
    r = client.get("/api/reminders")
    assert r.status_code == 200
    recs = {x["content"]: x for x in r.json()["records"]}
    assert recs["過期"]["due"] is True
    assert recs["未來"]["due"] is False


def test_notes_are_read_only_shape(client, isolated_memory, monkeypatch):
    monkeypatch.setattr(store, "_wall_clock", lambda: datetime.fromisoformat("2026-08-18T12:00:00"))
    daily.add_study_note("物理", "熵增", review_days=0)
    r = client.get("/api/notes")
    assert r.status_code == 200
    assert len(r.json()["due"]) == 1
    post = client.post("/api/notes", json={"subject": "x", "content": "y"})
    assert post.status_code in (404, 405)


def test_expenses_csv(client, isolated_memory):
    daily.log_expense("午餐", 150)
    r = client.get("/api/expenses.csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "午餐" in r.text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest web/tests/test_api.py::test_overview_empty_ok web/tests/test_api.py::test_expenses_lists_recent_after_log web/tests/test_api.py::test_notes_are_read_only_shape -v`

Expected: FAIL — 404 on `/api/overview`

- [ ] **Step 3: Implement GET routes**

在 `web/app.py` 於 `_mcp_on_path()` 之後加入：

```python
import config
import daily
import memory_store as store
import solarterm
import weekly
```

輔助：

```python
def _month_summary(month: str) -> dict:
    recs = [r for r in store.all_records("expenses") if r.get("date", "").startswith(month)]
    cats: dict[str, float] = {}
    for r in recs:
        cat = r.get("category", "其他")
        cats[cat] = cats.get(cat, 0) + r["amount"]
    return {
        "month": month,
        "total": round(sum(cats.values()), 2),
        "by_category": {k: round(v, 2) for k, v in cats.items()},
        "currency": config.currency_symbol(),
    }


def _recent(name: str, limit: int) -> list:
    recs = store.all_records(name)
    recs = list(reversed(recs))
    return recs[: max(1, min(limit, 100))]
```

路由（完整寫出，不要「依此類推」）：

```python
from fastapi import Query
from fastapi.responses import Response


@app.get("/api/overview")
def api_overview() -> dict:
    return {
        "status": weekly.status(),
        "report": weekly.weekly_report(),
        "solar_term": solarterm.current_solar_term(),
        "memory_dir": store.base_dir(),
    }


@app.get("/api/expenses")
def api_expenses(month: str = "") -> dict:
    month = month or store.now()[:7]
    if month == store.now()[:7]:
        summary = daily.month_expense_summary()
    else:
        summary = _month_summary(month)
    recs = [r for r in store.all_records("expenses") if r.get("date", "").startswith(month)]
    recs = list(reversed(recs))[:15]
    return {"summary": summary, "recent": recs}


@app.get("/api/health")
def api_health(limit: int = Query(10, ge=1, le=100)) -> dict:
    return {"records": _recent("health", limit)}


@app.get("/api/reminders")
def api_reminders() -> dict:
    now = store.now()
    recs = []
    for r in daily.pending_reminders():
        recs.append({**r, "due": r.get("datetime", "") <= now})
    return {"records": recs}


@app.get("/api/shopping")
def api_shopping() -> dict:
    return {"records": daily.list_shopping()}


@app.get("/api/moods")
def api_moods(limit: int = Query(15, ge=1, le=100)) -> dict:
    return {"records": _recent("mood_log", limit)}


@app.get("/api/notes")
def api_notes() -> dict:
    due = daily.due_study_notes()
    due_keys = {(r.get("date"), r.get("subject"), r.get("original")) for r in due}
    recent = [
        r for r in daily.list_study_notes()
        if (r.get("date"), r.get("subject"), r.get("original")) not in due_keys
    ]
    return {"due": due, "recent": recent}


@app.get("/api/expenses.csv")
def api_expenses_csv(month: str = "") -> Response:
    return Response(
        content=daily.export_expenses_csv(month),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="expenses.csv"'},
    )
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest web/tests/test_api.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/app.py web/tests/test_api.py
git commit -m "feat(web): read APIs for overview, daily collections, csv"
```

---

### Task 4: 寫 API 與驗證

**Files:**
- Modify: `web/app.py`
- Modify: `web/tests/test_api.py`

**Interfaces:**
- Consumes: Task 1 的 by-id 函數 + `daily.log_expense` / `log_health` / `add_reminder` / `mark_reminder_done` / `add_shopping` / `log_mood`
- Produces: 下表 POST/DELETE；驗證失敗 400 `{"error":"invalid","message":...}`；id 未命中 404 `{"error":"not_found","message":...}`

| 路徑 | 成功呼叫 |
|------|----------|
| `POST /api/expenses` body `{item: str, amount: number, category?: str}` | `daily.log_expense`。`item` 去空白後空 → 400「項目不能空白」。`amount` 非數字或 ≤0 → 400「金額必須是大於 0 的數字」 |
| `POST /api/health` body `{sleep_hours?: number, exercise?: str, water?: str}` | 三欄皆缺／空／0 → 400「至少填一項健康紀錄」。否則 `log_health` |
| `POST /api/reminders` body `{content: str, datetime: str, recurring?: bool}` | `content` 空 → 400。「datetime」用 `datetime.fromisoformat`，失敗 → 400「時間須為 ISO 格式」。成功 `add_reminder` |
| `POST /api/reminders/{id}/done` | `mark_reminder_done`；`matched is False` → 404「找不到這則提醒」 |
| `POST /api/shopping` body `{item: str}` | item 空 → 400。否則 `add_shopping` |
| `POST /api/shopping/{id}/check` | `check_shopping_by_id`；false → 404「找不到這筆採買」 |
| `DELETE /api/shopping/{id}` | `remove_shopping_by_id`；`removed == 0` → 404 |
| `POST /api/moods` body `{mood: str}` | mood 空 → 400。否則 `log_mood` |

400/404 用一個小助手，不要每條手寫 JSONResponse：

```python
def _err(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse({"error": code, "message": message}, status_code=status)
```

寫入路由回傳 `daily.*` 的 dict（200）。不要包多一層。

- [ ] **Step 1: Write the failing write tests**

追加到 `web/tests/test_api.py`：

```python
def test_post_expense_then_get(client, isolated_memory):
    r = client.post("/api/expenses", json={"item": "午餐", "amount": 80})
    assert r.status_code == 200
    assert r.json()["record"]["amount"] == 80
    listed = client.get("/api/expenses").json()
    assert listed["summary"]["total"] == 80


def test_post_expense_bad_amount(client):
    r = client.post("/api/expenses", json={"item": "午餐", "amount": 0})
    assert r.status_code == 400
    assert r.json()["error"] == "invalid"
    assert "金額" in r.json()["message"]


def test_mark_missing_reminder_404(client):
    r = client.post("/api/reminders/deadbeef/done")
    assert r.status_code == 404
    assert r.json()["error"] == "not_found"


def test_shopping_check_by_id_not_fuzzy(client, isolated_memory):
    a = client.post("/api/shopping", json={"item": "咖啡"}).json()["record"]
    b = client.post("/api/shopping", json={"item": "咖啡"}).json()["record"]
    r = client.post(f"/api/shopping/{a['id']}/check")
    assert r.status_code == 200
    recs = {x["id"]: x for x in client.get("/api/shopping").json()["records"]}
    assert recs[a["id"]]["checked"] is True
    assert recs[b["id"]]["checked"] is False


def test_delete_shopping_404(client):
    r = client.delete("/api/shopping/nope")
    assert r.status_code == 404


def test_health_requires_one_field(client):
    r = client.post("/api/health", json={})
    assert r.status_code == 400
    assert r.json()["error"] == "invalid"


def test_mood_roundtrip(client, isolated_memory):
    r = client.post("/api/moods", json={"mood": "今天好煩"})
    assert r.status_code == 200
    assert r.json()["record"]["classification"] == "負向"
    listed = client.get("/api/moods").json()["records"]
    assert listed[0]["mood"] == "今天好煩"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `python -m pytest web/tests/test_api.py::test_post_expense_then_get web/tests/test_api.py::test_shopping_check_by_id_not_fuzzy -v`

Expected: FAIL — 404 on POST

- [ ] **Step 3: Implement POST/DELETE**

在 `web/app.py` 加入（`from datetime import datetime` 已有則不重複）：

```python
from datetime import datetime

from fastapi import Body


def _err(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse({"error": code, "message": message}, status_code=status)


@app.post("/api/expenses")
def api_post_expense(body: dict = Body(...)):
    item = str(body.get("item", "")).strip()
    if not item:
        return _err("invalid", "項目不能空白", 400)
    try:
        amount = float(body.get("amount"))
    except (TypeError, ValueError):
        return _err("invalid", "金額必須是大於 0 的數字", 400)
    if amount <= 0:
        return _err("invalid", "金額必須是大於 0 的數字", 400)
    category = str(body.get("category") or "")
    return daily.log_expense(item, amount, category)


@app.post("/api/health")
def api_post_health(body: dict = Body(...)):
    sleep = body.get("sleep_hours", 0) or 0
    try:
        sleep_f = float(sleep)
    except (TypeError, ValueError):
        return _err("invalid", "睡眠時數必須是數字", 400)
    exercise = str(body.get("exercise") or "").strip()
    water = str(body.get("water") or "").strip()
    if sleep_f <= 0 and not exercise and not water:
        return _err("invalid", "至少填一項健康紀錄", 400)
    return daily.log_health(sleep_f, exercise, water)


@app.post("/api/reminders")
def api_post_reminder(body: dict = Body(...)):
    content = str(body.get("content", "")).strip()
    if not content:
        return _err("invalid", "提醒內容不能空白", 400)
    dt = str(body.get("datetime", "")).strip()
    try:
        datetime.fromisoformat(dt)
    except ValueError:
        return _err("invalid", "時間須為 ISO 格式", 400)
    recurring = bool(body.get("recurring", False))
    return daily.add_reminder(content, dt, recurring)


@app.post("/api/reminders/{reminder_id}/done")
def api_reminder_done(reminder_id: str):
    res = daily.mark_reminder_done(reminder_id)
    if not res.get("matched"):
        return _err("not_found", "找不到這則提醒", 404)
    return res


@app.post("/api/shopping")
def api_post_shopping(body: dict = Body(...)):
    item = str(body.get("item", "")).strip()
    if not item:
        return _err("invalid", "項目不能空白", 400)
    return daily.add_shopping(item)


@app.post("/api/shopping/{item_id}/check")
def api_shopping_check(item_id: str):
    res = daily.check_shopping_by_id(item_id)
    if not res.get("matched"):
        return _err("not_found", "找不到這筆採買", 404)
    return res


@app.delete("/api/shopping/{item_id}")
def api_shopping_delete(item_id: str):
    res = daily.remove_shopping_by_id(item_id)
    if not res.get("removed"):
        return _err("not_found", "找不到這筆採買", 404)
    return res


@app.post("/api/moods")
def api_post_mood(body: dict = Body(...)):
    mood = str(body.get("mood", "")).strip()
    if not mood:
        return _err("invalid", "情緒不能空白", 400)
    return daily.log_mood(mood)
```

未捕獲的例外不要特製 500 handler 也行（FastAPI 預設 500）；不要把 traceback 塞進 JSON。不要實作 `POST /api/notes`。

- [ ] **Step 4: Run tests to verify they pass**

Run: `python -m pytest web/tests/test_api.py -v`

Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add web/app.py web/tests/test_api.py
git commit -m "feat(web): write APIs for expense, health, reminder, shopping, mood"
```

---

### Task 5: 單頁儀表板

**Files:**
- Create: `web/static/index.html`
- Create: `web/static/app.css`
- Create: `web/static/app.js`
- Modify: `web/app.py`（mount StaticFiles，且不可吃掉 `/api/*`）
- Modify: `web/tests/test_api.py`（`GET /` 回 HTML）

**Interfaces:**
- Consumes: Task 3–4 全部路由與 JSON 形狀
- Produces: 瀏覽器打開 `/` 可見七塊；表單 POST 後重抓該資源

靜態掛載必須在所有 `/api` 路由**之後**註冊，且用：

```python
from fastapi.responses import FileResponse

@app.get("/")
def index():
    return FileResponse(os.path.join(_STATIC, "index.html"))


app.mount("/static", StaticFiles(directory=_STATIC), name="static")
```

`index.html` 用 `/static/app.css` 與 `/static/app.js`。不要 `mount("/", StaticFiles(..., html=True))`——那會與 API 搶路徑。

- [ ] **Step 1: Write the failing GET / test**

```python
def test_index_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "道樞" in r.text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `python -m pytest web/tests/test_api.py::test_index_html -v`

Expected: FAIL — 404 or missing file

- [ ] **Step 3: Write the page**

`web/static/index.html`（骨架鎖這些 `id`，JS 只綁它們）：

```html
<!DOCTYPE html>
<html lang="zh-Hant">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>道樞</title>
  <link rel="stylesheet" href="/static/app.css">
</head>
<body>
  <div class="stars"></div>
  <div class="vignette"></div>
  <header>
    <div class="title">道樞</div>
    <div id="solar" class="sub"></div>
    <div id="memory-dir" class="path"></div>
  </header>
  <main>
    <section id="week" class="card"></section>
    <section class="card">
      <h2>支出</h2>
      <div id="expense-summary"></div>
      <ul id="expense-list"></ul>
      <form id="expense-form">
        <input name="item" placeholder="項目" required>
        <input name="amount" type="number" step="0.01" min="0.01" placeholder="金額" required>
        <select name="category">
          <option value="">自動分類</option>
          <option>飲食</option><option>交通</option><option>娛樂</option><option>學習</option><option>其他</option>
        </select>
        <button type="submit">記入</button>
      </form>
      <p class="err" id="expense-err"></p>
      <a id="expense-csv" href="/api/expenses.csv">下載本月 CSV</a>
    </section>
    <section class="card">
      <h2>健康</h2>
      <ul id="health-list"></ul>
      <form id="health-form">
        <input name="sleep_hours" type="number" step="0.1" min="0" placeholder="睡眠時數">
        <input name="exercise" placeholder="運動">
        <input name="water" placeholder="飲水">
        <button type="submit">打卡</button>
      </form>
      <p class="err" id="health-err"></p>
    </section>
    <section class="card">
      <h2>提醒</h2>
      <ul id="reminder-list"></ul>
      <form id="reminder-form">
        <input name="content" placeholder="內容" required>
        <input name="datetime" type="datetime-local" required>
        <button type="submit">新增</button>
      </form>
      <p class="err" id="reminder-err"></p>
    </section>
    <section class="card">
      <h2>採買</h2>
      <ul id="shopping-open"></ul>
      <ul id="shopping-done"></ul>
      <form id="shopping-form">
        <input name="item" placeholder="要買的" required>
        <button type="submit">加入</button>
      </form>
      <p class="err" id="shopping-err"></p>
    </section>
    <section class="card">
      <h2>情緒</h2>
      <ul id="mood-list"></ul>
      <form id="mood-form">
        <input name="mood" placeholder="今天感覺…" required>
        <button type="submit">記下</button>
      </form>
      <p class="err" id="mood-err"></p>
      <p id="mood-care" class="care"></p>
    </section>
    <section class="card">
      <h2>筆記</h2>
      <ul id="notes-due"></ul>
      <ul id="notes-recent"></ul>
      <p class="hint">複習請在對話裡說。這裡只看。</p>
    </section>
  </main>
  <script src="/static/app.js"></script>
</body>
</html>
```

`web/static/app.css` 必備規則（可加間距，不可改色系）：

```css
* { margin: 0; padding: 0; box-sizing: border-box; }
body {
  min-height: 100vh;
  font-family: "Microsoft JhengHei", "PingFang TC", serif;
  color: #e8e0ff;
  background: radial-gradient(circle at 50% 25%, #1a1438 0%, #0d0a1a 70%);
  padding: 1.5rem;
}
.stars { position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background-image:
    radial-gradient(1px 1px at 20% 30%, #fff7, transparent),
    radial-gradient(1px 1px at 70% 15%, #fff5, transparent),
    radial-gradient(2px 2px at 40% 60%, #fff4, transparent); }
.vignette { position: fixed; inset: 0; pointer-events: none; z-index: 0;
  background: radial-gradient(circle at center, transparent 45%, #000a 100%); }
header, main { position: relative; z-index: 1; }
.title { letter-spacing: .35em; color: #9b8cff; text-shadow: 0 0 12px #9b8cff88; }
.sub { margin-top: .4rem; font-size: .75rem; color: #6f6394; }
.path { font-size: .65rem; color: #5c5a80; word-break: break-all; }
main { display: grid; gap: 1rem; grid-template-columns: 1fr; margin-top: 1.2rem; }
@media (min-width: 900px) { main { grid-template-columns: 1fr 1fr; } #week { grid-column: 1 / -1; } }
.card { background: #171236aa; border: 1px solid #3a2f66; border-radius: 14px; padding: 1rem 1.2rem; }
h2 { font-size: .85rem; letter-spacing: .2em; color: #9b8cff; margin-bottom: .6rem; }
ul { list-style: none; font-size: .8rem; line-height: 1.7; }
form { display: flex; flex-wrap: wrap; gap: .4rem; margin-top: .6rem; }
input, select, button {
  background: #0d0a1a; color: #e8e0ff; border: 1px solid #3a2f66;
  border-radius: 6px; padding: .35rem .5rem; font: inherit;
}
button { cursor: pointer; color: #9b8cff; }
.err { color: #e08a8a; font-size: .75rem; min-height: 1.1em; margin-top: .3rem; }
.care { color: #b8a86a; font-size: .75rem; }
.due { color: #e08a8a; }
.hint { font-size: .7rem; color: #6f6394; margin-top: .4rem; }
a { color: #9b8cff; font-size: .75rem; }
```

`web/static/app.js` 行為鎖死：

1. `async function get(path)` / `async function send(method, path, body)` — 非 2xx 時丟出 `err.message`（從 JSON `message` 取）。
2. 頁載入呼叫 `refreshAll()`：並行 GET overview、expenses、health、reminders、shopping、moods、notes。
3. `renderWeek(overview)`：`#solar` 顯示 `solar_term.guide`；`#memory-dir` 顯示 `memory_dir`；`#week` 顯示 `expense_total`（加 `currency`）、`sleep_avg_hours`、`exercise_count`、`mood_trend` 三色數字、`study_notes_due`、`energy_insight`、`decisions_logged`；`care_flag` 為真時加一句「最近幾天感覺不太好」。
4. 各 list 用 `textContent` 填，**禁止**把使用者輸入當 `innerHTML`。
5. 提醒：`due===true` 的 `<li>` 加 class `due`，並排在未到期前面。
6. 採買：未勾進 `#shopping-open`（每列：文字 +「勾」鈕 POST `/api/shopping/{id}/check` +「刪」鈕 DELETE）；已勾進 `#shopping-done`（只顯示，可留刪）。
7. 表單 submit `preventDefault`，成功後清該塊 `err` 並只重抓該資源（支出成功也重抓 overview 以更新週報條）。失敗把 `message` 寫進對應 `#*-err`。
8. 提醒表單的 `datetime-local` 送出前轉成 `YYYY-MM-DDTHH:MM:00`（無時區，與 `daily.add_reminder` 的 ISO 字串一致）。
9. 健康：空白睡眠當「未填」不要送 0 當唯一欄（若三欄都空，瀏覽器仍 submit → 後端 400，把訊息顯示即可）。
10. 情緒成功後若回傳 `care_note`，寫入 `#mood-care`。
11. 筆記：`due` 與 `recent` 分兩個 ul；無寫入表單。

`refreshAll` 與各 render 寫完整，不要「TODO 補 render」。一份建議結構：

```javascript
const $ = (id) => document.getElementById(id);

async function get(path) {
  const r = await fetch(path);
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.message || r.statusText);
  return data;
}

async function send(method, path, body) {
  const r = await fetch(path, {
    method,
    headers: body ? { "Content-Type": "application/json" } : {},
    body: body ? JSON.stringify(body) : undefined,
  });
  const data = await r.json().catch(() => ({}));
  if (!r.ok) throw new Error(data.message || r.statusText);
  return data;
}

function li(text, cls) {
  const el = document.createElement("li");
  if (cls) el.className = cls;
  el.textContent = text;
  return el;
}

async function refreshAll() {
  const [ov, ex, he, re, sh, mo, no] = await Promise.all([
    get("/api/overview"),
    get("/api/expenses"),
    get("/api/health"),
    get("/api/reminders"),
    get("/api/shopping"),
    get("/api/moods"),
    get("/api/notes"),
  ]);
  renderWeek(ov);
  renderExpenses(ex);
  renderHealth(he);
  renderReminders(re);
  renderShopping(sh);
  renderMoods(mo);
  renderNotes(no);
}

function renderWeek(ov) {
  $("solar").textContent = ov.solar_term.guide || "";
  $("memory-dir").textContent = ov.memory_dir || "";
  const r = ov.report;
  const cur = r.currency || "";
  const mood = r.mood_trend || {};
  $("week").replaceChildren();
  const lines = [
    `近七日 ${r.period || ""}`,
    `支出 ${cur}${r.expense_total}　睡眠均 ${r.sleep_avg_hours}h　運動 ${r.exercise_count} 次`,
    `情緒 正${mood["正向"] || 0} 中${mood["中性"] || 0} 負${mood["負向"] || 0}　待複習 ${r.study_notes_due}　決策 ${r.decisions_logged}`,
    r.energy_insight || "",
  ];
  if (r.care_flag) lines.push("最近幾天感覺不太好。");
  for (const t of lines) $("week").appendChild(Object.assign(document.createElement("p"), { textContent: t }));
}

function renderExpenses(ex) {
  const s = ex.summary;
  const cats = Object.entries(s.by_category || {}).map(([k, v]) => `${k} ${s.currency || ""}${v}`).join("　");
  $("expense-summary").textContent = `${s.month} 合計 ${s.currency || ""}${s.total}　${cats}`;
  $("expense-list").replaceChildren();
  for (const rec of ex.recent || []) {
    $("expense-list").appendChild(li(`${rec.date}　${rec.item}　${rec.category}　${rec.amount}`));
  }
}

function renderHealth(he) {
  $("health-list").replaceChildren();
  for (const rec of he.records || []) {
    $("health-list").appendChild(li(`${rec.date}　睡${rec.sleep_hours || "—"}　${rec.exercise || "—"}　${rec.water || "—"}`));
  }
}

function renderReminders(re) {
  const recs = [...(re.records || [])].sort((a, b) => Number(b.due) - Number(a.due));
  $("reminder-list").replaceChildren();
  for (const rec of recs) {
    const row = li(`${rec.datetime}　${rec.content}`, rec.due ? "due" : "");
    const btn = document.createElement("button");
    btn.type = "button";
    btn.textContent = "完成";
    btn.addEventListener("click", async () => {
      try {
        await send("POST", `/api/reminders/${rec.id}/done`);
        $("reminder-err").textContent = "";
        renderReminders(await get("/api/reminders"));
      } catch (e) {
        $("reminder-err").textContent = e.message;
      }
    });
    row.appendChild(btn);
    $("reminder-list").appendChild(row);
  }
}

function renderShopping(sh) {
  $("shopping-open").replaceChildren();
  $("shopping-done").replaceChildren();
  for (const rec of sh.records || []) {
    const row = li(rec.item);
    const check = document.createElement("button");
    check.type = "button";
    check.textContent = "勾";
    check.addEventListener("click", async () => {
      try {
        await send("POST", `/api/shopping/${rec.id}/check`);
        $("shopping-err").textContent = "";
        renderShopping(await get("/api/shopping"));
      } catch (e) {
        $("shopping-err").textContent = e.message;
      }
    });
    const del = document.createElement("button");
    del.type = "button";
    del.textContent = "刪";
    del.addEventListener("click", async () => {
      try {
        await send("DELETE", `/api/shopping/${rec.id}`);
        $("shopping-err").textContent = "";
        renderShopping(await get("/api/shopping"));
      } catch (e) {
        $("shopping-err").textContent = e.message;
      }
    });
    if (!rec.checked) row.appendChild(check);
    row.appendChild(del);
    (rec.checked ? $("shopping-done") : $("shopping-open")).appendChild(row);
  }
}

function renderMoods(mo) {
  $("mood-list").replaceChildren();
  for (const rec of mo.records || []) {
    $("mood-list").appendChild(li(`${rec.date}　${rec.classification}　${rec.mood}`));
  }
}

function renderNotes(no) {
  $("notes-due").replaceChildren();
  $("notes-recent").replaceChildren();
  for (const rec of no.due || []) $("notes-due").appendChild(li(`到期　${rec.subject}　${rec.summary || rec.original}`));
  for (const rec of no.recent || []) $("notes-recent").appendChild(li(`${rec.subject}　${rec.summary || rec.original}`));
}

function bindForm(formId, errId, handler) {
  $(formId).addEventListener("submit", async (ev) => {
    ev.preventDefault();
    $(errId).textContent = "";
    try {
      await handler(new FormData(ev.target));
      ev.target.reset();
    } catch (e) {
      $(errId).textContent = e.message;
    }
  });
}

bindForm("expense-form", "expense-err", async (fd) => {
  const category = fd.get("category") || "";
  await send("POST", "/api/expenses", {
    item: fd.get("item"),
    amount: Number(fd.get("amount")),
    category,
  });
  renderExpenses(await get("/api/expenses"));
  renderWeek(await get("/api/overview"));
});

bindForm("health-form", "health-err", async (fd) => {
  const body = {};
  const sleep = fd.get("sleep_hours");
  if (sleep) body.sleep_hours = Number(sleep);
  if (fd.get("exercise")) body.exercise = fd.get("exercise");
  if (fd.get("water")) body.water = fd.get("water");
  await send("POST", "/api/health", body);
  renderHealth(await get("/api/health"));
  renderWeek(await get("/api/overview"));
});

bindForm("reminder-form", "reminder-err", async (fd) => {
  const raw = String(fd.get("datetime") || "");
  const iso = raw.length === 16 ? `${raw}:00` : raw;
  await send("POST", "/api/reminders", { content: fd.get("content"), datetime: iso });
  renderReminders(await get("/api/reminders"));
});

bindForm("shopping-form", "shopping-err", async (fd) => {
  await send("POST", "/api/shopping", { item: fd.get("item") });
  renderShopping(await get("/api/shopping"));
});

bindForm("mood-form", "mood-err", async (fd) => {
  const res = await send("POST", "/api/moods", { mood: fd.get("mood") });
  $("mood-care").textContent = res.care_note || "";
  renderMoods(await get("/api/moods"));
  renderWeek(await get("/api/overview"));
});

refreshAll().catch((e) => { $("week").textContent = e.message; });
```

`web/app.py` 在所有 API 路由之後加 `index` 與 `mount /static`（見本 task Interfaces）。

- [ ] **Step 4: Run tests**

Run: `python -m pytest web/tests/test_api.py -v`

Expected: PASS，且 `test_index_html` 過

手動（執行者本機）：

```bash
cd /c/Galaxy/daozhu
# Git Bash on Windows:
export DAOZHU_MEMORY_DIR="/c/Galaxy/Type_moon/.claude/daozhu-mcp/local_memory"
python -m web
```

瀏覽器開 `http://127.0.0.1:8765`，確認頂欄路徑是 Type_moon 那份、記一筆測試支出、整理後數字還在。測完可在對話裡刪該筆或留著——執行者自行決定，不要寫刪庫腳本。

- [ ] **Step 5: Commit**

```bash
git add web/static/index.html web/static/app.css web/static/app.js web/app.py web/tests/test_api.py
git commit -m "feat(web): local dashboard page for daily memory"
```

---

### Task 6: CI、README、CHANGELOG

**Files:**
- Modify: `.github/workflows/test.yml`
- Modify: `README.md`
- Modify: `README.zh-TW.md`
- Modify: `CHANGELOG.md`
- Modify: `CONTRIBUTING.md`

**Interfaces:**
- Consumes: `mcp/requirements-web.txt`、`python -m web`
- Produces: 預設 `test` job 仍只裝 `mcp/requirements.txt`；新 job `dashboard` 裝 web extras 並跑 `web/tests`

- [ ] **Step 1: Extend CI**

在 `.github/workflows/test.yml` 的 `jobs.test` 之後加（不要改舊 job 的 pip 行）：

```yaml
  dashboard:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Set up Python 3.12
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - name: Install mcp + web extras
        run: |
          pip install -r mcp/requirements.txt
          pip install -r mcp/requirements-web.txt
          pip install pytest
      - name: Run dashboard tests
        run: python -m pytest web/tests/ -v
```

- [ ] **Step 2: Docs**

`README.md` 在 `## Development` 之前插入：

```markdown
## Local dashboard (optional)

A loopback-only web UI for the same `local_memory/` the MCP uses. Not a chat window.

```bash
pip install -r mcp/requirements-web.txt
# optional: point at an existing store (e.g. a Claude Code project copy)
set DAOZHU_MEMORY_DIR=C:\path\to\local_memory
python -m web
```

Open `http://127.0.0.1:8765`. Binds to `127.0.0.1` only. Study notes are read-only; review them in chat.
```

Windows `set` 與 POSIX `export` 並陳。`README.zh-TW.md` 對應繁中一節「本機儀表板」，指令相同。

`CHANGELOG.md` 的 `## [Unreleased]` → `### Added` 加：

```markdown
- 本機記憶儀表板（`python -m web`，`127.0.0.1:8765`）：週報／支出／健康／提醒／採買／情緒可寫入，筆記只讀
- `daily.check_shopping_by_id` / `daily.remove_shopping_by_id`（MCP：`daozhu_check_shopping_by_id` / `daozhu_remove_shopping_by_id`）
```

`CONTRIBUTING.md` 的 Development setup 加：

```markdown
Optional dashboard:

```bash
pip install -r mcp/requirements-web.txt
python -m pytest web/tests/
```

New HTTP routes must call `daily` / `weekly` / `solarterm` — never write `local_memory` JSON from `web/`.
```

- [ ] **Step 3: Run the full suite locally**

```bash
cd /c/Galaxy/daozhu/mcp && python -m pytest tests/ -q
cd /c/Galaxy/daozhu && python -m pytest web/tests/ -q
```

Expected: 兩邊全綠。

- [ ] **Step 4: Commit**

```bash
git add .github/workflows/test.yml README.md README.zh-TW.md CHANGELOG.md CONTRIBUTING.md
git commit -m "docs: local dashboard install, CI job, changelog"
```

---

## Self-review

**Spec coverage**

| Spec 節 | Task |
|---------|------|
| §2 三層、不經 stdio、DAOZHU_MEMORY_DIR | 2, 3, 5 手動 |
| §3 目錄 `web/`、`python -m web` | 2, 5, 6 |
| §4 七塊、筆記只讀、心鏡色、無動畫 | 5 |
| §5 GET/POST 表 | 3, 4 |
| §5 採買按 id | 1, 4 |
| §6 錯誤形狀 | 4（forbidden 在 2） |
| §7 web tests + mcp 舊測零改 | 1–5 |
| §8 extras、README、CHANGELOG、CONTRIBUTING | 6 |
| §9 以後殼共用 URL | `__main__` 固定 8765，無第二套 API |
| 非目標（聊天／extension／筆記寫入） | 無對應 task |

**Placeholder scan:** 無 TBD。Task 2 的非 loopback 測試給了 TestClient `client=` 與 ASGI scope 後備，驗收條件是 403 本體。Task 5 的 JS 是完整可跑稿，不是「類似 Task N」。

**Type consistency:** `check_shopping_by_id` / `remove_shopping_by_id` 名稱從 Task 1 貫到 4–5。Overview JSON 四鍵 `status/report/solar_term/memory_dir` 前後一致。錯誤碼只有 `invalid` / `not_found` / `forbidden` /（未特製的 FastAPI 500）。
