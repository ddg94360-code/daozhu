"""週報＋精力分析：聚合近 7 天日用集數據，輸出週回顧與精力洞察。"""
from collections import Counter
from datetime import datetime, timedelta

import memory_store as store
import daily
import config


def _week_bounds() -> tuple:
    """近 7 天窗口 (cutoff, today) 之 ISO 日期字串。"""
    n = datetime.now()
    today = n.strftime("%Y-%m-%d")
    cutoff = (n - timedelta(days=6)).strftime("%Y-%m-%d")
    return cutoff, today


def weekly_report() -> dict:
    """週回顧：支出、睡眠、運動、情緒趨勢、學習筆記、精力洞察。"""
    cutoff, today = _week_bounds()
    now_iso = datetime.now().isoformat(timespec="seconds")

    expenses = [r for r in store.all_records("expenses") if cutoff <= r["date"][:10] <= today]
    total_spend = round(sum(r["amount"] for r in expenses), 2)

    health = [r for r in store.all_records("health") if cutoff <= r["date"][:10] <= today]
    sleep_vals = [r["sleep_hours"] for r in health if r.get("sleep_hours", 0) > 0]
    avg_sleep = round(sum(sleep_vals) / len(sleep_vals), 1) if sleep_vals else 0
    exercise_count = sum(1 for r in health if r.get("exercise", ""))

    moods = [r for r in store.all_records("mood_log") if cutoff <= r["date"][:10] <= today]
    mood_trend = {k: sum(1 for r in moods if r.get("classification", "中性") == k)
                  for k in ("正向", "中性", "負向")}

    notes = [r for r in store.all_records("study_notes") if cutoff <= r["date"][:10] <= today]
    due = [r for r in notes if not r.get("reviewed") and r.get("review_date", "") <= now_iso]

    decisions = [r for r in store.all_records("decisions")
                 if cutoff <= r.get("timestamp", "")[:10] <= today]

    consecutive_negative = daily._consecutive_negative_days(moods)

    return {
        "period": f"{cutoff} ~ {today}",
        "expense_total": total_spend,
        "sleep_avg_hours": avg_sleep,
        "exercise_count": exercise_count,
        "mood_trend": mood_trend,
        "study_notes_added": len(notes),
        "study_notes_due": len(due),
        "decisions_logged": len(decisions),
        "energy_insight": _energy_insight(moods),
        "care_flag": consecutive_negative >= 3,
        "currency": config.currency_symbol(),
    }


def _energy_insight(mood_records: list) -> str:
    """精力洞察：依日誌時間戳分佈，找出活躍時段與低谷。

    數據不足 7 筆時回傳引導語，不輸出假分析。
    """
    hours = []
    for r in mood_records:
        try:
            hours.append(int(r.get("date", "")[11:13]))
        except (ValueError, IndexError):
            continue
    if len(hours) < 7:
        return "數據不足：需累積至少 7 天日誌才可產出精力分析。"
    peak = Counter(hours).most_common()
    top_hours = sorted(h for h, _ in peak[:3])
    bottom_hours = sorted(h for h, _ in peak[-2:])
    return (f"活躍時段集中於 {_fmt_hours(top_hours)}；"
            f"相對低谷在 {_fmt_hours(bottom_hours)}，建議安排低腦力工作。")


def _fmt_hours(hours: list) -> str:
    return "、".join(f"{h}-{h + 1}時" for h in hours)


def status() -> dict:
    """系統健康檢查：各記憶庫筆數與運作狀態。"""
    counts = {
        "expenses": store.count("expenses"),
        "health": store.count("health"),
        "reminders": store.count("reminders"),
        "shopping": store.count("shopping"),
        "mood_log": store.count("mood_log"),
        "study_notes": store.count("study_notes"),
        "decisions": store.count("decisions"),
    }
    return {"status": "ok", "memory_dir": store.base_dir(), "counts": counts}
