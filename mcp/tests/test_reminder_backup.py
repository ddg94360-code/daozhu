"""提醒系統與整庫備份測試。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from datetime import datetime

import daily
import daozang
import memory_store as store


# ---------------------------------------------------------------- 提醒系統
def _freeze(monkeypatch, iso: str) -> None:
    monkeypatch.setattr(store, "_wall_clock", lambda: datetime.fromisoformat(iso))


def test_due_reminders_filters_by_time(isolated_memory, monkeypatch):
    _freeze(monkeypatch, "2026-08-13T10:00:00")
    daily.add_reminder("過期事項", "2026-08-13T09:00:00")
    daily.add_reminder("未來事項", "2026-08-14T09:00:00")
    due = daily.due_reminders()
    assert len(due) == 1
    assert due[0]["content"] == "過期事項"


def test_mark_reminder_done(isolated_memory, monkeypatch):
    _freeze(monkeypatch, "2026-08-13T10:00:00")
    rec = daily.add_reminder("買牛奶", "2026-08-13T10:00:00")
    rid = rec["record"]["id"]
    assert daily.mark_reminder_done(rid)["matched"] is True
    assert daily.due_reminders() == []
    # 標記完成是就地改 done，不是刪除
    remaining = store.all_records("reminders")
    assert len(remaining) == 1
    assert remaining[0]["done"] is True
    assert remaining[0]["id"] == rid
    assert daily.pending_reminders() == []


# ---------------------------------------------------------------- 整庫備份
def test_export_import_all_roundtrip(isolated_memory):
    daily.log_expense("午餐", 150)
    daily.log_mood("好煩")
    exported = store.export_all()
    assert len(exported["daily"]["expenses"]) == 1

    # 清空後還原
    store.replace("expenses", [], "daily")
    store.replace("mood_log", [], "daily")
    n = store.import_all(exported)
    assert n >= 2
    assert store.count("expenses") == 1
    assert store.count("mood_log") == 1


def test_export_includes_daozang(isolated_memory):
    daozang.store("daoist", "順勢而行", "天之道", "好焦慮")
    exported = store.export_all()
    assert "daoist" in exported["daozang"]
    assert exported["daozang"]["daoist"][0]["classify"] == "天之道"


def test_import_skips_invalid_data(isolated_memory):
    # 非 list 的資料被忽略，不崩潰
    n = store.import_all({"daily": {"expenses": "not-a-list"}, "daozang": {"daoist": 42}})
    assert n == 0


# ---------------------------------------------------------------- 就地更新 primitive
def test_map_update_transforms_matching_records(isolated_memory):
    store.append("reminders", {"id": "a", "done": False})
    store.append("reminders", {"id": "b", "done": False})
    n = store.map_update(
        "reminders",
        lambda r: r["id"] == "a",
        lambda r: {**r, "done": True},
    )
    assert n == 1
    recs = {r["id"]: r for r in store.all_records("reminders")}
    assert recs["a"]["done"] is True
    assert recs["b"]["done"] is False


def test_map_update_no_match_writes_nothing(isolated_memory):
    store.append("reminders", {"id": "a", "done": False})
    n = store.map_update("reminders", lambda r: r["id"] == "missing", lambda r: {**r, "done": True})
    assert n == 0
    assert store.all_records("reminders")[0]["done"] is False


# ---------------------------------------------------------------- 採買 / 學習筆記標記
def test_check_shopping_marks_checked_not_deletes(isolated_memory):
    daily.add_shopping("牛奶")
    daily.add_shopping("雞蛋")
    assert daily.check_shopping("牛奶")["matched"] is True
    items = {r["item"]: r for r in daily.list_shopping()}
    assert len(items) == 2
    assert items["牛奶"]["checked"] is True
    assert items["雞蛋"]["checked"] is False


def test_mark_study_note_reviewed(isolated_memory, monkeypatch):
    _freeze(monkeypatch, "2026-08-13T10:00:00")
    daily.add_study_note("物理", "熵增定律", review_days=0)
    due = daily.due_study_notes()
    assert len(due) == 1
    res = daily.mark_study_note_reviewed("熵增")
    assert res["matched"] is True
    assert daily.due_study_notes() == []
    recs = store.all_records("study_notes")
    assert len(recs) == 1
    assert recs[0]["reviewed"] is True
