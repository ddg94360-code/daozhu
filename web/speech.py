"""內閣五階段模板填槽。不呼叫模型。"""
from __future__ import annotations

import os
import re
from typing import Any

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_SKILLS = os.path.join(_REPO, "skills", "daozhu")

_FILES = {
    "儒家": os.path.join(_SKILLS, "ministers", "confucian.md"),
    "道家": os.path.join(_SKILLS, "ministers", "daoist.md"),
    "法家": os.path.join(_SKILLS, "ministers", "legalist.md"),
    "縱橫家": os.path.join(_SKILLS, "ministers", "strategist.md"),
    "兵家": os.path.join(_SKILLS, "patches", "military.md"),
    "墨家": os.path.join(_SKILLS, "patches", "mohist.md"),
    "佛教": os.path.join(_SKILLS, "patches", "buddhist.md"),
}

_CLASSICS_SECTION = {
    "儒家": "儒家",
    "道家": "道家",
    "法家": "法家",
    "縱橫家": "縱橫家",
    "兵家": "兵家",
    "墨家": "墨家",
    "佛教": "佛教",
}

_FALLBACK_XINFA = {
    "儒家": "修己以安人",
    "道家": "反者道之動，弱者道之用",
    "法家": "循名責實，信賞必罰",
    "縱橫家": "捭闔為道，反應為法",
    "兵家": "知彼知己，百戰不殆",
    "墨家": "以類取，以類予",
    "佛教": "念起即覺，覺已不隨",
}

_FALLBACK_CLASSIC = {
    "儒家": "己所不欲，勿施於人。",
    "道家": "上善若水。",
    "法家": "法不阿貴，繩不撓曲。",
    "縱橫家": "捭闔者，天地之道。",
    "兵家": "知彼知己，百戰不殆。",
    "墨家": "兼相愛，交相利。",
    "佛教": "照見五蘊皆空。",
}

_VERDICT_BODY = "請在看板決策塊手寫，或把 persist 設為 true 只記「會議已開」。"
DEPTHS = ("brief", "deep", "flash")
CABINET_NAMES = tuple(_FILES.keys())
_FLASH_PLACEHOLDER = "（即時共識已併入各抒）"


def normalize_depth(raw: Any) -> str:
    """空／缺省 → brief。非法值 raise ValueError。"""
    if raw is None or str(raw).strip() == "":
        return "brief"
    depth = str(raw).strip().lower()
    if depth not in DEPTHS:
        raise ValueError("深度須為 brief／deep／flash")
    return depth


def fill(preview: dict, depth: str = "brief") -> list[dict]:
    """依 preview 的出席把五階段 body 填上模板句。回新 list，不改入參。"""
    depth = normalize_depth(depth)
    topic = str(preview.get("topic") or "")
    core = list(preview.get("core") or [])
    adjunct = list(preview.get("adjunct") or [])
    names = "、".join(m.get("name", "") for m in core + adjunct) or "（無）"
    stages = [dict(s) for s in (preview.get("stages") or [])]
    by_name = {s.get("name"): s for s in stages}

    if depth == "flash":
        if "開題" in by_name:
            by_name["開題"]["body"] = f"即時共識。議題：「{topic}」。出席：{names}。"
        if "各抒己見" in by_name:
            bits = [f"{m.get('name')}（{m.get('role')}）：{_xinfa(str(m.get('name') or ''))}" for m in core]
            by_name["各抒己見"]["body"] = "；".join(bits) or "（無核心內閣）"
        if "列席補充" in by_name:
            by_name["列席補充"]["body"] = _FLASH_PLACEHOLDER
        if "議長結辯" in by_name:
            by_name["議長結辯"]["body"] = _FLASH_PLACEHOLDER
        if "您裁決" in by_name:
            by_name["您裁決"]["body"] = _VERDICT_BODY
        return stages

    if "開題" in by_name:
        by_name["開題"]["body"] = f"收到。本次會議議題：「{topic}」。出席內閣：{names}。會議開始。"
    if "各抒己見" in by_name:
        if depth == "deep":
            by_name["各抒己見"]["body"] = "\n".join(_line_deep(m, topic) for m in core) or "（無核心內閣）"
        else:
            by_name["各抒己見"]["body"] = "\n".join(_line(m, topic) for m in core) or "（無核心內閣）"
    if "列席補充" in by_name:
        if adjunct:
            extra = "可再質詢。" if depth == "deep" else ""
            by_name["列席補充"]["body"] = "\n".join(_line(m, topic) + extra for m in adjunct)
        else:
            by_name["列席補充"]["body"] = "本場無列席。"
    if "議長結辯" in by_name:
        by_name["議長結辯"]["body"] = (
            f"共識點：各家都圍著「{topic}」說話。"
            f"分歧點：價值／成本／感受權重不同。"
            f"綜合建議：先定名分與成本，再調身心。非正式會議紀錄。"
        )
    if "您裁決" in by_name:
        by_name["您裁決"]["body"] = _VERDICT_BODY
    return stages


def followup(name: str, topic: str, question: str, stages: list | None = None) -> str:
    """二次質詢模板。name 須為四子或三補丁。stages 可選，帶本場會議摘句。"""
    if name not in CABINET_NAMES:
        raise ValueError("查無此內閣")
    xinfa = _xinfa(name)
    classic = _classic(name)
    ctx = stage_context(name, stages)
    if ctx:
        return (
            f"【{name}·追問】就「{topic}」再問「{question}」。"
            f"先前：{ctx}。{xinfa}。經云「{classic}」先答這一問。"
        )
    return f"【{name}·追問】就「{topic}」再問「{question}」：{xinfa}。經云「{classic}」先答這一問。"


def stage_context(name: str, stages: Any) -> str:
    """從五階段摘該內閣與結辯，供追問引用。不改入參。"""
    if not isinstance(stages, list):
        return ""
    bits: list[str] = []
    for s in stages:
        if not isinstance(s, dict):
            continue
        body = str(s.get("body") or "").strip()
        if not body:
            continue
        stage_name = str(s.get("name") or "")
        if name in body or stage_name == "議長結辯":
            bits.append(body[:160])
    return "／".join(bits)[:280]


def _line(member: dict, topic: str) -> str:
    name = str(member.get("name") or "")
    role = str(member.get("role") or "")
    xinfa = _xinfa(name)
    classic = _classic(name)
    return f"【{name}·{role}】就「{topic}」：{xinfa}。經云「{classic}」請先從可做的一步起。"


def _line_deep(member: dict, topic: str) -> str:
    name = str(member.get("name") or "")
    role = str(member.get("role") or "")
    xinfa = _xinfa(name)
    classic = _classic(name)
    return (
        f"【{name}·{role}】就「{topic}」先立心法：{xinfa}。"
        f"再落到一步：經云「{classic}」，今晚只做能檢查的那一件。"
    )


def _xinfa(name: str) -> str:
    path = _FILES.get(name)
    if path and os.path.isfile(path):
        text = _read(path)
        m = re.search(r"「([^」]+)」", text)
        if m:
            return m.group(1)
    return _FALLBACK_XINFA.get(name, "先把事情看清楚")


def _classic(name: str) -> str:
    path = os.path.join(_SKILLS, "modules", "classics.md")
    section = _CLASSICS_SECTION.get(name)
    if section and os.path.isfile(path):
        text = _read(path)
        marker = f"## {section}"
        idx = text.find(marker)
        if idx >= 0:
            chunk = text[idx: idx + 800]
            rows = re.findall(r"\| 《[^|]+》 \| ([^|]+) \|", chunk)
            if rows:
                return rows[0].strip()
    return _FALLBACK_CLASSIC.get(name, "知止不殆")


def _read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()
