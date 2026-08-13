"""道樞記憶層底層：JSON 記憶庫讀寫（原子寫入，防損壞）。

集合概念：name = 記憶庫名，subdir = 記憶庫所在子目錄（預設 daily/）。
支援多子目錄（daily / daozang...），全體共用同一套讀寫與損壞處理。
"""
import json
import os
from datetime import datetime


# 記憶庫根目錄。惰性讀取，測試可用 DAOZHU_MEMORY_DIR 覆蓋。
def base_dir() -> str:
    return os.environ.get(
        "DAOZHU_MEMORY_DIR",
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "local_memory"),
    )


def now() -> str:
    """統一 ISO 時間戳（秒精度），全模組共用單一時鐘。"""
    return datetime.now().isoformat(timespec="seconds")


def _dir(subdir: str) -> str:
    return os.path.join(base_dir(), subdir)


def _ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)


def _file_path(name: str, subdir: str) -> str:
    _ensure_dir(_dir(subdir))
    return os.path.join(_dir(subdir), f"{name}.json")


def _read_all(name: str, subdir: str) -> list:
    path = _file_path(name, subdir)
    if not os.path.exists(path):
        return []
    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        if isinstance(data, list):
            return data
        return []
    except (json.JSONDecodeError, OSError):
        # 檔案損壞時保留原檔（改名備份），回傳空 list 避免整個記憶層崩潰
        backup = path + ".corrupt"
        try:
            os.replace(path, backup)
        except OSError:
            pass
        return []


def _write_all(name: str, records: list, subdir: str) -> None:
    """原子寫入：先寫 tmp 檔再 replace，避免寫一半崩壞。"""
    path = _file_path(name, subdir)
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(records, f, ensure_ascii=False, indent=2)
    os.replace(tmp, path)


def append(name: str, record: dict, subdir: str = "daily") -> tuple:
    """追加一筆，回傳 (index, records)。records 供呼叫端直接聚合，避免重讀。"""
    records = _read_all(name, subdir)
    records.append(record)
    _write_all(name, records, subdir)
    return len(records) - 1, records


def all_records(name: str, subdir: str = "daily") -> list:
    return _read_all(name, subdir)


def last_n(name: str, n: int, subdir: str = "daily") -> list:
    """最近 n 筆（新的在前）。"""
    return list(reversed(_read_all(name, subdir)[-n:]))


def replace(name: str, records: list, subdir: str = "daily") -> None:
    _write_all(name, records, subdir)


def count(name: str, subdir: str = "daily") -> int:
    return len(_read_all(name, subdir))


def filter_replace(name: str, keep_predicate, subdir: str = "daily") -> int:
    """讀取→過濾→覆寫，回傳被移除筆數。keep_predicate(r) -> bool 為保留條件。"""
    records = _read_all(name, subdir)
    kept = [r for r in records if keep_predicate(r)]
    if len(kept) != len(records):
        _write_all(name, kept, subdir)
    return len(records) - len(kept)


# ---------------------------------------------------------------- 整庫備份 / 還原

_COLLECTIONS = ["expenses", "health", "reminders", "shopping", "mood_log", "study_notes", "decisions"]


def export_all() -> dict:
    """備份整庫：daily 各集合 + daozang 各人格，回傳可 JSON 序列化之 dict。

    匯出不含損壞備份檔（*.corrupt）。用於「記憶逃生艙」。
    """
    data = {"daily": {name: _read_all(name, "daily") for name in _COLLECTIONS}}
    dz_dir = os.path.join(base_dir(), "daozang")
    data["daozang"] = {}
    if os.path.isdir(dz_dir):
        for f in sorted(os.listdir(dz_dir)):
            if f.endswith(".json") and not f.endswith(".corrupt"):
                data["daozang"][f[:-5]] = _read_all(f[:-5], "daozang")
    return data


def import_all(data: dict) -> int:
    """從 export_all 產生的 dict 還原整庫，回傳還原之集合數。"""
    count = 0
    for name, records in (data.get("daily") or {}).items():
        if isinstance(records, list):
            _write_all(name, records, "daily")
            count += 1
    for persona, records in (data.get("daozang") or {}).items():
        if isinstance(records, list):
            _write_all(persona, records, "daozang")
            count += 1
    return count
