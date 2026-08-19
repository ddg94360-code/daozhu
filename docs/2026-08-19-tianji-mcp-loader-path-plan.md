# Type_moon tianji-mcp Loader 絕對路徑 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Type_moon `.claude/tianji-mcp` 的 skyfield Loader 改為套件絕對路徑，與開源 tianji `9e0100b` 對齊，CWD 不是套件根也能找到 `de440s.bsp`。

**Architecture:** 只改三個 Loader 賦值＋抄一條開源測試。不覆蓋整檔、不改開源 repo、不 commit Type_moon（除非另明示）。

**Tech Stack:** Python、skyfield Loader、pytest

**Spec:** [docs/2026-08-19-tianji-mcp-loader-path-design.md](2026-08-19-tianji-mcp-loader-path-design.md)

## Global Constraints

- 實作目錄：`c:\Galaxy\Type_moon\.claude\tianji-mcp`。
- **禁止**改 `c:\Galaxy\tianji`。HEAD 須保持 `9e0100b`、工作樹乾淨。
- **禁止**改 daozhu `web/`。daozhu 只已有本設計／計畫文。
- 不 push、不開 PR、不裝套件、不下載星曆、不改 submodule、不刪 tianji-mcp。
- 不整理 Type_moon 其它未提交檔（xingming／memory_store／server 等）。
- 先 Read 再補兩行，禁止用開源整檔覆蓋 Type_moon。
- 預設不 `git commit` Type_moon。
- 須使用者已明示「可以改 Type_moon」才執行本計畫（設計已拍板；動手仍要這句）。

---

## File map

| 路徑 | 職責 |
|------|------|
| `.claude/tianji-mcp/lunar.py` | `_REPO`＝本檔目錄；絕對 Loader |
| `.claude/tianji-mcp/engines/western.py` | `_REPO`＝套件根；絕對 Loader |
| `.claude/tianji-mcp/engines/qizheng.py` | 同 western |
| `.claude/tianji-mcp/tests/test_western.py` | 加 `test_ephemeris_loader_is_repo_relative` |
| `c:\Galaxy\tianji\**` | 不改 |

---

### Task 1: 先加會失敗的 Loader 測

**Files:**
- Modify: `c:\Galaxy\Type_moon\.claude\tianji-mcp\tests\test_western.py`

**Interfaces:**
- Consumes: `engines.western._LOADER`、`lunar._LOADER`、`engines.qizheng._LOADER`、`natal`
- Produces: `test_ephemeris_loader_is_repo_relative`

- [ ] **Step 1: Read 現況，不要覆蓋**

Read：

- `c:\Galaxy\Type_moon\.claude\tianji-mcp\tests\test_western.py`（前 20 行）
- `c:\Galaxy\tianji\tests\test_western.py` 的 `test_ephemeris_loader_is_repo_relative`（約 L10–24）

確認 Type_moon 該檔目前 `from engines.western import natal, transit, planet_positions, _house_of` **沒有** `_LOADER`。

- [ ] **Step 2: 寫失敗測試**

改 import：

```python
from engines.western import natal, transit, planet_positions, _house_of, _LOADER
```

在 `_natal` **之前**插入（與開源相同，勿改斷言）：

```python
def test_ephemeris_loader_is_repo_relative(tmp_path, monkeypatch):
    """Loader 必須指到套件內 data/ephemeris，不能跟 CWD，否則從 daozhu 起儀表板會誤下載。"""
    import os
    import engines.qizheng as qizheng
    import engines.western as western
    import lunar
    monkeypatch.chdir(tmp_path)
    repo = os.path.dirname(os.path.dirname(os.path.abspath(western.__file__)))
    expected = os.path.join(repo, "data", "ephemeris")
    for loader in (_LOADER, lunar._LOADER, qizheng._LOADER):
        assert os.path.isabs(loader.directory)
        assert os.path.abspath(loader.directory) == os.path.abspath(expected)
    assert os.path.isfile(os.path.join(expected, "de440s.bsp"))
    natal(datetime(2000, 1, 1, 8, 0), 8.0, 40.0, 120.0)
    assert not (tmp_path / "data").exists()
```

不要改錨點測 `test_ascendant_mc` 等。

- [ ] **Step 3: 跑新測，確認紅在相對路徑**

```bash
cd /c/Galaxy/Type_moon/.claude/tianji-mcp
python -m pytest tests/test_western.py::test_ephemeris_loader_is_repo_relative -q
```

Expected: FAIL。`loader.directory` 非絕對，或 `chdir` 後路徑不等於套件 `data/ephemeris`。若 `de440s.bsp` 本身不存在，**停下來報告**，不要下載。

---

### Task 2: 三檔 Loader 改絕對路徑

**Files:**
- Modify: `c:\Galaxy\Type_moon\.claude\tianji-mcp\lunar.py`
- Modify: `c:\Galaxy\Type_moon\.claude\tianji-mcp\engines\western.py`
- Modify: `c:\Galaxy\Type_moon\.claude\tianji-mcp\engines\qizheng.py`

**Interfaces:**
- Consumes: 開源同名檔的 `_REPO`／`_LOADER` 寫法
- Produces: 三個 `_LOADER.directory` 皆為套件根下 `data/ephemeris` 的絕對路徑

- [ ] **Step 1: Read 三檔 Loader 附近 20 行，確認仍是相對路徑且無其它你要保留的本地改動卡在同一行**

- [ ] **Step 2: `lunar.py`**

在檔首 import 區補 `import os`（放在 `from datetime` 之前或之後皆可，與開源一致即可）：

```python
import os
from datetime import datetime, timedelta
```

把

```python
_LOADER = Loader("data/ephemeris")
```

換成

```python
_REPO = os.path.dirname(os.path.abspath(__file__))
_LOADER = Loader(os.path.join(_REPO, "data", "ephemeris"))
```

不要動 `ZHONGQI_MONTH`、`_eph`、`solar_to_lunar`。

- [ ] **Step 3: `engines/western.py`**

`import math` 旁已有或補 `import os`。把

```python
_LOADER = Loader("data/ephemeris")
```

換成

```python
_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOADER = Loader(os.path.join(_REPO, "data", "ephemeris"))
```

不要動 `PLANETS`／`natal`。

- [ ] **Step 4: `engines/qizheng.py`**

補 `import os`。`_REPO`／`_LOADER` 與 western **同一寫法**（再上一層到套件根）。不要動七政計算。

- [ ] **Step 5: 再跑新測**

```bash
cd /c/Galaxy/Type_moon/.claude/tianji-mcp
python -m pytest tests/test_western.py::test_ephemeris_loader_is_repo_relative -q
```

Expected: PASS。

- [ ] **Step 6: 全套 tianji-mcp 測試**

```bash
cd /c/Galaxy/Type_moon/.claude/tianji-mcp
python -m pytest tests/ -q
```

Expected: 全綠。若無關的既有未提交改動讓別條本來就紅，記錄下來，**不要順手修**。

- [ ] **Step 7: 確認開源 tianji 沒被碰**

```bash
cd /c/Galaxy/tianji && git status --short && git rev-parse --short HEAD
```

Expected: 空 status、`9e0100b`。

- [ ] **Step 8: 自審 Type_moon diff 範圍**

```bash
cd /c/Galaxy/Type_moon
git diff -- .claude/tianji-mcp/lunar.py .claude/tianji-mcp/engines/western.py .claude/tianji-mcp/engines/qizheng.py .claude/tianji-mcp/tests/test_western.py
```

只應看到 Loader／`import os`／一條新測。不要 commit、不要 push。
