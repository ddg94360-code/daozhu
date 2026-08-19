# 風水可填出生年 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 心鏡風水真抽從 textarea 解析出生年（可選性別），解析不到才回落今年。

**Architecture:** 只改 `web/static/xinjing.js`。抽出 `yearFrom`／`genderFrom`，與既有 `dtLocalFrom` 同風格。後端 `tianji_bridge` 已要 `year`，不改。無 JS 測試框架，不新開；後端缺 year 的 400 已存在。

**Tech Stack:** vanilla JS、FastAPI 既有 `/api/xinjing/cast`、pytest（不為本項新增）

**Spec:** [docs/2026-08-19-daozhu-dashboard-fengshui-year-design.md](2026-08-19-daozhu-dashboard-fengshui-year-design.md)

## Global Constraints

- 工作目錄 `c:\Galaxy\daozhu`。不改 Type_moon、不 push、不開 PR、不裝套件。
- 不改 `tianji_bridge.py`、`app.py`、`xinjing.html`、`xinjing_engine.html`。
- 不加獨立年份欄。風水不改吃 `dt_local`。
- 缺 POST body 仍 422。看板／內閣使用者輸入不當 innerHTML（本項只動心鏡 JS）。
- 不實作 B（會議暫存）或 C（Type_moon Loader）。
- ISO `1990-05-15` 只取年。範圍 1900–2100。

---

## File map

| 路徑 | 職責 |
|------|------|
| `web/static/xinjing.js` | `yearFrom`／`genderFrom`；fengshui 真抽改呼叫它們 |
| `web/static/xinjing.html` | 不改 |
| `web/tianji_bridge.py` | 不改 |

---

### Task 1: yearFrom／genderFrom 與真抽接線

**Files:**
- Modify: `web/static/xinjing.js`
- Do not modify: `web/tianji_bridge.py`, `web/static/xinjing.html`, Type_moon

**Interfaces:**
- Consumes: 既有 `looksIso(text)`（`/^\d{4}-\d{2}-\d{2}/` 且不以 `{` 開頭）
- Produces: `yearFrom(raw) → number`；`genderFrom(raw) → "男"|"女"|""`

- [ ] **Step 1: 在 `dtLocalFrom` 之後加入兩個函式**

放在 `function dtLocalFrom` 與 `async function get` 之間。

```javascript
function yearInRange(n) {
  return Number.isInteger(n) && n >= 1900 && n <= 2100;
}

function yearFrom(raw) {
  const text = String(raw || "").trim();
  const fallback = new Date().getFullYear();
  if (looksIso(text)) {
    const y = Number(text.slice(0, 4));
    if (yearInRange(y)) return y;
  }
  try {
    const parsed = JSON.parse(text);
    if (parsed && yearInRange(Number(parsed.year))) return Number(parsed.year);
    const nested = parsed && parsed.input && parsed.input.year;
    if (yearInRange(Number(nested))) return Number(nested);
    const iso = (parsed && parsed.dt_local) || (parsed && parsed.input && parsed.input.dt_local);
    if (typeof iso === "string" && looksIso(iso.replace(" ", "T"))) {
      const y = Number(String(iso).slice(0, 4));
      if (yearInRange(y)) return y;
    }
  } catch {
    /* 不是 JSON */
  }
  const m = text.match(/\d{4}/);
  if (m) {
    const y = Number(m[0]);
    if (yearInRange(y)) return y;
  }
  return fallback;
}

function genderFrom(raw) {
  try {
    const parsed = JSON.parse(String(raw || "").trim());
    const g = parsed && (parsed.gender || (parsed.input && parsed.input.gender));
    const s = String(g || "").trim();
    if (s === "男" || s === "女") return s;
  } catch {
    /* 不是 JSON */
  }
  return "";
}
```

- [ ] **Step 2: 改真抽 fengshui 分支**

把

```javascript
    if (mode === "fengshui") extra.year = new Date().getFullYear();
```

換成

```javascript
    if (mode === "fengshui") {
      extra.year = yearFrom(raw);
      const g = genderFrom(raw);
      if (g) extra.gender = g;
    }
```

不要改 gua／chart／submit／example 分支。

- [ ] **Step 3: 用 Node 核對純函式（不新開測試框架）**

在 `c:\Galaxy\daozhu` 執行（把函式內嵌進 `-e`，或暫時 `node` REPL）。預期：

| 輸入 | yearFrom | genderFrom |
|------|----------|------------|
| `1998` | 1998 | `""` |
| `{"year":1998}` | 1998 | `""` |
| `{"input":{"year":1998}}` | 1998 | `""` |
| `1990-05-15T08:00:00` | 1990 | `""` |
| `2024年要搬家嗎` | 2024 | `""` |
| `{"year":1998,"gender":"女"}` | 1998 | `女` |
| `{"gender":"其他"}` | 今年 | `""` |
| `""` | 今年 | `""` |
| `123` | 今年 | `""` |
| `9999` | 今年 | `""` |

可把 `xinjing.js` 前段（到 genderFrom 為止）拷到暫存 `.mjs` 跑 assert；**不要把暫存檔 commit**。核對完刪暫存。

- [ ] **Step 4: 跑既有 pytest，確認沒動到後端**

```bash
cd /c/Galaxy/daozhu
python -m pytest mcp/tests/ web/tests/ -q
```

Expected: 與第六期相同數量通過（136 或實作時的全綠）。FastAPI 0.116.1 × Python 3.14 DeprecationWarning 可忽略。

- [ ] **Step 5: Commit（僅當使用者明示可 commit；預設可停在這裡）**

若獲准：

```bash
cd /c/Galaxy/daozhu
git add web/static/xinjing.js docs/2026-08-19-daozhu-dashboard-fengshui-year-design.md docs/2026-08-19-daozhu-dashboard-fengshui-year-plan.md
git commit -m "feat(web): parse fengshui birth year from textarea"
```

未獲准則不要 `git commit`。不要 push。
