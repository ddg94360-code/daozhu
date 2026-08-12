"""陰陽時令：計算 24 節氣日期（壽星公式，適用 1900-2099），判斷當前節氣與養生方向。

嵌入道家第一階：節氣轉換前後 3 天內每日首次對話提示一次。
"""
from datetime import datetime

# 21 世紀節氣常數（C 值）。順序：小寒..冬至 共 24 個。
_TERMS = [
    ("小寒", 1, 5.4055), ("大寒", 1, 20.12),
    ("立春", 2, 3.87), ("雨水", 2, 18.73),
    ("驚蟄", 3, 5.63), ("春分", 3, 20.646),
    ("清明", 4, 4.81), ("穀雨", 4, 20.1),
    ("立夏", 5, 5.52), ("小滿", 5, 21.04),
    ("芒種", 6, 5.678), ("夏至", 6, 21.37),
    ("小暑", 7, 7.108), ("大暑", 7, 22.83),
    ("立秋", 8, 7.5), ("處暑", 8, 23.13),
    ("白露", 9, 7.646), ("秋分", 9, 23.042),
    ("寒露", 10, 8.318), ("霜降", 10, 23.438),
    ("立冬", 11, 7.438), ("小雪", 11, 22.36),
    ("大雪", 12, 7.18), ("冬至", 12, 21.94),
]

# 養生方向：春生/夏長/秋收/冬藏（四立四至為分界）
_SEASON = {
    "立春": "春", "雨水": "春", "驚蟄": "春", "春分": "春", "清明": "春", "穀雨": "春",
    "立夏": "夏", "小滿": "夏", "芒種": "夏", "夏至": "夏", "小暑": "夏", "大暑": "夏",
    "立秋": "秋", "處暑": "秋", "白露": "秋", "秋分": "秋", "寒露": "秋", "霜降": "秋",
    "立冬": "冬", "小雪": "冬", "大雪": "冬", "冬至": "冬", "小寒": "冬", "大寒": "冬",
}
_SEASON_GUIDE = {"春": "生發", "夏": "宣洩", "秋": "收斂", "冬": "閉藏"}
# 前後幾天內視為「節氣轉換期」
_WINDOW_DAYS = 3


def _solar_term_date(name: str, month: int, c: float, year: int) -> datetime:
    """壽星公式：節氣日 = int(Y×0.2422 + C − int((Y−1)/4))，Y 為年份後兩位。"""
    y = year % 100
    day = int(y * 0.2422 + c - int((y - 1) / 4))
    return datetime(year, month, day)


def all_solar_terms(year: int) -> list[dict]:
    """該年全部 24 個節氣。date 為 datetime 物件，輸出時才格式化。"""
    out = []
    for name, month, c in _TERMS:
        season = _SEASON[name]
        dt = _solar_term_date(name, month, c, year)
        out.append({"name": name, "month": month, "day": dt.day, "date": dt,
                    "season": season, "guide": f"{season}·{_SEASON_GUIDE[season]}"})
    return out


def current_solar_term(today: datetime | None = None) -> dict:
    """回傳當前節氣狀態。

    建一條跨年連續時間線（上一年最後一節氣 + 今年 24 + 下一年第一個），
    線性掃描一次即得 current/next，無年初/年末特例分支。
    """
    today = today or datetime.now()
    timeline = all_solar_terms(today.year - 1)[-1:] + all_solar_terms(today.year) + all_solar_terms(today.year + 1)[:1]

    i = 0
    while i < len(timeline) - 1 and today >= timeline[i + 1]["date"]:
        i += 1
    current, next_term = timeline[i], timeline[i + 1]

    near = ((today - current["date"]).days <= _WINDOW_DAYS
            or (next_term["date"] - today).days <= _WINDOW_DAYS)

    return {
        "current": current["name"],
        "current_season": current["season"],
        "next": next_term["name"],
        "near_transition": near,
        "guide": f"{current['name']}·{current['guide']}",
    }
