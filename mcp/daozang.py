"""道藏：各人格成功策略案例庫。

存於 local_memory/daozang/<persona>.json（subdir="daozang"）。
分類標籤：道家=天之道/人之道/鬼之道；縱橫家=合/連/攬/破/靜；法家=賞/刑/法。
"""
import memory_store as ms

now = ms.now
PERSONAE = ["daoist", "strategist", "legalist", "confucian"]
SUBDIR = "daozang"
CLASSIFY = {
    "daoist": ["天之道", "人之道", "鬼之道"],
    "strategist": ["合", "連", "攬", "破", "靜"],
    "legalist": ["賞", "刑", "法"],
}


def _validate(persona: str, classify: str = "") -> str | None:
    """驗證 persona（與選擇性 classify）。合法回 None，否則回錯誤訊息。"""
    if persona not in PERSONAE:
        return f"persona 必須為 {PERSONAE} 之一"
    if classify and persona in CLASSIFY and classify not in CLASSIFY[persona]:
        return f"classify '{classify}' 不合法，應為 {CLASSIFY[persona]}"
    return None


def store(persona: str, strategy: str, classify: str, trigger_question: str = "", outcome: str = "待觀察") -> dict:
    """存入一條成功策略案例至對應人格道藏。"""
    err = _validate(persona, classify)
    if err:
        return {"error": err}
    rec = {"timestamp": now(), "persona_type": persona, "trigger_question": trigger_question,
           "adopted_strategy": strategy, "classify": classify, "outcome": outcome}
    idx, _ = ms.append(persona, rec, subdir=SUBDIR)
    return {"record": rec, "total": idx + 1}


def recall(persona: str, classify: str = "") -> dict:
    """召回某人格之成功策略，可依分類過濾。新的在前。"""
    err = _validate(persona)
    if err:
        return {"error": err}
    records = ms.all_records(persona, subdir=SUBDIR)
    if classify:
        records = [r for r in records if r.get("classify") == classify]
    return {"persona": persona, "count": len(records), "records": list(reversed(records[-10:]))}


def count_all() -> dict:
    return {p: ms.count(p, subdir=SUBDIR) for p in PERSONAE}
