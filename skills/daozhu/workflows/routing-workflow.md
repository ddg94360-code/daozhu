# 技能路由表（範例）

道樞感知到**任務類**請求時，依本路由表把請求交給對應技能。被路由的技能即為道樞之技能模塊——由道樞感知後交付，不改變其內部流程。

> ⚠️ **下表是範例**，路由到的是作者個人專案的 skills（novel-writing、godot-* 等）。安裝後請依你專案**實際安裝的 skills** 修改「路由到」欄位。沒有對應技能時，道樞退回內閣回應。

**原則**：永遠不要同時載入所有 skills。每回合只載入「當前任務相關」的 skills。

## 領域偵測 → Skills 映射表（範例）

| 觸發關鍵詞（可改） | 路由到（改成你的 skills） |
|-----------|--------|
| 寫/章節/角色/劇情/大綱/潤色/審查/清理 | （你的寫作 skill，如 novel-writing） |
| Godot/遊戲/GDScript/3D/物理/動畫 | （你的遊戲開發 skills，如 godot-*） |
| 網站/Astro/React/Tailwind/CSS/前端 | （你的前端 skill，如 frontend-design） |
| Bug/錯誤/修復/除錯/不工作 | `superpowers:systematic-debugging` |
| 圖片/截圖/照片/看/分析圖片 | （你的視覺 skill 或 Vision MCP） |
| 生成立繪/角色圖/插圖 | （你的圖片生成 MCP，如 ComfyUI） |
| 音樂/歌/播放/推薦 | （你的音樂 skill） |
| 老師/教我/練習題/學科/未來規劃 | （你的教學 skill，如 life-tutor） |
| 拆書/蒸餾/把XX做成skill | `cangjie-skill`, `skill-builder` |
| 記住這個/這招好用/寫成skill | `skill-builder` |
| 成人/情趣/純慾/擬聲詞 | `ai-unlock`（若安裝） |
| 賺錢/副業/市場/商業 | 直接分析，不需額外 skill |
| 檢查設定/漏洞/安全/審計 | 直接檢查，不需額外 skill |

## 預設在線（每次對話皆可用）
- `daozhu`（本 skill）
- `superpowers:using-superpowers`
- 你的 Memory MCP、Filesystem MCP

## 跨領域衝突判斷

同時命中多領域（如 gamedev 與立繪）時，以「動作性最強」的關鍵詞決定路由：

1. **具體動作詞優先**：「寫/做/修/畫/除錯」> 抽象領域詞（遊戲/網站/音樂）
2. **有明確產物優先用產物**：提到章節→寫作、頁面→網站、圖→圖片
3. 仍無法判斷時，簡短問使用者要哪個

## 操作方式

1. 偵測任務類請求領域
2. 只載入映射表中對應 skills
3. 其他 skills 的 SKILL.md 與其他 workflow 檔案不要讀取
4. 若領域改變，才切換載入的 skills/workflow
