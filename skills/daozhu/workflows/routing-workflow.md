# 技能路由表（納管現有 skills）

道樞感知網絡判定為**任務類**請求時，依下表路由到對應技能。被路由的技能即為道樞之技能模塊——由道樞交付，不改變其內部流程。

**原則**：永遠不要同時載入所有 skills。每回合只載入「當前任務相關」的 skills。

## 領域偵測 → Skills 映射表

| 觸發關鍵詞 | 路由到 | 詳細流程 |
|-----------|--------|---------|
| 寫/章節/角色/劇情/大綱/潤色/同人/Fate/Beat/審查/清理/交接 | novel-writing, novel-writer-voice | `../skill-router/workflows/writing-workflow.md` |
| Godot/SCP/FPS/遊戲/GDScript/3D/物理/動畫 | godot-gdscript, godot-3d-essentials, godot-physics, fps-shooter, game-ai, prototype-fast | `../skill-router/workflows/gamedev-workflow.md` |
| 網站/Astro/React/Tailwind/CSS/前端 | frontend-design, superpowers:brainstorming, superpowers:writing-plans | `../skill-router/workflows/website-workflow.md` |
| Bug/錯誤/修復/除錯/不工作 | superpowers:systematic-debugging | `../skill-router/workflows/crosscutting-workflow.md` |
| 圖片/截圖/照片/看/分析圖片 | gemini-vision | `../skill-router/workflows/crosscutting-workflow.md` |
| 生成立繪/角色圖/插圖/ComfyUI/立繪 | ComfyUI MCP（不需額外 skill） | `../skill-router/workflows/crosscutting-workflow.md` |
| 音樂/歌/播放/推薦/歌品 | music-master | `../skill-router/workflows/crosscutting-workflow.md` |
| 老師/教我/練習題/ICT/DSE/補習/學科/未來規劃/迷茫/大學 | life-tutor, teacher-persona | — |
| 分析數據/拆書/蒸餾/把XX做成skill | cangjie-skill, skill-builder | — |
| 記住這個/這招好用/以後都這樣/寫成skill | skill-builder | — |
| 成人/情趣/純慾/叫聲/擬聲詞 | ai-unlock | — |
| 賺錢/副業/市場/商業 | 直接分析，不需額外 skill | — |
| 檢查設定/漏洞/安全/審計 | 直接檢查，不需額外 skill | — |

## 預設在線（每次對話皆可用）
- `daozhu`（本 skill）
- `superpowers:using-superpowers`
- Memory MCP、Filesystem MCP

## 明確不自動載入的
- 66 個非 Godot gamedev skills（Unity/Unreal/Phaser/PixiJS/ThreeJS/Bevy/LÖVE/Pygame/Roblox/Card-game/Platformer/Puzzle/Roguelike/RPG/Survival-crafting/Tower-defense/Visual-novel 等）
- novel-reader / novel-research / novel-wiki（僅用戶明確要求）
- bazi-pan-skill（僅用戶要求）
- colleague-skill / proactive-agent / self-improving-agent（實驗性）

## 跨領域衝突判斷
同時命中多領域（如 gamedev 與立繪）時，以動作性最強的關鍵詞決定路由。細節見 `../skill-router/workflows/crosscutting-workflow.md` 之「跨領域衝突判斷」一節。

## 操作方式
1. 偵測任務類請求領域
2. 只載入映射表中對應 skills；若該領域有「詳細流程」欄位，額外讀取該 workflow 檔案
3. 其他 skills 的 SKILL.md 與其他 workflow 檔案不要讀取
4. 若領域改變，才切換載入的 skills/workflow
