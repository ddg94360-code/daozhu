# 萬象心鏡動畫引擎（xinjing）

把萬象心鏡的七個玄學模式做成**視覺化動畫**——抽牌、成卦、字卡、行星運行，取代純文字輸出。
由 AI 觸發 `/卦` `/塔羅` `/緣` 等時，自動生成一頁動畫並開啟。

## 檔案

```
xinjing/
├── xinjing_engine.html    # 自包含動畫引擎（七模式 CSS/JS，單檔無依賴）
├── xinjing_render.py      # 生成器：模式 + 資料 → 動畫 HTML
└── examples/              # 七模式各一份示例資料（JSON）
```

## 用法

```bash
python xinjing_render.py <模式> <資料.json> [-o 輸出.html]

模式：tarot | gua | yuan | chart | fengshui | star | dream
```

範例：
```bash
python xinjing_render.py tarot examples/tarot.json -o /tmp/ta.html
python xinjing_render.py gua   examples/gua.json   -o /tmp/gua.html
```

生成後用瀏覽器開啟輸出檔即見動畫。

## 七模式資料結構

各模式的 JSON 欄位（僅列出必填；所有欄位含中文，`ensure_ascii=False`）：

**tarot**（翻牌，`img` 可用網路 URL 或本地路徑）
```json
{ "source": "標語",
  "cards": [ { "phase": "過 去", "img": "…/RWS_Tarot_00_Fool.jpg", "en": "The Fool",
               "desc": "描述", "tip": "提醒" } ],
  "delays": [400, 1500, 2700], "verdict": "牌意總結" }
```

**gua**（六爻逐爻生成）
```json
{ "source": "標語", "trigram": "䷆ 上坤下坎", "name": "師 卦", "mean": "卦義",
  "yao": [ { "label": "初 六", "yin": true, "mark": "陰", "desc": "爻辭" } ] }
```

**yuan**（星空字卡淡入）
```json
{ "source": "出處", "text": "一句宇宙短訊" }
```

**chart**（行星軌道；`deg` 為角度 0-360，`ring` 1-4 軌道圈）
```json
{ "source": "標語",
  "planets": [ { "name": "太陽", "sym": "☉", "ring": 2, "deg": 30,
                 "color": "#ffd9a0", "hl": true, "meaning": "核心自我" } ],
  "summary": "星象總語" }
```

**fengshui**（五行氣流）
```json
{ "source": "標語", "element": "水", "glow": "#6a9bff", "text": "空間與心之映照" }
```

**star**（十二原型圖騰；`all` 為 12 個原型，`active` 為高亮索引）
```json
{ "source": "標語",
  "all": [ { "sym": "🌟", "name": "夢者" } ], "active": 11,
  "sym": "🌟", "name": "夢 者", "desc": "原型映照" }
```

**dream**（夢境漸層碎片）
```json
{ "source": "標語", "mood": "夢境餘溫", "note": "夢境註腳",
  "images": [ { "sym": "🚪", "color": "#8fc4d8" } ] }
```

## AI 使用流程（道樞觸發時）

1. 感知用戶觸發 `/卦` `/塔羅` `/緣` `/星盤` `/風水` `/星` `/夢`
2. 依該模式生成內容（卦象／牌面／行星／短訊…）
3. 寫成資料 JSON，呼叫：
   ```bash
   python skills/daozhu/xinjing/xinjing_render.py <模式> <資料.json> -o <輸出>.html
   ```
4. 開啟輸出檔（Windows：`cmd //c start "" "<路徑>"`；macOS：`open`；Linux：`xdg-open`）
5. 同時以文字附上簡短解讀（動畫負責儀式感，文字負責智慧）

## 注意

- 引擎是單檔無依賴，離線可用；塔羅 `img` 若用網路 URL 需連網，可改用本地牌圖。
- 圖片建議用公有領域來源（如 Wikimedia Commons 的 Rider-Waite 塔羅牌，版權已過期）。
- 生成器只嵌入資料，不修改引擎——更新引擎後重新生成即可。
