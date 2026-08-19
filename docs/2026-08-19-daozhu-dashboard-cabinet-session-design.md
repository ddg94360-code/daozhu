# 道樞儀表板後續 B：二次質詢行程暫存

日期：2026-08-19
狀態：設計已拍板，未實作
範圍：開源套件 `c:\Galaxy\daozhu` 內閣 API。不寫 `local_memory/`、不改 Type_moon、不 push、不開 PR。與 A（風水年）、C（Type_moon Loader）獨立，實作分開。

第四期 followup 可帶 `stages`，前端用分頁變數 `lastStages`。重整／關頁後沒有本場會議。曾考慮寫 daily（B2），已改回行程記憶體（B1）。

---

## 0. 已拍板

| 題 | 決定 |
|----|------|
| 落點 | **B1 行程 dict**，不寫碟 |
| 容量 | 只留**最近一場**；新 convene 覆蓋 |
| 使用者分片 | 不做。本機單人 |
| 客戶端仍帶 `stages` | **以客戶端為準**，不強制 session |
| 無 `stages` 且無暫存 | **400**「尚無本場會議」（不是 200 無上下文模板） |
| 寫決策日誌 | **不**因暫存而寫。既有 `persist: true` 仍只記「會議已開」 |
| preview | 不變、不建暫存 |
| `--window` 且 8765 已在聽 | 暫存跟已在聽的 uvicorn 走，視窗殼不另開行程、不清暫存 |

---

## 1. 問題與成功標準

現況：

- `POST /api/cabinet/convene` 回五階段，不回 session，伺服器不記。
- `POST /api/cabinet/followup` 有 list `stages` 就引用；沒有就走無上下文模板 **200**。
- [`web/static/cabinet.js`](../web/static/cabinet.js) `lastStages` 只活在該分頁。

成功看起來像：

1. convene 200 的 JSON 多 `session`（8 位小寫 hex 字串）。
2. 同一行程內，followup **不帶** `stages` → 用暫存的 stages 組「先前：…」，200。
3. 行程尚無 convene（或重啟後），followup 不帶 `stages` → **400** `{error:invalid, message:尚無本場會議}`。
4. followup 帶非空 list `stages` → 仍 200，**不讀**暫存（舊前端、測試 `test_followup_uses_stage_context` 不壞）。
5. 第二次 convene 覆蓋第一場；無 stages 的 followup 只看第二場。
6. 不出現 `local_memory/` 新檔、不改已入帳、不改五階段原文。
7. `speech.followup` 純函式仍可不帶 stages（單元測）。HTTP 層才要求本場或客戶端 stages。
8. 缺 POST body 仍 422。500 仍內部錯誤形。看板／內閣使用者輸入不當 innerHTML。

### 不做

- B2 寫 daily／新 JSON 集合
- 多場列表、過期 TTL、按 tab 分 session
- 把追問寫進決策
- 改 preview、改 depth 語意
- 同步到 Type_moon

---

## 2. 做法

新小模組 [`web/cabinet_session.py`](../web/cabinet_session.py)，避免 `app.py` 再長。行程級單槽：

```python
# 形狀（概念）
{
  "id": "a1b2c3d4",      # secrets.token_hex(4)
  "topic": str,
  "stages": list[dict],  # convene 回傳那份的淺拷貝
  "depth": str,
}
```

| 函式 | 行為 |
|------|------|
| `save(topic, stages, depth) -> str` | 覆蓋單槽，回 `id` |
| `get() -> dict\|None` | 無則 `None` |
| `stages_for_followup(body_stages) -> list` | 見下 |
| `clear()` | 測用；正式路由不暴露 |

`stages_for_followup(body_stages)`：

- `body_stages` 是 **list**（含空 list）→ 回該 list（客戶端為準；空 list 視為「有帶 stages」，不當「尚無本場」）。
- 否則看單槽：有 `stages` list → 回它。
- 否則 **raise ValueError("尚無本場會議")**。

`app.py`：

- convene 在組好 `preview` 後 `preview["session"] = cabinet_session.save(topic, stages, depth)`。
- followup 在空白檢查之後：

```python
try:
    stages = cabinet_session.stages_for_followup(
        body.get("stages") if isinstance(body.get("stages"), list) else None
    )
except ValueError as e:
    return _err("invalid", str(e), 400)
```

其後 `speech.followup(..., stages)` 與 LLM `stage_context` 用這個 `stages`。不把 `session` id 當 followup 必填欄（單槽就夠；回 `session` 只為除錯／之後若要對 id）。

前端 [`cabinet.js`](../web/static/cabinet.js)：convene／preview 仍把回傳 stages 畫上並寫 `lastStages`。followup **可繼續送** `lastStages`（重整前行為不變）。重整後 `lastStages=[]`，若不送或送的不是 list，伺服器用暫存。為讓重整後的表單不必改，followup 在 `lastStages.length === 0` 時**省略** `stages` 鍵，讓伺服器走暫存。

pytest 的 TestClient 與 app 同行程，單槽會跨測試污染：**每個測 convene／followup 的測試**在開頭 `cabinet_session.clear()`，或 `conftest` 的 fixture autouse clear。必做。

---

## 3. 測試（[`web/tests/test_phase4.py`](../web/tests/test_phase4.py)）

改：

- `test_followup_template`、`test_followup_without_stages_still_works`：不帶 stages 且未 convene → **400**，`message` 含「尚無本場會議」。可合併成一條。
- `test_followup_uses_stage_context`：仍帶 stages，**200**，不依賴暫存。
- `test_followup_unknown_name_400`、`test_followup_blank_400`、422：不變。
- `test_speech_followup_does_not_need_preview`：不變（純函式）。

加：

- convene 後不帶 stages 的 followup → 200，body 含本場結辯／該內閣摘句。
- convene A 再 convene B，不帶 stages 的 followup 只見 B。
- convene 回傳有 8 hex `session`。
- `clear()` 後不帶 stages → 400。

---

## 4. 風險

| 風險 | 處理 |
|------|------|
| 測試互相污染 | autouse `clear()` |
| 兩分頁搶單槽 | 已拍板接受（本機單人） |
| 重開 `python -m web` 暫存沒了 | 已拍板；文件寫明 |
| uvicorn `--reload` 子行程 | 重載即忘；可接受 |
| 空 list `stages: []` | 當客戶端明示無上下文，**不** 400、也不讀暫存。followup 模板無「先前」 |

---

## 5. 檔案

- 新增：`web/cabinet_session.py`
- 改：`web/app.py`（convene 存、followup 取）
- 改：`web/static/cabinet.js`（`lastStages.length===0` 時省略 stages）
- 改：`web/tests/test_phase4.py`、必要時 `web/tests/conftest.py`
- 不改：`mcp/daily.py`、`local_memory/`、Type_moon
