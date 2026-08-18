# 道樞記憶儀表板（第二期）設計

日期：2026-08-18
狀態：實作中
範圍：開源套件 `c:\Galaxy\daozhu`。Type_moon 實例不改、不同步、不 push、不開 PR。

第一期是單頁記憶看板。第二期把 `web/` 做成三個 URL：看板補完＋感知條、內閣組閣預覽、心鏡獨立頁。沒有聊天後端。

---

## 1. 問題與成功標準

第一期刻意拿掉筆記寫入、決策、道藏、500 handler、視覺薄皮。日常複習與決策仍必須走進對話；心鏡只能用 CLI 生成 HTML。

成功看起來像：

1. `/` 能新增／複習／刪筆記；記一筆決策後列表看得到；道藏四欄有內容或空狀態。
2. 頂欄感知條依記憶亮燈；空庫不炸、不寫「本次感知：…」。
3. `/cabinet` 輸入「組員不做事該怎麼講」→ 儒家主＋縱橫家輔，五階段空位可見，沒有假發言。
4. `/xinjing` 選 tarot、載入 example → 播示範動畫；貼壞 JSON → 該頁顯示中文原因。
5. 業務例外仍 400／404；未捕獲例外 500 且無堆疊；缺 POST body 仍 422。
6. `mcp/tests` 舊斷言零改仍全過（可新增測試）；`web/tests` 覆蓋新路由。第一期 `test_notes_are_read_only_shape` 的 POST 404/405 斷言改成 200——這是已知契約變更。

### 做

| 塊 | 做什麼 |
|----|--------|
| 筆記 | 完整 CRUD：新增（科目＋內容＋複習天數）、按 id 標已複習、按 id 刪。現有模糊字串工具保留給對話。 |
| 決策 | 可寫：題目＋裁決＋理由。列表只讀最近數則。不改、不刪。 |
| 道藏 | 只讀：四人格各召回最近數則。不寫入。 |
| 錯誤 | 統一 500 `{error: internal, message: 內部錯誤}`。缺 POST body 仍 422。 |
| 感知條 | 裝飾＋記憶推斷。七層當標誌；依最近情緒／待辦／到期／待複習亮燈。 |
| 內閣 | `/cabinet`：填議題 → 依 cabinet-workflow 排出出席與五階段空位。不生成會議文字。 |
| 心鏡 | `/xinjing`：七模式＋貼 JSON 或載入 `examples/` → `xinjing_render.render()`。不算命。 |
| 導覽 | 頂欄：看板／內閣／心鏡。看板頁仍無翻牌、無進場特效。 |

### 不做

- 聊天窗、串流、模型後端、真會議文字、真抽牌、真排盤
- VS Code 側欄、桌面殼、遠端、帳密、CORS、WebSocket
- 改已入帳金額、改提醒時間、改／刪決策、寫入道藏
- 同步 `web/` 到 Type_moon；把 422 改成 400

---

## 2. 架構

```
瀏覽器
  GET /              看板（七塊＋筆記寫入＋決策＋道藏＋感知條）
  GET /cabinet       內閣組閣預覽
  GET /xinjing       心鏡播放器
        │  HTTP，只打 127.0.0.1
        ▼
web/app.py           FastAPI：驗欄位、擋非本機、500 handler
web/cabinet.py       議題 → 出席名單（純函數，不碰記憶）
web/perception.py    記憶 → 七層亮燈（純函數）
        │  直接 import
        ▼
mcp/daily.py · weekly.py · solarterm.py · daozang.py · memory_store.py
skills/daozhu/xinjing/xinjing_render.py
        ▼
local_memory/        與 MCP 同一份
```

規則沿用第一期：不經 MCP stdio、不自行 replace JSON、只認 `DAOZHU_MEMORY_DIR`、綁 `127.0.0.1:8765`、不開 CORS。

---

## 3. 記憶層變更

筆記目前沒有 `id`。網頁不得用模糊字串對「物理」這種重複科目。

- `add_study_note` 新筆記加 `id`（`uuid.uuid4().hex[:8]`，與提醒／採買同一形狀）。
- 新增 `mark_study_note_reviewed_by_id(note_id) -> {"matched": bool}`。
- 新增 `delete_study_note_by_id(note_id) -> {"removed": int}`。
- 舊的 `mark_study_note_reviewed(keyword)`／`delete_study_note(keyword)` 契約不變。
- 舊筆記沒有 id：GET 仍回傳；前端不顯示複習／刪按鈕。不回填、不 replace。
- MCP `_TOOLS` 加兩支 by-id。決策不加 id（不改不刪）。

---

## 4. HTTP API

### 讀

| 路徑 | 回傳 |
|------|------|
| `GET /api/notes` | 同第一期，每筆多帶既有欄位（新筆記含 `id`） |
| `GET /api/decisions` | `{records: daily.review_decisions()[:20]}` |
| `GET /api/daozang` | `{personae: {daoist: recall..., ...}}`；四人格都召回，空庫 `records=[]` |
| `GET /api/perception` | 見 §5 |
| `POST /api/cabinet/preview` | 見 §6 |
| `GET /api/xinjing/examples` | `{modes: ["tarot","gua","yuan","chart","fengshui","star","dream"]}` |
| `GET /api/xinjing/examples/{mode}` | example JSON 原樣；未知 mode 404 |
| `POST /api/xinjing/render` | `{mode, data}` → `text/html`；未知 mode／data 非物件 400 |

### 寫

| 路徑 | body | 呼叫 |
|------|------|------|
| `POST /api/notes` | `{subject, content, review_days?}` | `add_study_note`。subject／content 空 → 400。`review_days` 缺省 7；非整數或 <0 → 400 |
| `POST /api/notes/{id}/reviewed` | 無 | `mark_study_note_reviewed_by_id`；false → 404 |
| `DELETE /api/notes/{id}` | 無 | `delete_study_note_by_id`；0 → 404 |
| `POST /api/decisions` | `{topic, verdict, reason?}` | `log_decision`。topic／verdict 空 → 400 |

沒有：改決策、刪決策、POST 道藏、改金額。

### 錯誤

同第一期 `{error, message}`。另加：

| 情況 | HTTP | error |
|------|------|-------|
| 未捕獲例外 | 500 | `internal`（message 固定「內部錯誤」，不丟堆疊） |
| 缺 POST body | 422 | FastAPI 預設，不改 |

`RequestValidationError` 不攔截。`HTTPException` 不攔截。

---

## 5. 感知條（裝飾＋記憶推斷）

`GET /api/perception`：

```json
{
  "layers": [
    {"key": "emotion", "label": "情緒", "on": false, "hint": ""},
    {"key": "task", "label": "任務", "on": false, "hint": ""},
    {"key": "interpersonal", "label": "人際", "on": false, "hint": ""},
    {"key": "complexity", "label": "複雜", "on": false, "hint": ""},
    {"key": "concise", "label": "精簡", "on": false, "hint": ""},
    {"key": "tone", "label": "語氣", "on": false, "hint": ""},
    {"key": "energy", "label": "精力", "on": false, "hint": ""}
  ],
  "disclaimer": "依記憶推斷，不是一次真實對話感知。"
}
```

推斷（純函數，讀現成 daily／weekly，不寫檔）：

| 層 | on | hint |
|----|----|------|
| 情緒 | 最近一則 mood 存在 | `最近：正向／中性／負向` |
| 任務 | pending reminders > 0 或 due notes > 0 | `待辦 N／到期筆記 M` |
| 人際 | 永遠 false | 空（沒有人際資料） |
| 複雜 | 近 7 日 `decisions_logged` ≥ 1 | `本週決策 N` |
| 精簡 | 永遠 false | 空 |
| 語氣 | 永遠 false | 空 |
| 精力 | `energy_insight` 不含「數據不足」 | 洞察原文（可截到 40 字） |

畫面：七顆小標，`on` 用紫 `#9b8cff`，`off` 用 `#5c5a80`。旁邊一行 disclaimer。不寫「本次感知」。

---

## 6. 內閣預覽

`POST /api/cabinet/preview` body `{topic}`。topic 空 → 400。

回傳：

```json
{
  "topic": "…",
  "rule": "人際/師生/親友/倫理",
  "chair": "議長（執中）",
  "core": [{"name": "儒家", "role": "主"}],
  "adjunct": [{"name": "縱橫家", "role": "輔"}],
  "stages": [
    {"name": "開題", "who": "議長", "body": ""},
    {"name": "各抒己見", "who": "核心內閣", "body": ""},
    {"name": "列席補充", "who": "列席內閣", "body": ""},
    {"name": "議長結辯", "who": "議長", "body": ""},
    {"name": "您裁決", "who": "你", "body": ""}
  ],
  "disclaimer": "只排出席，不生成會議文字。"
}
```

關鍵詞表（先命中先用，由上而下）：

| 特徵（任一子串） | 核心 | 列席 |
|------------------|------|------|
| 教授／老師／組員／同學／主管／老闆／同事／朋友／家人／男友／女友／對象／客戶／室友／親戚／長輩／人際／倫理 | 儒家主 | 縱橫家輔 |
| 制度／規則／績效／截止／待辦／時間管理 | 法家主 | 墨家輔 |
| 競爭／談判／資源／說服 | 縱橫家主 | 兵家輔 |
| 焦慮／壓力／迷惘／意義／想放棄／好煩／累 | 道家主 | 佛教輔 |
| 該不該／要不要 | 儒家＋法家＋道家（皆核心，無主輔） | 無 |
| 怎麼執行／步驟／怎麼做 | 法家＋兵家＋墨家 | 無 |
| 生涯／長期／規劃 | 道家＋儒家＋法家 | 無 |

都沒命中：儒家＋法家＋道家（與「該不該」同一組）。`rule` 寫「預設（價值／成本／感受）」。

不呼叫 LLM。不把預覽寫進決策日誌。使用者若要把裁決記入，回看板決策塊手寫。

---

## 7. 心鏡

`/xinjing` 獨立頁。七顆模式鈕＋textarea＋「載入示範」＋「播放」。

- 載入示範：`GET /api/xinjing/examples/{mode}` 填進 textarea。
- 播放：`POST /api/xinjing/render`，回 HTML 用 iframe `srcdoc` 或新開 `/xinjing/play` 回完整 HTML。採 **回完整 HTML 頁**（`Content-Type: text/html`），前端用 iframe `srcdoc` 以免破壞外殼導覽。
- 未知 mode／JSON 非物件 → 400「模式須為七模式之一」／「資料須為 JSON 物件」。
- 不算卦、不抽牌、不接 tianji。example JSON 形狀即日後 tianji 接縫。

`xinjing_render.render(mode, data)` 原樣呼叫。引擎檔只讀，不改動畫。

---

## 8. 畫面

三頁共用 `app.css` 色票。頂欄導覽：`看板` `/` · `內閣` `/cabinet` · `心鏡` `/xinjing`。

看板新增：

- `#perception` 七層標誌
- 筆記塊：表單（科目／內容／複習天數）＋到期列「複習」「刪」＋最近列「刪」
- `#decisions` 塊：列表＋表單
- `#daozang` 塊：四人格只讀

`/cabinet`：題目 textarea、預覽鈕、出席名單、五階段空卡。
`/xinjing`：模式鈕、textarea、iframe 舞台。動畫只發生在 iframe 內。

使用者輸入一律 `textContent`，禁止當 `innerHTML`。心鏡 iframe 的 HTML 來自自己的 render（受信任的引擎＋使用者 JSON 欄位——引擎本身用 innerHTML；第二期不重寫引擎）。textarea 內容不當看板 innerHTML。

---

## 9. 測試

- `mcp/tests`：追加 by-id 筆記測試。舊模糊字串測試不改。
- `web/tests`：筆記 CRUD、決策 POST、道藏 GET、perception 空庫、cabinet 人際題、xinjing example／壞 JSON、500 handler（可 patch 一個路由 raise）、`POST /api/notes` 200（取代只讀斷言）、缺 body 仍 422。
- 舊 `mcp/tests` 全過。

---

## 10. 已否決

- 感知條寫 `last_perception`（沒有對話層可寫）
- 內閣頁生成發言
- 心鏡嵌進首頁一塊
- 舊筆記回填 id
- 決策改／刪
