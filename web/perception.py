"""依記憶推斷七層感知亮燈。不是一次真實對話感知。"""
from __future__ import annotations

import daily
import memory_store as store
import weekly


def infer() -> dict:
    """讀現成 daily／weekly，回七層 on/hint。不寫檔。"""
    report = weekly.weekly_report()
    latest = _latest_mood_class()
    pending = daily.pending_reminders()
    due_notes = daily.due_study_notes()

    emotion_on = bool(latest)
    emotion_hint = f"最近：{latest}" if latest else ""

    task_on = bool(pending) or bool(due_notes)
    task_hint = f"待辦 {len(pending)}／到期筆記 {len(due_notes)}" if task_on else ""

    decisions = int(report.get("decisions_logged") or 0)
    complexity_on = decisions >= 1
    complexity_hint = f"本週決策 {decisions}" if complexity_on else ""

    insight = str(report.get("energy_insight") or "")
    energy_on = bool(insight) and "數據不足" not in insight
    energy_hint = (insight[:40] + "…") if energy_on and len(insight) > 40 else (insight if energy_on else "")

    return {
        "layers": [
            {"key": "emotion", "label": "情緒", "on": emotion_on, "hint": emotion_hint},
            {"key": "task", "label": "任務", "on": task_on, "hint": task_hint},
            {"key": "interpersonal", "label": "人際", "on": False, "hint": ""},
            {"key": "complexity", "label": "複雜", "on": complexity_on, "hint": complexity_hint},
            {"key": "concise", "label": "精簡", "on": False, "hint": ""},
            {"key": "tone", "label": "語氣", "on": False, "hint": ""},
            {"key": "energy", "label": "精力", "on": energy_on, "hint": energy_hint},
        ],
        "disclaimer": "依記憶推斷，不是一次真實對話感知。",
    }


def _latest_mood_class() -> str:
    recs = store.all_records("mood_log")
    if not recs:
        return ""
    return str(recs[-1].get("classification") or "")
