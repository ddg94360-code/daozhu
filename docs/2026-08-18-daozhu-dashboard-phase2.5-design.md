# 道樞記憶儀表板（2.5 期）設計

日期：2026-08-18
狀態：已實作
範圍：開源套件 `c:\Galaxy\daozhu`。Type_moon 實例不改、不同步、不 push、不開 PR。

第二期是三頁記憶看板。2.5 期只換外殼色票：四學說＋太極可切，預設道家，紫夜不列在儀表板清單。沒有聊天、沒有真會議、不接 tianji。

---

## 1. 問題與成功標準

三頁共用寫死紫夜（`#1a1438`／`#9b8cff`）。學說切換、太極、黑白都做不到。Canva 參考圖只當對色，不重排版面。

成功看起來像：

1. 第一次打開是道家青綠，不是紫夜。
2. 頂欄 `<select>` 可切：道家／儒家／法家／縱橫／太極。
3. 重整、換 `/cabinet`／`/xinjing` 後仍是上次的選擇（`localStorage['daozhu.theme']`）。
4. 太極顯示慢轉陰陽魚（90s 一圈、`pointer-events:none`）；其他主題不顯示。
5. 看板表單與 API 契約不變。舊測試全過。
6. 心鏡 iframe 內動畫仍用引擎自己的模式色（含塔羅紫夜）。外殼跟手選主題。

### 不做

- 聊天窗、真會議文字、真抽牌／真排盤、VS Code 側欄、桌面殼
- 主題寫進 `local_memory/`、新 HTTP API、生圖 API
- 同步 `web/` 到 Type_moon；改 422／500
- 看板翻牌／進場特效；使用者輸入當 `innerHTML`

---

## 2. 做法

純前端 token。`app.css` 用 CSS 變數；`html[data-theme]` 五套；三頁引 `theme.js`。非法或沒存 → `daoist`。

| key | 名 | 背景／卡片／標題／正文／強調 |
|-----|----|------------------------------|
| `daoist` | 道家 | `#0a120e`→`#1a2a24`／`#121c18`／`#8fbfa8`／`#d8e4dc`／`#8fbfa8` |
| `confucian` | 儒家 | `#1a140e`→`#2a2218`（暗紙）／`#241c14`／`#a33b3b`／`#e8dcc0`／`#c4a574` |
| `legalist` | 法家 | `#0a0a0c`／`#1a1a1e`／`#e8e8ea`／`#c8c8cc`／`#c23b3b`；圓角 8 |
| `strategist` | 縱橫 | `#0c0a08`／`#1c1812`／`#d4b56a`／`#e4d8b8`／`#d4b56a` |
| `taiji` | 太極 | `#0a0a0a`／`#141414`／`#f2f2f2`／`#e6e6e6`／`#f2f2f2`；無彩色警告 |

儒家用暗紙而非淺宣紙，避免和現有深色看板打架。

---

## 3. 檔案

| 路徑 | 職責 |
|------|------|
| `web/static/app.css` | `var(--*)`＋五套 `[data-theme]`＋太極魚 |
| `web/static/theme.js` | 讀寫 localStorage、設 `data-theme` |
| `web/static/index.html`／`cabinet.html`／`xinjing.html` | select＋theme.js＋SVG 魚 |
| `web/tests/test_api.py` | 三頁含 select／五 key；CSS／JS 契約 |
| README／CHANGELOG | 一行說明 |

---

## 4. 驗收

```
cd /c/Galaxy/daozhu
python -m pytest mcp/tests/ web/tests/ -q
```

瀏覽器：`http://127.0.0.1:8765` 預設道家；切法家變鐵灰＋紅；重整仍在；太極看得到慢轉魚。
