# 道樞記憶儀表板（第四期）設計

日期：2026-08-18
狀態：本夜已落地，daozhu 未 commit；tianji 新 repo 已 initial commit、無 remote
範圍：開源套件 `c:\Galaxy\daozhu` 的儀表板加深＋本機包裝；tianji 獨立抽套件到 `c:\Galaxy\tianji`。Type_moon 實例不改、不同步、不 push、不開 PR。第三期未 commit 的檔案一併保留。

第三期是聊天窗＋模板會議＋外掛 tarot／gua／fengshui。第四期五塊一起做，但契約彼此獨立：壞一塊不能拖垮另外四塊。

---

## 0. 已拍板

| 題 | 決定 |
|----|------|
| 五塊都做還是先一塊 | 都做。優先序 C1 → C2 → C5 → C4 → C3 |
| 聊天窗當通用助手 | **不做**。規則＋可選分類仍是第三期契約 |
| 把 tianji 引擎複製進 daozhu | **不做**。C3 抽獨立 repo，儀表板仍只認 `DAOZHU_TIANJI_DIR` |
| 敘事層 yuan／star／dream | 仍示範，不算命 |
| Type_moon 實例 | 不改。tianji 開源是**複製**到 `c:\Galaxy\tianji`，不是搬空 Type_moon |
| commit／push／PR | 本夜可寫檔、可測；**不 commit、不 push、不開 PR**（與第三期同一條） |
| 裝套件 | 不新裝 npm／pip 到使用者環境。C4／C5 用 stdlib 或已有 fastapi |

---

## 1. 問題與成功標準

明早打開能驗：

1. `/cabinet` 可選深度三檔（精簡預設／深度／即時共識）；開會後可對某一內閣「追問」，回一張補充卡，不改五階段原文。
2. `/xinjing` 真抽清單含 `tarot`／`gua`／`fengshui`／`chart`／`bazi`／`ziwei`／`meihua`。yuan／star／dream 仍 400「此模式不算命」。chart 缺 skyfield → 503「未接天機」。
3. `python -m web.desktop` 起同一套 FastAPI，印出網址；無瀏覽器自動化、無新視窗函式庫。
4. `extension/` 是一份可 `code --install-extension` 的 VS Code 套件骨架：側欄 webview 載 `http://127.0.0.1:8765`；伺服器沒開時顯示中文提示＋重試。不發佈市集。
5. `c:\Galaxy\tianji` 是獨立 git repo（尚未 remote），含引擎＋測試＋README，**不含** Type_moon 的 skill 詮釋層與命主記憶。daozhu 不引用這個路徑寫死。

舊測試全過。缺 POST body 仍 422。500 仍 `{error:internal, message:內部錯誤}`。看板／內閣使用者輸入不當 `innerHTML`。

### 不做

- 聊天窗當通用 LLM
- 把 tianji 推進 daozhu repo
- 真算寫入命主檔／問卜歷史
- 紫夜重回儀表板外殼
- 同步 `web/` 到 Type_moon
- push、開 PR、改 Type_moon
- 裝 Tauri／pywebview／electron
- 改 422→400、回填舊筆記 id、改已入帳金額

---

## 2. 架構

```
瀏覽器 / VS Code webview / python -m web.desktop
        │  HTTP 127.0.0.1:8765
        ▼
web/app.py
  POST /api/cabinet/convene   + depth
  POST /api/cabinet/followup  二次質詢
  POST /api/xinjing/cast      + bazi/ziwei/meihua
        │
web/speech.py     依 depth 縮放模板字數
web/tianji_bridge.py  七個計算模式
        │
mcp/daily.py · 本機 DAOZHU_TIANJI_DIR
```

C3 平行存在於 `c:\Galaxy\tianji`，與儀表板零 import。

---

## 3. C1 內閣加深

既有 `POST /api/cabinet/preview` 不變（仍空 body）。

### `POST /api/cabinet/convene`

body：`{topic, persist?, depth?}`。

| depth | 預設 | 模板行為 |
|-------|------|----------|
| `brief` | 是 | 與第三期相同（核心 ≤80、列席 ≤60、結辯 ≤120） |
| `deep` | | 核心每人兩句、列席一句加「可再質詢」、結辯含共識／分歧／建議三段 |
| `flash` | | 不走五張卡填滿：開題一句＋各抒合併成一段 ≤150 字＋您裁決固定句；列席／結辯寫「（即時共識已併入各抒）」 |

非法 depth → 400「深度須為 brief／deep／flash」。缺欄當 `brief`。

有 LLM key 時仍對開題／各抒／列席／結辯各打一次（flash 只打各抒一次），失敗回落對應深度的模板。`source` 仍 `template|llm|mixed`。

回傳加 `depth`。preview 路由不加 depth。

### `POST /api/cabinet/followup`

body：`{topic, name, question}`。任一空 → 400。

`name` 必須是四子或三補丁之一（儒家／道家／法家／縱橫家／兵家／墨家／佛教）。否則 400「查無此內閣」。

無 key：`speech.followup(name, topic, question)` 模板一句。
有 key：打一次 LLM（≤80 字），失敗回落模板。

回傳：

```json
{
  "name": "儒家",
  "topic": "…",
  "question": "…",
  "body": "…",
  "source": "template",
  "disclaimer": "模板追問，非正式會議紀錄。"
}
```

不寫記憶、不改五階段。畫面：開會區加 depth `<select>`；五階段下加追問表（內閣名＋問題＋按鈕），結果用 `textContent` 另開一卡。

---

## 4. C2 心鏡真算補完

### `GET /api/xinjing/status`

```json
{
  "tianji": false,
  "dir": "",
  "modes": ["tarot", "gua", "fengshui", "chart", "bazi", "ziwei", "meihua"],
  "narrative": ["yuan", "star", "dream"]
}
```

`tianji` true 條件不變：目錄在且能 `import engines.tarot`。

### `POST /api/xinjing/cast`

| mode | 引擎 | 轉成 xinjing |
|------|------|----------------|
| tarot／gua／fengshui | 第三期 | 不變 |
| chart | `engines.western.natal` | 既有；缺 skyfield／缺 dt_local 分別 503／400 |
| bazi | `engines.bazi.paipan(BirthInput)` | 走 **gua** 殼：trigram=日柱干支，name=四柱一行，mean=格局＋用神，yao=年／月／日／時／大運首步／警語 |
| ziwei | `engines.ziwei.paipan(y,m,d,h)` | 走 **gua** 殼：trigram=命宮，name=五行局，mean=紫微在＋四化摘要，yao=命／身／官祿／財帛／夫妻／福德 |
| meihua | `engines.meihua.cast(method=number, numbers)` | 走 **gua** 殼：trigram=主卦，name=主卦名，mean=體用關係，yao=上／下／互／變／動爻／警語 |
| yuan／star／dream | — | 400「此模式不算命」 |
| 其他 | — | 400「此模式不算命」 |

bazi／ziwei 缺 `dt_local` → 400「須提供 dt_local」。meihua 缺 numbers 時用問題字數或 `[3, 8]` 保底（文件寫明）。不寫 `local_memory/`。警語固定「命理僅供參考，非科學預測」。

前端：真抽時 chart／bazi／ziwei 若 textarea 不像 JSON，把整段當 `dt_local`（ISO）；meihua 從 textarea 抓兩個整數，抓不到用 `[3,8]`。成功後仍塞 textarea 並 render。bazi／ziwei／meihua 的 render mode 用 `gua`（引擎七模式未加新殼，不改 xinjing_engine.html）。

---

## 5. C5 桌面殼（薄）

不裝 Tauri／pywebview。新增 `web/desktop.py`：

```
python -m web.desktop
```

行為＝`python -m web`，但啟動 log 多一行「桌面殼：請用系統瀏覽器打開 http://127.0.0.1:8765 （第四期不內嵌視窗）」。`web/__main__.py` 不改預設。

若本機已有 `webbrowser`（stdlib），嘗試 `webbrowser.open` 打 127.0.0.1（不是 localhost）。失敗忽略。

測試：import `web.desktop` 有 `main`；不真開 browser（monkeypatch）。

---

## 6. C4 VS Code 側欄

路徑：`c:\Galaxy\daozhu\extension/`

最小可用骨架，不發佈：

- `package.json`：publisher `daozhu`、name `daozhu-dashboard`、engines vscode `^1.85.0`、activation `onView:daozhu.sidebar`、貢獻一個 activitybar view
- `extension.js` CommonJS：WebviewViewProvider，html 為 iframe `http://127.0.0.1:8765`；`retainContextWhenHidden: true`
- 連不上時（webview 內 onerror 或提示條）顯示「儀表板未開。在套件根目錄執行 python -m web」＋「重試」鈕（重設 iframe src）
- README 繁中：如何 `code --install-extension daozhu-dashboard-0.4.0.vsix` 或從資料夾「安裝本機套件」
- `.vscodeignore` 排除測試與記憶庫

不呼叫 `vsce package`（不裝 vsce）。不把 iframe 指到 Type_moon。CSP 允許 `frame-src http://127.0.0.1:8765`。

測試（daozhu pytest）：讀 `extension/package.json` 含 view id、讀 `extension.js` 含 `127.0.0.1:8765` 且不含 `localhost`。

---

## 7. C3 tianji 開源抽套件

目的：讓別人能 `DAOZHU_TIANJI_DIR=/path/to/tianji` 接真算，不必進 Type_moon。

做法：

1. 建立 `c:\Galaxy\tianji`（獨立 git repo，預設 branch `main`）。
2. 複製 Type_moon `.claude/tianji-mcp/` 的**引擎層**：`astro.py` `calendar_base.py` `lunar.py` `solar_terms.py` `timezone.py` `memory_store.py` `server.py` `engines/` `data/`（含 ephemeris）`tests/` `overrides/` `LICENSE` `ORACLE.md` `requirements.txt` `README.md`。
3. **不複製** Type_moon `.claude/skills/tianji/`（詮釋層仍留在實例）。
4. 根目錄加 `.gitignore`（`__pycache__`、`.pytest_cache`、使用者 memory）。
5. README 頂加「這是事實層 MCP。儀表板用 `DAOZHU_TIANJI_DIR` 指到本目錄。命理僅供參考，非科學預測。」
6. `git init`＋initial commit **只在 tianji 新 repo**（這不是 daozhu 的 commit，也不 push）。
7. 不設 remote、不改 Type_moon 裡的檔。

驗收：`cd /c/Galaxy/tianji && python -m pytest tests/ -q` 至少引擎單測能跑（缺 skyfield 的 western 測試允許 skip／既有行為）。daozhu 測試不依賴這個目錄存在。

---

## 8. 錯誤契約

與第三期相同。另加：

| 情況 | HTTP | error |
|------|------|-------|
| 非法 depth | 400 | `invalid` |
| 追問查無此內閣 | 400 | `invalid` |
| yuan／star／dream／未知 mode | 400 | `invalid`，message「此模式不算命」 |

第三期「此模式第三期不真算」改成「此模式不算命」（契約微調；舊測試 `dream` 只斷 400，不斷文案）。

---

## 9. 測試

- convene `depth=flash` → 各抒有字且總長合理；列席／結辯為佔位句
- convene 非法 depth → 400
- followup 儒家＋問題 → 200 body 非空；空名 400
- preview 仍空 body
- status.modes 含 bazi／ziwei／meihua；narrative 含 dream
- cast dream → 400 此模式不算命
- tmp 假 engines 可 cast bazi（假 paipan）→ 200 且 data 有 trigram
- extension/package.json 有 `daozhu.sidebar`
- desktop 模組可 import
- 舊 `mcp/tests`＋`web/tests` 全過

---

## 10. 已否決

- 通用助手聊天
- tianji 引擎進 daozhu
- Tauri／pywebview
- 發佈 VS Code 市集
- 把 Type_moon 的 tianji 刪掉或改成 submodule
- push 任一 repo
