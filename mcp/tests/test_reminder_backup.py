"""提醒系統與整庫備份測試。"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import daily
import daozang
import memory_store as store


# ---------------------------------------------------------------- 提醒系統
def test_due_reminders_filters_by_time(isolated_memory, monkeypatch):
    monkeypatch.setattr(daily, "now", lambda: "2026-08-13T10:00:00")
    daily.add_reminder("過期事項", "2026-08-13T09:00:00")
    daily.add_reminder("未來事項", "2026-08-14T09:00:00")
    due = daily.due_reminders()
    assert len(due) == 1
    assert due[0]["content"] == "過期事項"


def test_mark_reminder_done(isolated_memory, monkeypatch):
    monkeypatch.setattr(daily, "now", lambda: "2026-08-13T10:00:00")
    rec = daily.add_reminder("買牛奶", "2026-08-13T10:00:00")
    rid = rec["record"]["id"]
    assert daily.mark_reminder_done(rid)["matched"] is True
    assert daily.due_reminders() == []
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
