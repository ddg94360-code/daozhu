# 後續 C：Type_moon tianji-mcp 同步絕對路徑 Loader

日期：2026-08-19
狀態：設計已拍板，未實作
範圍：**只改** `c:\Galaxy\Type_moon\.claude\tianji-mcp` 三個 Loader。不改 `c:\Galaxy\tianji`（已上線）、不改 daozhu、不整庫同步、不改 submodule、不刪 tianji-mcp、不 push、預設**不 commit Type_moon**。

與 A（風水年）、B（會議暫存）獨立。實作必須另一次明示「可以改 Type_moon」。

開源 tianji `9e0100b` 已修：skyfield `Loader` 用套件絕對路徑。Type_moon 實例仍 `Loader("data/ephemeris")`，CWD 不是套件根就找不到 `de440s.bsp`（儀表板 `DAOZHU_TIANJI_DIR` 指這份時，chart／qizheng／fusion／農曆會失敗或誤往 CWD 下載）。

---

## 0. 已拍板

| 題 | 決定 |
|----|------|
| 改哪個庫 | **只** Type_moon `.claude/tianji-mcp` |
| 開源 tianji | **不動** |
| 對齊方式 | 抄 `9e0100b` 同一寫法，不重寫引擎 |
| 其它 Type_moon 未提交改動 | **不**順手清、不混進無關檔 |
| commit Type_moon | 本設計**不**要求 commit |
| 把 tianji-mcp 改成 submodule／刪掉 | **不做** |
| 同步 daozhu `web/` | **不做** |

---

## 1. 問題與成功標準

Type_moon 仍相對 CWD：

| 檔 | 現況 | 應對齊（開源） |
|----|------|----------------|
| `lunar.py` | `Loader("data/ephemeris")` | `_REPO = dirname(abspath(__file__))`（此檔在套件根），`Loader(join(_REPO, "data", "ephemeris"))` |
| `engines/western.py` | 同上 | `_REPO = dirname(dirname(abspath(__file__)))`，同上 join |
| `engines/qizheng.py` | 同上 | 與 western 相同 `_REPO` |

成功看起來像：

1. 三檔 `_LOADER.directory` 為絕對路徑，且等於套件根下 `data/ephemeris`。
2. 從空白暫存目錄 `chdir` 後呼叫 `natal(...)` **不會**在 CWD 建 `data/`，且套件內 `de440s.bsp` 仍在。
3. Type_moon 既有 `tianji-mcp/tests` 全過。
4. `c:\Galaxy\tianji` 工作樹仍乾淨、HEAD 仍 `9e0100b`。
5. daozhu 工作樹不因 C 出現程式改動（設計檔可已在 daozhu `docs/`）。

### 不做

- 改 `server.py` 其它邏輯、姓名學、記憶層
- 把 Type_moon 未提交的 xingming／memory_store 等一併「整理」
- 從開源 repo 整包覆蓋 Type_moon
- push 任一 remote

---

## 2. 做法

逐檔對照開源同名檔的 Loader 區塊，只補 `import os`（若缺）與 `_REPO`／`_LOADER` 兩行。不改行星表、不改 `_eph()` 快取語意。

`lunar.py` 的 `_REPO` 是**本檔所在目錄**（套件根）。`engines/*` 的 `_REPO` 是**再上一層**。

測試：Type_moon [`tests/test_western.py`](.claude/tianji-mcp/tests/test_western.py) **尚無**開源那條 `test_ephemeris_loader_is_repo_relative`。把開源 [`tianji/tests/test_western.py`](../../tianji/tests/test_western.py) 該測抄過來（可 `chdir` 到 `tmp_path`、assert 三個 `_LOADER`、assert `de440s.bsp`、跑一次 `natal`、assert CWD 下無 `data/`）。不要抄無關錨點測的改寫。

若 Type_moon 該檔 import 路徑與開源不同，以 Type_moon 現有 conftest／sys.path 為準，只加測、不改收集方式。

---

## 3. 驗收指令

```bash
cd /c/Galaxy/Type_moon/.claude/tianji-mcp
python -m pytest tests/test_western.py::test_ephemeris_loader_is_repo_relative tests/ -q
```

（全檔 `tests/` 為準；先跑新測再全套。）

另確認：

```bash
cd /c/Galaxy/tianji && git status --short && git rev-parse --short HEAD
```

須空、且 `9e0100b`。

---

## 4. 風險

| 風險 | 處理 |
|------|------|
| Type_moon tianji-mcp 已有大量未提交 | 只動三個 Loader＋一條測試；diff 用 `git diff -- lunar.py engines/western.py engines/qizheng.py tests/test_western.py` 自審 |
| 與未提交的 western／lunar 其它改動衝突 | 先 Read 再補 Loader，不要整檔覆蓋成開源版 |
| MCP 行程已 import 舊模組 | 改完需重載 MCP／重開 Claude；設計不自動重啟 |
| 無 de440s.bsp | 測會失敗；不在 C 範圍下載星曆。檔應已在 `data/ephemeris/` |

---

## 5. 檔案

- 改：`c:\Galaxy\Type_moon\.claude\tianji-mcp\lunar.py`
- 改：`c:\Galaxy\Type_moon\.claude\tianji-mcp\engines\western.py`
- 改：`c:\Galaxy\Type_moon\.claude\tianji-mcp\engines\qizheng.py`
- 改：`c:\Galaxy\Type_moon\.claude\tianji-mcp\tests\test_western.py`（加一條）
- 不改：`c:\Galaxy\tianji\**`、`c:\Galaxy\daozhu\web\**`

本設計文放在 daozhu `docs/`，方便與 A／B 並列；**實作入口是 Type_moon**。
