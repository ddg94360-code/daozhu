# 二次質詢行程暫存 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** convene 把最近一場五階段放進行程單槽；followup 無客戶端 `stages` 時用暫存，兩者都沒有則 400「尚無本場會議」。

**Architecture:** 新模組 `web/cabinet_session.py` 管單槽。`app.py` convene 存、followup 取。`cabinet.js` 在 `lastStages` 為空時省略 `stages` 鍵。不寫 `local_memory/`。pytest autouse `clear()` 防污染。

**Tech Stack:** Python 3.10+、FastAPI、pytest、vanilla JS

**Spec:** [docs/2026-08-19-daozhu-dashboard-cabinet-session-design.md](2026-08-19-daozhu-dashboard-cabinet-session-design.md)

## Global Constraints

- 工作目錄 `c:\Galaxy\daozhu`。不改 Type_moon、不 push、不開 PR、不裝套件、不寫 daily 新集合。
- 缺 POST body 仍 422。500 message「內部錯誤」。
- 看板／內閣使用者輸入不當 innerHTML。
- 客戶端帶 list `stages`（含空 list）以客戶端為準，不讀暫存。
- `speech.followup` 純函式仍可不帶 stages。HTTP 層才 400。
- 不實作 A（風水年）或 C（Type_moon Loader）。
- 只留最近一場；新 convene 覆蓋。

---

## File map

| 路徑 | 職責 |
|------|------|
| `web/cabinet_session.py` | 單槽 save／get／clear／stages_for_followup |
| `web/app.py` | convene 寫入 `session`；followup 經 stages_for_followup |
| `web/static/cabinet.js` | lastStages 空則省略 stages |
| `web/tests/conftest.py` | autouse clear |
| `web/tests/test_phase4.py` | 改舊 200、加覆蓋／暫存測 |
| `mcp/daily.py` | 不改 |

---

### Task 1: cabinet_session 模組（TDD）

**Files:**
- Create: `web/cabinet_session.py`
- Test: `web/tests/test_phase4.py`（先加單元測；HTTP 測在 Task 2）

**Interfaces:**
- Consumes: 無
- Produces:
  - `save(topic: str, stages: list, depth: str) -> str`（8 hex）
  - `get() -> dict | None`
  - `clear() -> None`
  - `stages_for_followup(body_stages) -> list`（list 原樣回；否則單槽；否則 `ValueError("尚無本場會議")`）

- [ ] **Step 1: 寫失敗的單元測**

在 `web/tests/test_phase4.py` 檔首已有 `import speech`／`tianji_bridge`，加 `import cabinet_session`。於 followup 測附近插入：

```python
def test_session_save_get_clear():
    cabinet_session.clear()
    assert cabinet_session.get() is None
    sid = cabinet_session.save("題甲", [{"name": "開題", "body": "甲"}], "brief")
    assert len(sid) == 8 and all(c in "0123456789abcdef" for c in sid)
    got = cabinet_session.get()
    assert got["id"] == sid
    assert got["topic"] == "題甲"
    assert got["stages"][0]["body"] == "甲"
    assert got["depth"] == "brief"
    cabinet_session.save("題乙", [{"name": "開題", "body": "乙"}], "deep")
    assert cabinet_session.get()["topic"] == "題乙"
    cabinet_session.clear()
    assert cabinet_session.get() is None


def test_stages_for_followup_prefers_client_list():
    cabinet_session.clear()
    cabinet_session.save("題", [{"name": "開題", "body": "存檔"}], "brief")
    client = [{"name": "開題", "body": "客戶"}]
    assert cabinet_session.stages_for_followup(client) == client
    assert cabinet_session.stages_for_followup([]) == []
    assert cabinet_session.stages_for_followup(None)[0]["body"] == "存檔"
    cabinet_session.clear()
    with pytest.raises(ValueError, match="尚無本場會議"):
        cabinet_session.stages_for_followup(None)
```

檔頂加 `import pytest`（若尚未）。

- [ ] **Step 2: 跑測確認失敗**

```bash
cd /c/Galaxy/daozhu
python -m pytest web/tests/test_phase4.py::test_session_save_get_clear web/tests/test_phase4.py::test_stages_for_followup_prefers_client_list -q
```

Expected: FAIL（`cabinet_session` 不存在或無函式）。

- [ ] **Step 3: 寫最小實作**

`web/cabinet_session.py`：

```python
"""本場內閣會議行程暫存。只留最近一場，不寫碟。"""
from __future__ import annotations

import copy
import secrets
from typing import Any

_SLOT: dict[str, Any] | None = None


def clear() -> None:
    global _SLOT
    _SLOT = None


def get() -> dict[str, Any] | None:
    return _SLOT


def save(topic: str, stages: list, depth: str) -> str:
    global _SLOT
    sid = secrets.token_hex(4)
    _SLOT = {
        "id": sid,
        "topic": topic,
        "stages": copy.deepcopy(list(stages)),
        "depth": depth,
    }
    return sid


def stages_for_followup(body_stages: Any) -> list:
    if isinstance(body_stages, list):
        return body_stages
    if _SLOT and isinstance(_SLOT.get("stages"), list):
        return _SLOT["stages"]
    raise ValueError("尚無本場會議")
```

- [ ] **Step 4: 再跑單元測**

```bash
cd /c/Galaxy/daozhu
python -m pytest web/tests/test_phase4.py::test_session_save_get_clear web/tests/test_phase4.py::test_stages_for_followup_prefers_client_list -q
```

Expected: PASS。

- [ ] **Step 5: 先不要 commit**（與 Task 2 同一次；使用者未明示則整計畫都不 commit）

---

### Task 2: HTTP convene／followup 接線

**Files:**
- Modify: `web/app.py`
- Modify: `web/tests/conftest.py`
- Modify: `web/tests/test_phase4.py`

**Interfaces:**
- Consumes: `cabinet_session.save`／`stages_for_followup`／`clear`
- Produces: convene JSON 多 `session`；followup 無 list stages 且無槽 → 400

- [ ] **Step 1: 改／加 HTTP 測（先跑應紅）**

把 `test_followup_template` 與 `test_followup_without_stages_still_works` **合併／改寫**為：

```python
def test_followup_without_stages_and_no_session_400(client):
    r = client.post(
        "/api/cabinet/followup",
        json={"topic": "組員不做事該怎麼講", "name": "儒家", "question": "先說哪一句"},
    )
    assert r.status_code == 400
    assert r.json()["error"] == "invalid"
    assert "尚無本場會議" in r.json()["message"]
```

刪除（或不再期望 200 的）舊兩條同義測。保留：

- `test_followup_uses_stage_context`（帶 stages → 200）
- `test_followup_unknown_name_400`
- `test_followup_blank_400`
- `test_speech_followup_does_not_need_preview`

新增：

```python
def test_convene_returns_session_hex(client):
    r = client.post("/api/cabinet/convene", json={"topic": "該不該接這個專案"})
    assert r.status_code == 200
    sid = r.json()["session"]
    assert len(sid) == 8 and all(c in "0123456789abcdef" for c in sid)


def test_followup_uses_server_session_without_stages(client):
    client.post("/api/cabinet/convene", json={"topic": "組員不做事該怎麼講"})
    r = client.post(
        "/api/cabinet/followup",
        json={"topic": "組員不做事該怎麼講", "name": "儒家", "question": "先說哪一句"},
    )
    assert r.status_code == 200
    body = r.json()["body"]
    assert body
    assert "非正式" in r.json()["disclaimer"]
    assert "先前" in body or "正名" in body or "名分" in body or "組員" in body


def test_second_convene_replaces_session(client):
    client.post("/api/cabinet/convene", json={"topic": "第一場議題甲"})
    client.post("/api/cabinet/convene", json={"topic": "第二場議題乙"})
    r = client.post(
        "/api/cabinet/followup",
        json={"topic": "第二場議題乙", "name": "法家", "question": "成本"},
    )
    assert r.status_code == 200
    assert "乙" in r.json()["body"] or "第二場" in r.json()["body"]
    assert "議題甲" not in r.json()["body"]
```

`test_followup_uses_stage_context` 不變（明確送 stages）。

- [ ] **Step 2: 跑上述 HTTP 測，確認新行為尚未接線而紅**

```bash
cd /c/Galaxy/daozhu
python -m pytest web/tests/test_phase4.py::test_followup_without_stages_and_no_session_400 web/tests/test_phase4.py::test_convene_returns_session_hex web/tests/test_phase4.py::test_followup_uses_server_session_without_stages -q
```

Expected: 無 session 鍵 → FAIL；不帶 stages 仍 200 → `test_followup_without_stages_and_no_session_400` FAIL。

- [ ] **Step 3: conftest autouse clear**

`web/tests/conftest.py` 在 `client` fixture 之後加：

```python
@pytest.fixture(autouse=True)
def _clear_cabinet_session():
    import cabinet_session

    cabinet_session.clear()
    yield
    cabinet_session.clear()
```

- [ ] **Step 4: 接 `app.py`**

檔內其它 import 旁加 `import cabinet_session`（`app.py` 已把 `_WEB` 插入 `sys.path`，與 `import speech` 相同）。

`api_cabinet_convene` 在 `preview["persisted"] = …` 之後、`return preview` 之前：

```python
    preview["session"] = cabinet_session.save(topic, stages, depth)
    return preview
```

`api_cabinet_followup` 把

```python
    stages = body.get("stages") if isinstance(body.get("stages"), list) else None
    try:
        template = speech.followup(name, topic, question, stages)
```

換成

```python
    try:
        stages = cabinet_session.stages_for_followup(
            body.get("stages") if isinstance(body.get("stages"), list) else None
        )
        template = speech.followup(name, topic, question, stages)
```

`except ValueError` 仍 400（「查無此內閣」與「尚無本場會議」同一支）。LLM 區塊繼續用這個 `stages`。

空白檢查（topic／name／question）仍在 `stages_for_followup` **之前**。缺 body 仍 422。

- [ ] **Step 5: 跑第四期測＋全套**

```bash
cd /c/Galaxy/daozhu
python -m pytest web/tests/test_phase4.py -q
python -m pytest mcp/tests/ web/tests/ -q
```

Expected: 全綠。

---

### Task 3: 前端省略空 stages

**Files:**
- Modify: `web/static/cabinet.js`

**Interfaces:**
- Consumes: `lastStages` 陣列
- Produces: followup POST 在長度 0 時不帶 `stages` 鍵

- [ ] **Step 1: 改 followup submit**

把

```javascript
    const data = await send("POST", "/api/cabinet/followup", {
      topic,
      name: $("cabinet-followup-name").value,
      question: $("cabinet-followup-q").value,
      stages: lastStages,
    });
```

換成

```javascript
    const payload = {
      topic,
      name: $("cabinet-followup-name").value,
      question: $("cabinet-followup-q").value,
    };
    if (lastStages.length) payload.stages = lastStages;
    const data = await send("POST", "/api/cabinet/followup", payload);
```

`render` 仍 `lastStages = preview.stages || []`。preview（空 body）不要呼叫 `cabinet_session.save`（後端本就不存 preview）。

- [ ] **Step 2: 再跑全套確認沒改壞後端**

```bash
cd /c/Galaxy/daozhu
python -m pytest mcp/tests/ web/tests/ -q
```

- [ ] **Step 3: Commit（僅當使用者明示）**

```bash
cd /c/Galaxy/daozhu
git add web/cabinet_session.py web/app.py web/static/cabinet.js web/tests/conftest.py web/tests/test_phase4.py docs/2026-08-19-daozhu-dashboard-cabinet-session-design.md docs/2026-08-19-daozhu-dashboard-cabinet-session-plan.md
git commit -m "feat(web): keep last cabinet convene in process for followup"
```

未獲准則不要 commit、不要 push。
