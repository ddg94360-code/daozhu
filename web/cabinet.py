"""議題 → 內閣出席與五階段空位。不生成會議文字。"""
from __future__ import annotations

STAGES = [
    {"name": "開題", "who": "議長", "body": ""},
    {"name": "各抒己見", "who": "核心內閣", "body": ""},
    {"name": "列席補充", "who": "列席內閣", "body": ""},
    {"name": "議長結辯", "who": "議長", "body": ""},
    {"name": "您裁決", "who": "你", "body": ""},
]

# 先命中先用。
_RULES: list[tuple[str, list[str], list[tuple[str, str]], list[tuple[str, str]]]] = [
    (
        "人際/師生/親友/倫理",
        ["教授", "老師", "組員", "同學", "主管", "老闆", "同事", "朋友", "家人",
         "男友", "女友", "對象", "客戶", "室友", "親戚", "長輩", "人際", "倫理"],
        [("儒家", "主")],
        [("縱橫家", "輔")],
    ),
    (
        "制度/規則/績效/時間管理",
        ["制度", "規則", "績效", "截止", "待辦", "時間管理"],
        [("法家", "主")],
        [("墨家", "輔")],
    ),
    (
        "競爭/談判/資源/說服",
        ["競爭", "談判", "資源", "說服"],
        [("縱橫家", "主")],
        [("兵家", "輔")],
    ),
    (
        "焦慮/壓力/迷惘/意義",
        ["焦慮", "壓力", "迷惘", "意義", "想放棄", "好煩", "累"],
        [("道家", "主")],
        [("佛教", "輔")],
    ),
    (
        "我要不要做某件事",
        ["該不該", "要不要"],
        [("儒家", "價值"), ("法家", "成本"), ("道家", "感受")],
        [],
    ),
    (
        "該怎麼執行具體任務",
        ["怎麼執行", "步驟", "怎麼做"],
        [("法家", "步驟"), ("兵家", "策略"), ("墨家", "邏輯")],
        [],
    ),
    (
        "生涯方向/長期規劃",
        ["生涯", "長期", "規劃"],
        [("道家", "視野"), ("儒家", "社會責任"), ("法家", "階段目標")],
        [],
    ),
]

_DEFAULT_RULE = "預設（價值／成本／感受）"
_DEFAULT_CORE = [("儒家", "價值"), ("法家", "成本"), ("道家", "感受")]


def preview(topic: str) -> dict:
    """依關鍵詞表排出席。不呼叫模型、不寫記憶。"""
    rule, core, adjunct = _match(topic)
    return {
        "topic": topic,
        "rule": rule,
        "chair": "議長（執中）",
        "core": [{"name": n, "role": r} for n, r in core],
        "adjunct": [{"name": n, "role": r} for n, r in adjunct],
        "stages": [dict(s) for s in STAGES],
        "disclaimer": "只排出席，不生成會議文字。",
    }


def _match(topic: str) -> tuple[str, list[tuple[str, str]], list[tuple[str, str]]]:
    for rule, needles, core, adjunct in _RULES:
        if any(n in topic for n in needles):
            return rule, core, adjunct
    return _DEFAULT_RULE, _DEFAULT_CORE, []
