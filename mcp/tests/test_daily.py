"""daozhu-mcp 測試：記憶庫讀寫、日用集邏輯、週報聚合。

測試用 tmp 目錄隔離記憶庫（DAOZHU_MEMORY_DIR，見 conftest.py）。
"""
import os

import daily
import memory_store as store
import weekly


# ---------------------------------------------------------------- memory_store
def test_append_and_read(isolated_memory):
    store.append("expenses", {"item": "測試", "amount": 10})
    assert store.count("expenses") == 1
    assert store.all_records("expenses")[0]["amount"] == 10


def test_missing_file_returns_empty(isolated_memory):
    assert store.all_records("nonexistent") == []


def test_corrupt_file_backed_up(isolated_memory):
    daily_dir = os.path.join(store.base_dir(), "daily")
    os.makedirs(daily_dir, exist_ok=True)
    with open(os.path.join(daily_dir, "expenses.json"), "w", encoding="utf-8") as f:
        f.write("{broken json")
    assert store.all_records("expenses") == []
    assert os.path.exists(os.path.join(daily_dir, "expenses.json.corrupt"))


# ---------------------------------------------------------------- 記帳
def test_expense_auto_category(isolated_memory):
    rec = daily.log_expense("午餐吃了150", 150)
    assert rec["record"]["category"] == "飲食"
    assert rec["total"] == 150


def test_expense_explicit_category(isolated_memory):
    rec = daily.log_expense("買書", 320, "學習")
    assert rec["record"]["category"] == "學習"


# ---------------------------------------------------------------- 情緒日記
def test_mood_classification(isolated_memory):
    assert daily.classify_mood("好煩") == "負向"
    assert daily.classify_mood("今天好開心") == "正向"
    assert daily.classify_mood("普通的一天") == "中性"


def test_consecutive_negative_care_flag(isolated_memory, monkeypatch):
    # 跨 3 天各寫一筆負向，驗證「連續 3 天」觸發關心提示
    for d in ["2026-08-10T10:00:00", "2026-08-11T10:00:00", "2026-08-12T10:00:00"]:
        monkeypatch.setattr(daily, "now", lambda d=d: d)
        daily.log_mood("好煩")
    rec = daily.log_mood("壓力大")
    assert rec["consecutive_negative_days"] == 3  # 三個不同天
    assert rec["care_note"]


def test_same_day_multiple_negative_counts_as_one(isolated_memory):
    daily.log_mood("好煩")
    daily.log_mood("好累")
    rec = daily.log_mood("撐不下去")
    assert rec["consecutive_negative_days"] == 1  # 同一天只算一天


# ---------------------------------------------------------------- 學習筆記
def test_study_note_summary_long_content(isolated_memory):
    long_content = ("熵增定律是熱力學第二定律的核心，它揭示了孤立系統的熵永遠不會自發減少，"
                    "所有自然過程都朝向更混亂、更無序的方向演進，這是理解時間箭頭的關鍵。")
    rec = daily.add_study_note("物理", long_content)
    assert rec["record"]["summary"].endswith("…")


def test_study_note_due(isolated_memory):
    daily.add_study_note("歷史", "法國大革命", review_days=0)  # 立即到期
    assert len(daily.due_study_notes()) == 1


def test_delete_study_note(isolated_memory):
    daily.add_study_note("數學", "傅立葉變換")
    res = daily.delete_study_note("傅立葉")
    assert res["removed"] == 1
    assert daily.list_study_notes() == []


# ---------------------------------------------------------------- 週報
def test_weekly_report_structure(isolated_memory):
    daily.log_expense("早餐", 60)
    daily.log_health(sleep_hours=7)
    daily.log_mood("好開心")
    daily.log_decision("是否接專案", "接", "時程可行")
    report = weekly.weekly_report()
    assert report["expense_total"] == 60
    assert report["sleep_avg_hours"] == 7
    assert report["mood_trend"].get("正向") == 1
    assert report["decisions_logged"] == 1


def test_status_counts(isolated_memory):
    daily.log_mood("好煩")
    status = weekly.status()
    assert status["status"] == "ok"
    assert status["counts"]["mood_log"] == 1


def test_check_shopping_by_id_only_touches_that_row(isolated_memory):
    a = daily.add_shopping("咖啡")["record"]
    b = daily.add_shopping("咖啡")["record"]
    assert daily.check_shopping_by_id(a["id"])["matched"] is True
    items = {r["id"]: r for r in daily.list_shopping()}
    assert items[a["id"]]["checked"] is True
    assert items[b["id"]]["checked"] is False


def test_check_shopping_by_id_missing_or_already_checked(isolated_memory):
    rec = daily.add_shopping("牛奶")["record"]
    assert daily.check_shopping_by_id("no-such")["matched"] is False
    assert daily.check_shopping_by_id(rec["id"])["matched"] is True
    assert daily.check_shopping_by_id(rec["id"])["matched"] is False
    assert len(daily.list_shopping()) == 1


def test_remove_shopping_by_id_only_deletes_that_row(isolated_memory):
    a = daily.add_shopping("雞蛋")["record"]
    b = daily.add_shopping("雞蛋")["record"]
    assert daily.remove_shopping_by_id(a["id"])["removed"] == 1
    left = daily.list_shopping()
    assert len(left) == 1
    assert left[0]["id"] == b["id"]
    assert daily.remove_shopping_by_id("no-such")["removed"] == 0
