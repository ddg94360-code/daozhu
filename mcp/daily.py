"""日用集：記帳、健康、提醒、採買、情緒日記、學習筆記、決策日誌。

儲存格式對應道樞建置文件第九章/第十五章規格（截斷處已補全）。
所有時間欄位為 ISO 8601，統一由 memory_store.now() 產生。
"""
import csv
import io
import uuid
from datetime import datetime, timedelta

import config
import memory_store as store

now = store.now


# ---------------------------------------------------------------- 記帳
EXPENSE_CATEGORIES = ["飲食", "交通", "娛樂", "學習", "其他"]


def log_expense(item: str, amount: float, category: str = "") -> dict:
    """記一筆消費。item 為項目名（如「午餐」「買筆記本」），amount 為金額。category 可省略，會自動歸類。"""
    cat = category if category in EXPENSE_CATEGORIES else _guess_category(item)
    rec = {"date": now(), "category": cat, "item": item, "amount": round(float(amount), 2)}
    _, records = store.append("expenses", rec)
    total = round(sum(r["amount"] for r in records), 2)
    return {"record": rec, "total": total, "currency": config.currency_symbol()}


def _guess_category(item: str) -> str:
    kw = {"飲食": ["餐", "飯", "麵", "吃", "咖啡", "飲料", "奶茶", "便當", "小吃"],
          "交通": ["車", "油", "捷運", "公車", "高鐵", "taxi", "uber", "火車"],
          "娛樂": ["電影", "遊戲", "課金", "音樂", "netflix", "steam", "演唱會"],
          "學習": ["書", "課程", "文具", "筆記本", "補習"]}
    for cat, words in kw.items():
        if any(w in item for w in words):
            return cat
    return "其他"


def month_expense_summary() -> dict:
    """本月支出摘要（依 category 聚合）。"""
    month = now()[:7]
    cats: dict[str, float] = {}
    for r in store.all_records("expenses"):
        if r.get("date", "").startswith(month):
            cat = r.get("category", "其他")
            cats[cat] = cats.get(cat, 0) + r["amount"]
    return {"month": month, "total": round(sum(cats.values()), 2),
            "by_category": {k: round(v, 2) for k, v in cats.items()},
            "currency": config.currency_symbol()}


def export_expenses_csv(month: str = "") -> str:
    """匯出指定月份（預設本月）記帳為 CSV 文字。"""
    month = month or now()[:7]
    records = [r for r in store.all_records("expenses") if r.get("date", "").startswith(month)]
    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["date", "category", "item", "amount", "currency"])
    for r in records:
        writer.writerow([r.get("date", ""), r.get("category", "其他"),
                         r.get("item", ""), r["amount"], config.currency_symbol()])
    return buf.getvalue()


# ---------------------------------------------------------------- 健康
def log_health(sleep_hours: float = 0, exercise: str = "", water: str = "") -> dict:
    """健康打卡：睡眠時數、運動、飲水。回傳連續達成天數。"""
    rec = {"date": now(), "sleep_hours": float(sleep_hours), "exercise": exercise, "water": water}
    store.append("health", rec)
    return {"record": rec, "consecutive_days": _consecutive_health_days()}


def _consecutive_health_days() -> int:
    """連續達成天數：從最新往回，有睡眠或運動紀錄且日曆相鄰的天算連續。"""
    days: list[str] = []
    for r in reversed(store.all_records("health")):
        if r.get("sleep_hours", 0) > 0 or r.get("exercise", ""):
            d = r["date"][:10]
            if not days or days[-1] != d:
                days.append(d)
        else:
            break
    if not days:
        return 0
    streak = 1
    for i in range(1, len(days)):
        newer = datetime.fromisoformat(days[i - 1]).date()
        older = datetime.fromisoformat(days[i]).date()
        if (newer - older).days == 1:
            streak += 1
        else:
            break
    return streak


# ---------------------------------------------------------------- 提醒
def add_reminder(content: str, datetime_str: str, recurring: bool = False) -> dict:
    """設定日程提醒。datetime_str 為 ISO 格式。"""
    rec = {"id": uuid.uuid4().hex[:8], "content": content, "datetime": datetime_str,
           "recurring": recurring, "done": False}
    store.append("reminders", rec)
    return {"record": rec}


def pending_reminders() -> list:
    return [r for r in store.all_records("reminders") if not r.get("done", False)]


def due_reminders() -> list:
    """回傳到期（datetime 已到）且未完成的提醒。供對話開始時自動檢查。"""
    now_iso = now()
    return [r for r in store.all_records("reminders")
            if not r.get("done", False) and r.get("datetime", "") <= now_iso]


def mark_reminder_done(reminder_id: str) -> dict:
    """標記某提醒為已完成（by id），就地改 done，不刪除。"""
    n = store.map_update(
        "reminders",
        lambda r: r.get("id") == reminder_id and not r.get("done", False),
        lambda r: {**r, "done": True},
    )
    return {"matched": n > 0}


# ---------------------------------------------------------------- 採買
def add_shopping(item: str) -> dict:
    rec = {"id": uuid.uuid4().hex[:8], "item": item, "checked": False}
    store.append("shopping", rec)
    return {"record": rec}


def list_shopping() -> list:
    return store.all_records("shopping")


def check_shopping(item: str) -> dict:
    """標記已購（模糊匹配 item），就地改 checked，不刪除。"""
    n = store.map_update(
        "shopping",
        lambda r: item in r["item"] and not r.get("checked", False),
        lambda r: {**r, "checked": True},
    )
    return {"matched": n > 0}


def remove_shopping(item: str) -> dict:
    removed = store.filter_replace("shopping", lambda r: item not in r["item"])
    return {"removed": removed}


def check_shopping_by_id(item_id: str) -> dict:
    """按 id 標記已購，就地改 checked，不刪除。"""
    n = store.map_update(
        "shopping",
        lambda r: r.get("id") == item_id and not r.get("checked", False),
        lambda r: {**r, "checked": True},
    )
    return {"matched": n > 0}


def remove_shopping_by_id(item_id: str) -> dict:
    """按 id 刪除一筆採買。"""
    removed = store.filter_replace("shopping", lambda r: r.get("id") != item_id)
    return {"removed": removed}


# ---------------------------------------------------------------- 情緒日記
POSITIVE = ["開心", "滿足", "平靜", "快樂", "興奮", "爽", "好", "喜歡", "期待", "放鬆"]
NEGATIVE = ["煩", "焦慮", "沮喪", "累", "難過", "生氣", "壓力", "崩潰", "撐不下去", "低落", "怕", "後悔", "自卑"]


def classify_mood(mood: str) -> str:
    for w in NEGATIVE:
        if w in mood:
            return "負向"
    for w in POSITIVE:
        if w in mood:
            return "正向"
    return "中性"


def log_mood(mood: str) -> dict:
    """情緒日記：記錄情緒詞並自動分類。"""
    classification = classify_mood(mood)
    rec = {"date": now(), "mood": mood, "classification": classification}
    _, records = store.append("mood_log", rec)
    consecutive = _consecutive_negative_days(records)
    note = "最近幾天感覺不太好。需要我陪你聊聊嗎？" if consecutive >= 3 else ""
    return {"record": rec, "consecutive_negative_days": consecutive, "care_note": note}


def _consecutive_negative_days(records: list | None = None) -> int:
    """連續負向天數：從最新往回數，遇到非負向筆即停。

    同一天多筆負向仍算一天；無記錄的日期不視為中斷。
    """
    records = records if records is not None else store.all_records("mood_log")
    seen: set[str] = set()
    for r in reversed(records):
        if r.get("classification") == "負向":
            seen.add(r["date"][:10])
        else:
            break
    return len(seen)


# ---------------------------------------------------------------- 學習筆記
def add_study_note(subject: str, content: str, review_days: int = 7) -> dict:
    """學習筆記：自動分類、超長自動摘要、排定複習日期。"""
    summary = content if len(content) <= 50 else content[:50] + "…"
    review_date = (datetime.fromisoformat(now()) + timedelta(days=int(review_days))).isoformat(timespec="seconds")
    rec = {"id": uuid.uuid4().hex[:8], "date": now(), "subject": subject, "original": content,
           "summary": summary, "review_date": review_date, "reviewed": False}
    store.append("study_notes", rec)
    return {"record": rec}


def list_study_notes(subject: str = "") -> list:
    records = store.all_records("study_notes")
    if subject:
        records = [r for r in records if subject in r.get("subject", "")]
    return list(reversed(records[-10:]))


def due_study_notes() -> list:
    now_iso = now()
    return [r for r in store.all_records("study_notes") if not r.get("reviewed") and r.get("review_date", "") <= now_iso]


def mark_study_note_reviewed(keyword: str) -> dict:
    """標記學習筆記為已複習（模糊匹配 subject 或原文）。"""
    n = store.map_update(
        "study_notes",
        lambda r: not r.get("reviewed") and (keyword in r.get("original", "") or keyword in r.get("subject", "")),
        lambda r: {**r, "reviewed": True},
    )
    return {"matched": n > 0}


def delete_study_note(keyword: str) -> dict:
    removed = store.filter_replace(
        "study_notes",
        lambda r: keyword not in r.get("original", "") and keyword not in r.get("subject", ""),
    )
    return {"removed": removed}


def mark_study_note_reviewed_by_id(note_id: str) -> dict:
    """按 id 標記學習筆記為已複習，就地改 reviewed，不刪除。"""
    n = store.map_update(
        "study_notes",
        lambda r: r.get("id") == note_id and not r.get("reviewed"),
        lambda r: {**r, "reviewed": True},
    )
    return {"matched": n > 0}


def delete_study_note_by_id(note_id: str) -> dict:
    """按 id 刪除一則學習筆記。"""
    removed = store.filter_replace("study_notes", lambda r: r.get("id") != note_id)
    return {"removed": removed}


# ---------------------------------------------------------------- 決策日誌
def log_decision(topic: str, verdict: str, reason: str = "") -> dict:
    rec = {"timestamp": now(), "topic": topic, "verdict": verdict, "reason": reason}
    store.append("decisions", rec)
    return {"record": rec}


def review_decisions(topic: str = "") -> list:
    records = store.all_records("decisions")
    if topic:
        records = [r for r in records if topic in r.get("topic", "")]
    return list(reversed(records))
