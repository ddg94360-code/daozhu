# 道樞記憶儀表板（第三期）設計

日期：2026-08-18
狀態：實作中
範圍：開源套件 `c:\Galaxy\daozhu`。Type_moon 實例不改、不同步、不 push、不開 PR。

第二期是三頁記憶看板。2.5 期換外殼色票。第三期在同一套 loopback 網頁上加三塊：**看板聊天窗、內閣真會議、心鏡外掛 tianji**。不做 VS Code 側欄、不做桌面殼。

---

## 0. 已拍板

| 題 | 決定 |
|----|------|
| 三塊都做還是先一塊 | 都做，順序 3.1 → 3.2 → 3.3 |
| 聊天窗誰路由 | 規則先吃；吃不下才問可選模型 |
| 會議發言從哪來 | 預設 ministers 模板填槽；有 API key 才升級真模型 |
| 心鏡真算從哪來 | 外掛本機 `tianji-mcp`（環境變數路徑）。不把引擎複製進 daozhu |
| tianji 是否已上 GitHub | 不擋本規格。開源套件不帶引擎 |

---

## 1. 問題與成功標準

現況：看板靠表單寫記憶；內閣只排出席空位；心鏡只播示範／自貼 JSON。

成功看起來像：

1. `/` 底欄能打「午餐吃了 150」→ 記入支出，列表立刻出現；沒模型也能用。
2. 「組員不做事該怎麼講」規則吃不下且沒 key → 回「聽不懂，請用表單或到內閣頁」。
3. `/cabinet` 按「開會」→ 五階段都有正文；沒 key 是模板；有 `DAOZHU_LLM_*` 才真發言。
4. 會議最後可選「記入決策」→ 走既有 `daily.log_decision`，不改不刪。
5. `/xinjing` 選 tarot 按「真抽」：設了 `DAOZHU_TIANJI_DIR` 就洗 78 牌再播；沒設回 503「未接天機」，示範鈕仍可用。
6. 舊測試全過。缺 POST body 仍 422。500 仍 `{error:internal, message:內部錯誤}`。
7. 看板／內閣頁使用者輸入不當 `innerHTML`。

### 不做

- VS Code 側欄、Tauri／pywebview、遠端、帳密、CORS、WebSocket、串流
- 把 tianji 引擎複製進 daozhu；把 422 改成 400；回填舊筆記 id
- 改已入帳金額、改／刪決策、聊天窗寫入道藏
- 感知條假裝是「本次 Claude 對話」；聊天窗當通用助手
- 同步 `web/` 到 Type_moon；push；開 PR
- 真會議二次質詢 `/追問`、深度／即時共識三檔（第三期只做精簡五階段）
- 心鏡七模式全部真算：第三期真算只做 `tarot`／`gua`／`fengshui`；`chart` 若引擎可 import 則做，失敗當未接；`yuan`／`star`／`dream` 仍示範（敘事層，不算命）

---

## 2. 架構

```
瀏覽器
  POST /api/chat            規則 →（可選）LLM 分類 → daily.*
  POST /api/cabinet/convene  preview + 模板／可選 LLM → 五階段正文
  POST /api/xinjing/cast     外掛 tianji → 轉 xinjing JSON → render()
        │  HTTP，只打 127.0.0.1
        ▼
web/router.py      規則意圖
web/llm.py         可選 OpenAI 相容 chat（沒 key 回 None）
web/speech.py      模板填槽
web/tianji_bridge.py  可選 import 本機 tianji 引擎
web/cabinet.py     既有出席（不改關鍵詞表）
        │
        ▼
mcp/daily.py · skills/daozhu/xinjing/xinjing_render.py
        │
        ▼
local_memory/      與 MCP 同一份
```

規則沿用：不經 MCP stdio、不自行 replace JSON、只認 `DAOZHU_MEMORY_DIR`、綁 `127.0.0.1:8765`、不開 CORS。

---

## 3. 環境變數（不寫記憶庫）

| 變數 | 用途 | 缺省 |
|------|------|------|
| `DAOZHU_LLM_API_KEY` | 可選模型。空＝離線模板／規則 | 空 |
| `DAOZHU_LLM_BASE_URL` | OpenAI 相容 `/v1/chat/completions` | `https://api.openai.com/v1` |
| `DAOZHU_LLM_MODEL` | 模型名 | `gpt-4o-mini` |
| `DAOZHU_TIANJI_DIR` | 本機 tianji-mcp 根目錄（含 `engines/`） | 空＝未接天機 |

測試用 monkeypatch 環境變數與假 client，不打外網、不要求本機真有 tianji。

---

## 4. 3.1 看板聊天窗

### 允許寫入

支出、健康、提醒、採買、情緒、筆記、決策。**不寫**道藏、不改金額、不刪既有列。

查詢類（只讀、不寫）：本月支出摘要、待辦提醒、到期筆記。回文字，不新開 API 契約以外的寫入。

### `POST /api/chat`

body：`{text}`。`text` 空 → 400「內容不能空白」。

回傳：

```json
{
  "ok": true,
  "intent": "expense",
  "source": "rule",
  "reply": "已記入午餐 150（飲食）",
  "result": {}
}
```

| 情況 | ok | intent | HTTP |
|------|----|--------|------|
| 規則命中並寫入成功 | true | 對應名 | 200 |
| 規則／模型都無法分類 | false | `unknown` | 200（業務失敗不 400） |
| 分類到但欄位不夠 | false | 該名 | 200，reply 說明缺什麼 |
| 模型呼叫例外 | 走 500 handler | — | 500 |

`source`：`rule`｜`llm`｜`none`。

### 規則表（先命中先用）

1. **expense**：含金額數字，且含「吃了／花了／付了／買了」或飲食詞（餐／飯／麵／咖啡／飲料／奶茶／便當）。抓第一個數字為 `amount`，項目取數字前的名詞（去掉「吃了」等）。例：「午餐吃了 150」→ item=午餐 amount=150。
2. **mood**：命中 `daily.POSITIVE` 或 `daily.NEGATIVE` 任一子串，且沒抓到金額。全文當 mood。
3. **shopping_add**：以「買」「記得買」「加入採買」開頭，或「採買：X」。
4. **health**：含「睡了／睡眠」＋數字 → sleep_hours；或「運動了 X」→ exercise；或「喝了 X」→ water。
5. **reminder**：含「提醒」且能抓到 ISO 或 `YYYY-MM-DD[ T]HH:MM`。抓不到時間 → unknown 並提示用表單。
6. **note**：以「記 」開頭（全形／半形空格），其後「科目：內容」或「科目 內容」。
7. **decision**：以「裁決」開頭，形如「裁決 題目＝X 決＝Y」或「裁決：題目／裁決」。
8. **query_expense**：「這個月花多少／本月支出」。
9. **query_reminders**：「有什麼待辦／到期提醒」。
10. **query_notes**：「待複習／到期筆記」。

都沒命中：若 `llm.available()`，請模型只回 JSON `{intent, slots}`，intent 白名單同上；否則 `unknown`。

LLM 分類 system 提示固定、temperature 0、回覆必須是 JSON 物件。解析失敗當 unknown。

### 畫面

看板 `<main>` 後加 `#chat` 卡：log（`textContent` 逐行）＋ input＋送出。送出後 `refreshAll()`。不改版面網格其他塊。

---

## 5. 3.2 內閣真會議

既有 `POST /api/cabinet/preview` 不變。

### `POST /api/cabinet/convene`

body：`{topic, persist?}`。topic 空 → 400。

1. `cabinet.preview(topic)` 得出席。
2. 生成五階段 `body`：
   - 無 key：`speech.fill(preview)` 模板。
   - 有 key：對開題／各抒／列席／結辯各打一次 LLM（精簡：核心每人 ≤80 字、列席 ≤60 字、議長結辯 ≤120 字）。失敗則該段回落模板，不整場 500。
3. `persist: true` 時呼叫 `daily.log_decision(topic, "會議已開", 結辯摘要)`。預設 false。

回傳＝preview 形狀＋`source: template|llm|mixed`＋各 stage.body 有字＋disclaimer 改為「模板發言，非正式會議紀錄。」或「模型發言，非正式會議紀錄。」

「您裁決」階段 body 固定：「請在看板決策塊手寫，或把 persist 設為 true 只記『會議已開』。」不替使用者做裁決。

### 模板填槽

讀 `skills/daozhu/ministers/*.md` 與 `patches/*.md` 的「核心心法」第一句＋`classics.md` 對應節第一條經文。正文是固定句式，把 `{topic}` 填進去。不呼叫模型。找不到檔案則用內建短句（測試不依賴缺檔）。

人格檔對照：

| 出席名 | 檔 |
|--------|----|
| 儒家 | ministers/confucian.md |
| 道家 | ministers/daoist.md |
| 法家 | ministers/legalist.md |
| 縱橫家 | ministers/strategist.md |
| 兵家 | patches/military.md |
| 墨家 | patches/mohist.md |
| 佛教 | patches/buddhist.md |

### 畫面

內閣頁按鈕旁加「開會」。五階段卡顯示 `body`（`textContent`）。加「記入『會議已開』」核取方塊，對應 `persist`。

---

## 6. 3.3 心鏡外掛 tianji

既有 examples／render 不變。

### `GET /api/xinjing/status`

```json
{ "tianji": false, "dir": "", "modes": ["tarot", "gua", "fengshui"] }
```

`tianji` true 僅當 `DAOZHU_TIANJI_DIR` 指向的目錄存在且能 `import engines.tarot`。

### `POST /api/xinjing/cast`

body：`{mode, question?, seed?, year?, gender?, dt_local?, lat?, lon?}`。

| mode | 引擎 | 轉成 xinjing |
|------|------|----------------|
| tarot | `engines.tarot.draw(spread="three", seed)` | cards[].phase=position，en=name，desc=meaning＋orientation，tip=orientation；img 空字串（引擎無圖仍可播） |
| gua | `engines.liuyao.cast(question, seed)` | trigram=symbol+name，yao 由下而上，yin=value 偶，mark=動/陰/陽，desc=六親＋地支 |
| fengshui | `engines.fengshui.bazhai_gui(year, gender)` | element 由命卦五行粗對（坎水／離火／震巽木／坤艮土／乾兌金），text=命卦＋吉方＋警語 |
| chart | `engines.western.natal(...)` 若可 import | planets 取日／月／水／金／火／木／土黃經 → deg，ring 1–4；缺 skyfield → 503 |
| 其他 | — | 400「此模式第三期不真算」 |

未接天機：503 `{error: unavailable, message: 未接天機}`。
引擎 raise：400 `{error: invalid, message: 中文原因}`（ValueError）或 500。
回傳 JSON：`{mode, data, disclaimer}`。`disclaimer` 固定「命理僅供參考，非科學預測」。前端拿到後塞 textarea 並可直接 POST render。

不把 tianji 結果寫進 `local_memory/`。

### 畫面

心鏡頁加「真抽／真起」鈕與一行狀態（已接／未接）。hint 改成「示範仍可用；真算需 DAOZHU_TIANJI_DIR」。

---

## 7. 錯誤契約

與第二期相同。另加：

| 情況 | HTTP | error |
|------|------|-------|
| 未接天機 | 503 | `unavailable` |
| 聊天／開會業務失敗（聽不懂、缺欄） | 200 | 無；`ok: false` |
| 缺 POST body | 422 | FastAPI 預設 |

---

## 8. 測試

- 規則：「午餐吃了 150」→ 支出 150；「今天好煩」→ 負向情緒；空白 400。
- 規則吃不下且無 key → 200 `ok:false` intent=unknown。
- 開會無 key → 五階段 body 非空；preview 路由仍空 body。
- persist true → decisions 多一列。
- xinjing status 預設 tianji=false；cast 503。
- 用 tmp 假 `engines/tarot.py` 指 `DAOZHU_TIANJI_DIR` → cast tarot 200 且 data.cards 長度 3。
- 舊 `mcp/tests`＋既有 `web/tests` 全過。
- 三頁仍有 theme-select。

---

## 9. 已否決

- 聊天窗當通用 LLM 對話
- 會議深度三檔、二次質詢
- 把 tianji 推進 daozhu repo
- 真算寫入命主檔／問卜歷史（那是 tianji 自己的 memory）
- 紫夜重回儀表板外殼
