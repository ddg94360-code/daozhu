"""看板聊天窗規則路由。先命中先用；吃不下回 unknown。"""
from __future__ import annotations

import re
from typing import Any

import daily

INTENTS = (
    "expense",
    "mood",
    "shopping_add",
    "health",
    "reminder",
    "note",
    "decision",
    "query_expense",
    "query_reminders",
    "query_notes",
    "unknown",
)

_AMOUNT = re.compile(r"(-?\d+(?:\.\d+)?)")
_ISOISH = re.compile(r"(\d{4}-\d{2}-\d{2}[ T]\d{2}:\d{2}(?::\d{2})?)")
_FOOD = ("餐", "飯", "麵", "吃", "咖啡", "飲料", "奶茶", "便當", "小吃")
_PAY = ("吃了", "花了", "付了", "買了")
# daily.POSITIVE 含單字「好」，聊天窗不能把寒暄當情緒。
_MOOD_SKIP = {"好"}
_GENERIC_OK = {"好", "好的", "很好", "我很好", "好啊", "好吧", "好喔", "好哦"}


def parse(text: str) -> dict[str, Any]:
    """把一句話拆成 intent + slots。不寫記憶、不呼叫模型。"""
    raw = (text or "").strip()
    if not raw:
        return {"intent": "unknown", "slots": {}}

    expense = _expense(raw)
    if expense:
        return expense
    if _is_query_expense(raw):
        return {"intent": "query_expense", "slots": {}}
    reminders_q = _query_reminders(raw)
    if reminders_q:
        return reminders_q
    if _is_query_notes(raw):
        return {"intent": "query_notes", "slots": {}}
    shop = _shopping(raw)
    if shop:
        return shop
    health = _health(raw)
    if health:
        return health
    reminder = _reminder(raw)
    if reminder:
        return reminder
    note = _note(raw)
    if note:
        return note
    decision = _decision(raw)
    if decision:
        return decision
    mood = _mood(raw)
    if mood:
        return mood
    return {"intent": "unknown", "slots": {}}


def _expense(text: str) -> dict[str, Any] | None:
    m = _AMOUNT.search(text)
    if not m:
        return None
    amount = float(m.group(1))
    if amount <= 0:
        return None
    paid = any(p in text for p in _PAY)
    food = any(w in text for w in _FOOD)
    if not (paid or food):
        return None
    item = text[: m.start()]
    for p in _PAY:
        item = item.replace(p, "")
    item = item.strip(" 　，,。") or "未名項目"
    return {"intent": "expense", "slots": {"item": item, "amount": amount}}


def _mood(text: str) -> dict[str, Any] | None:
    if _AMOUNT.search(text):
        return None
    if text in _GENERIC_OK:
        return None
    hits = [w for w in list(daily.POSITIVE) + list(daily.NEGATIVE) if w not in _MOOD_SKIP]
    if any(w in text for w in hits):
        return {"intent": "mood", "slots": {"mood": text}}
    return None


def _shopping(text: str) -> dict[str, Any] | None:
    for prefix in ("採買：", "採買:", "記得買", "加入採買"):
        if text.startswith(prefix):
            item = text[len(prefix):].strip(" 　")
            if item:
                return {"intent": "shopping_add", "slots": {"item": item}}
    if text.startswith("買") and "買了" not in text:
        item = text[1:].strip(" 　")
        if item:
            return {"intent": "shopping_add", "slots": {"item": item}}
    return None


def _health(text: str) -> dict[str, Any] | None:
    slots: dict[str, Any] = {}
    sleep_m = re.search(r"(?:睡了|睡眠)\s*(-?\d+(?:\.\d+)?)", text)
    if sleep_m:
        slots["sleep_hours"] = float(sleep_m.group(1))
    ex_m = re.search(r"運動了\s*(.+)$", text)
    if ex_m:
        slots["exercise"] = ex_m.group(1).strip()
    water_m = re.search(r"喝了\s*(.+)$", text)
    if water_m:
        slots["water"] = water_m.group(1).strip()
    if slots:
        return {"intent": "health", "slots": slots}
    return None


def _reminder(text: str) -> dict[str, Any] | None:
    if "提醒" not in text:
        return None
    m = _ISOISH.search(text)
    if not m:
        return {"intent": "unknown", "slots": {"hint": "提醒缺少時間，請用表單"}}
    dt = m.group(1).replace(" ", "T")
    if len(dt) == 16:
        dt = dt + ":00"
    content = text.replace("提醒", "").replace(m.group(1), "").strip(" 　：:") or "提醒"
    return {"intent": "reminder", "slots": {"content": content, "datetime": dt}}


def _note(text: str) -> dict[str, Any] | None:
    if not (text.startswith("記 ") or text.startswith("記　")):
        return None
    rest = text[2:].strip()
    if "：" in rest:
        subject, content = rest.split("：", 1)
    elif ":" in rest:
        subject, content = rest.split(":", 1)
    else:
        parts = rest.split(None, 1)
        if len(parts) < 2:
            return {"intent": "unknown", "slots": {"hint": "筆記須有科目與內容"}}
        subject, content = parts
    subject, content = subject.strip(), content.strip()
    if not subject or not content:
        return {"intent": "unknown", "slots": {"hint": "筆記須有科目與內容"}}
    slots = {"subject": subject, "content": content}
    if "今天複習" in text or "立刻複習" in text:
        slots["review_days"] = 0
    return {"intent": "note", "slots": slots}


def _decision(text: str) -> dict[str, Any] | None:
    if not text.startswith("裁決"):
        return None
    rest = text[2:].lstrip(" 　：:")
    topic = ""
    verdict = ""
    tm = re.search(r"題目[=＝]([^決]+)", rest)
    vm = re.search(r"決[=＝](.+)$", rest)
    if tm and vm:
        topic, verdict = tm.group(1).strip(), vm.group(1).strip()
    elif "／" in rest:
        topic, verdict = [x.strip() for x in rest.split("／", 1)]
    elif "/" in rest:
        topic, verdict = [x.strip() for x in rest.split("/", 1)]
    if not topic or not verdict:
        return {"intent": "unknown", "slots": {"hint": "裁決格式：裁決 題目＝X 決＝Y"}}
    return {"intent": "decision", "slots": {"topic": topic, "verdict": verdict}}


def _is_query_expense(text: str) -> bool:
    return any(k in text for k in ("這個月花多少", "本月支出", "花了多少"))


def _query_reminders(text: str) -> dict[str, Any] | None:
    if "到期提醒" in text:
        return {"intent": "query_reminders", "slots": {"scope": "due"}}
    if any(k in text for k in ("有什麼待辦", "待辦提醒")):
        return {"intent": "query_reminders", "slots": {"scope": "pending"}}
    return None


def _is_query_notes(text: str) -> bool:
    return any(k in text for k in ("待複習", "到期筆記"))
