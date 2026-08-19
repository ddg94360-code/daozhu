# 道樞儀表板後續 A：風水可填出生年

日期：2026-08-19
狀態：設計已拍板，未實作
範圍：開源套件 `c:\Galaxy\daozhu` 心鏡前端。不改 Type_moon、不 push、不開 PR。與 B（會議暫存）、C（Type_moon Loader）獨立，實作分開。

第四期風水真抽把 `year` 寫死為 `new Date().getFullYear()`，textarea 裡的出生年被丟掉。後端契約已正確。

---

## 0. 已拍板

| 題 | 決定 |
|----|------|
| 怎麼填年 | textarea 解析，**不加**獨立年份欄 |
| 解析不到 | 回落今年（與現況相同） |
| 性別 | 可選從 textarea 讀 `gender`（男／女）；沒有則不送，後端預設「男」 |
| 後端 | **不改** `tianji_bridge`／`app.py` |
| 引擎殼 | **不改** `xinjing_engine.html` |
| 風水改吃 `dt_local` | **不做**。八宅只要出生年 |
| ISO 字串 | `1990-05-15` 只取年 `1990`，不當完整生日 |

---

## 1. 問題與成功標準

後端 `cast(mode="fengshui")` 已要 `year`，缺則 `ValueError("風水須提供 year")`。前端 [`web/static/xinjing.js`](../web/static/xinjing.js) 真抽時：

```js
if (mode === "fengshui") extra.year = new Date().getFullYear();
```

textarea 的 `1998` 或 `{"year":1998}` 不會進 POST。

成功看起來像：

1. textarea `1998` 或 `{"year":1998}` 或 `{"input":{"year":1998}}` → POST `/api/xinjing/cast` 的 `year` 為 `1998`。
2. `1990-05-15T08:00:00` 或 JSON 內同等 ISO → `year` 為 `1990`。
3. `2024年要搬家嗎` → `year` 為 `2024`（第一個四位數年）。
4. 空 textarea、無四位數、JSON 無 year → `year` 為今年。
5. JSON `{"year":1998,"gender":"女"}` → 一併送 `gender`。非法／缺省不送 `gender`。
6. 非 fengshui 模式行為不變。舊 pytest 全過。缺 POST body 仍 422。

### 不做

- 獨立 `<input type="number">` 年份欄
- 改 `tianji_bridge`、改 422／500、回填舊筆記
- 把風水當八字（不要日柱、不要時辰）
- 同步 `web/` 到 Type_moon
- B、C 的檔案

---

## 2. 做法

只改 [`web/static/xinjing.js`](../web/static/xinjing.js)。抽出與 `dtLocalFrom` 同風格的純函式，真抽 fengshui 時呼叫。

### `yearFrom(raw) → number`

順序（先命中先用）：

1. `looksIso(raw)` → `Number(raw.slice(0, 4))`，若在 1900–2100 則用。
2. `JSON.parse(raw)` 成功：
   - `parsed.year` 為數字或數字字串 → 取整。
   - 否則 `parsed.input.year` 同上。
   - 否則若 `parsed.dt_local`／`parsed.input.dt_local` 像 ISO → 取前年四位。
3. `raw.match(/\d{4}/)` 第一組，值在 1900–2100。
4. 以上皆無 → `new Date().getFullYear()`。

範圍外（如 `123`、`9999`）不當年份，落到下一步或今年。

### `genderFrom(raw) → "男"|"女"|""`

僅 JSON：`parsed.gender` 或 `parsed.input.gender` 去掉空白後為「男」或「女」才回傳；否則 `""`。真抽只在非空時 `extra.gender = …`。

### 真抽

```js
if (mode === "fengshui") {
  extra.year = yearFrom(raw);
  const g = genderFrom(raw);
  if (g) extra.gender = g;
}
```

播放（submit）仍只把 textarea 當 JSON 資料丟 render，不經 yearFrom。載入示範不變。

---

## 3. 測試

前端目前無 JS 單測。契約用 pytest 鎖後端（已有：缺 year → 400）。本項可選：

- 在 `web/tests/test_phase4.py` 加一條：接假 tianji 時 POST `{mode:fengshui, year:1998}` 200，且不強制前端。前端驗收靠手動：textarea `1998` 真抽，回傳文案含該年命卦（或 Network 看 body）。

不為 A 新開測試框架。不改舊測。

---

## 4. 風險

| 風險 | 處理 |
|------|------|
| textarea 兼問題與年份 | `2024年要搬家嗎` 吃 2024，已拍板為預期 |
| 示範 JSON 若含今年以外的 year | 載入示範後再真抽會用示範的 year；可接受 |
| 使用者輸入不當 innerHTML | 本項不改 DOM 寫入方式 |

---

## 5. 檔案

- 改：`web/static/xinjing.js`
- 可選改：`web/tests/test_phase4.py`（只加後端 year=1998 假引擎一條，若尚無）
- 不改：`web/tianji_bridge.py`、`web/static/xinjing.html`、Type_moon
