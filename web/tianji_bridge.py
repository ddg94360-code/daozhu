"""外掛本機 tianji-mcp。不把引擎複製進 daozhu。"""
from __future__ import annotations

import os
import sys
from datetime import datetime
from typing import Any

CAST_MODES = (
    "tarot", "gua", "fengshui", "chart", "bazi", "ziwei", "meihua",
    "qimen", "qizheng", "xingming", "numerology", "lenormand", "fusion",
)
NARRATIVE_MODES = ("yuan", "star", "dream")
DISCLAIMER = "命理僅供參考，非科學預測"
NOT_CAST = "此模式不算命"

_ELEMENT = {
    "坎": "水",
    "離": "火",
    "震": "木",
    "巽": "木",
    "坤": "土",
    "艮": "土",
    "乾": "金",
    "兌": "金",
}
_GLOW = {
    "水": "#6a9bff",
    "火": "#ff8a8a",
    "木": "#9be8b8",
    "土": "#d8c8a0",
    "金": "#ffd9a0",
}


def tianji_dir() -> str:
    return (os.environ.get("DAOZHU_TIANJI_DIR") or "").strip()


def available() -> bool:
    """目錄存在且能 import engines.tarot 才算接上。"""
    root = tianji_dir()
    if not root or not os.path.isdir(root):
        return False
    if root not in sys.path:
        sys.path.insert(0, root)
    try:
        import engines.tarot  # noqa: F401
    except Exception:
        return False
    return True


def status() -> dict[str, Any]:
    return {
        "tianji": available(),
        "dir": tianji_dir(),
        "modes": list(CAST_MODES),
        "narrative": list(NARRATIVE_MODES),
    }


def cast(mode: str, **kw: Any) -> dict[str, Any]:
    """呼叫本機引擎並轉成 xinjing JSON。未接則 raise RuntimeError('未接天機')。"""
    if mode in NARRATIVE_MODES or mode not in CAST_MODES:
        raise ValueError(NOT_CAST)
    if not available():
        raise RuntimeError("未接天機")
    if mode == "tarot":
        data = _cast_tarot(kw.get("seed"))
    elif mode == "gua":
        data = _cast_gua(str(kw.get("question") or ""), kw.get("seed"))
    elif mode == "fengshui":
        year = kw.get("year")
        gender = str(kw.get("gender") or "男")
        if year is None:
            raise ValueError("風水須提供 year")
        data = _cast_fengshui(int(year), gender)
    elif mode == "chart":
        if not str(kw.get("dt_local") or "").strip():
            raise ValueError("星盤須提供 dt_local")
        data = _cast_chart(kw)
    elif mode == "bazi":
        if not str(kw.get("dt_local") or "").strip():
            raise ValueError("須提供 dt_local")
        data = _cast_bazi(kw)
    elif mode == "ziwei":
        if not str(kw.get("dt_local") or "").strip():
            raise ValueError("須提供 dt_local")
        data = _cast_ziwei(kw)
    elif mode == "meihua":
        data = _cast_meihua(kw)
    elif mode == "qimen":
        if not str(kw.get("dt_local") or "").strip():
            raise ValueError("須提供 dt_local")
        data = _cast_qimen(kw)
    elif mode == "qizheng":
        if not str(kw.get("dt_local") or "").strip():
            raise ValueError("須提供 dt_local")
        data = _cast_qizheng(kw)
    elif mode == "xingming":
        surname, given = _name_parts(kw)
        if not surname or not given:
            raise ValueError("須提供姓名")
        data = _cast_xingming(kw)
    elif mode == "numerology":
        data = _cast_numerology(kw)
    elif mode == "lenormand":
        data = _cast_lenormand(kw.get("seed"))
    else:
        data = _cast_fusion(kw)
    return {"mode": mode, "data": data, "disclaimer": DISCLAIMER}


def _cast_tarot(seed: Any) -> dict[str, Any]:
    from engines.tarot import draw

    raw = draw(spread="three", seed=_int_or_none(seed))
    cards = []
    for c in raw.get("cards") or []:
        cards.append({
            "phase": c.get("position") or "",
            "img": "",
            "en": c.get("name") or "",
            "desc": f"{c.get('orientation') or ''}。{c.get('meaning') or ''}".strip("。"),
            "tip": c.get("orientation") or "",
        })
    return {
        "source": DISCLAIMER,
        "cards": cards,
        "delays": [400, 1500, 2700],
        "verdict": "、".join(c.get("en") or "" for c in cards),
    }


def _cast_gua(question: str, seed: Any) -> dict[str, Any]:
    from engines.liuyao import cast as liuyao_cast

    raw = liuyao_cast(question=question, seed=_int_or_none(seed))
    ben = raw.get("ben_gua") or {}
    name = ben.get("name") or ""
    symbol = ben.get("symbol") or ""
    yao = []
    labels = ("初", "二", "三", "四", "五", "上")
    for i, y in enumerate(raw.get("yaos") or []):
        val = int(y.get("value") or 8)
        yin = val % 2 == 0
        mark = "動" if y.get("動") else ("陰" if yin else "陽")
        yao.append({
            "label": f"{labels[i] if i < 6 else i}　{y.get('地支') or ''}",
            "yin": yin,
            "mark": mark,
            "desc": f"{y.get('六親') or ''}　{y.get('地支') or ''}",
        })
    return {
        "source": DISCLAIMER,
        "trigram": f"{symbol} {name}".strip(),
        "name": name,
        "mean": (raw.get("duanyu") or [{}])[0].get("text") or "",
        "yao": yao,
    }


def _cast_fengshui(year: int, gender: str) -> dict[str, Any]:
    from engines.fengshui import bazhai_gui

    raw = bazhai_gui(year, gender)
    gua = raw.get("命卦") or ""
    element = _ELEMENT.get(gua, "土")
    lucky = "、".join(raw.get("吉方") or [])
    text = f"命卦{gua}（{raw.get('東西四命') or ''}）。吉方：{lucky}。{DISCLAIMER}"
    return {
        "source": DISCLAIMER,
        "element": element,
        "glow": _GLOW.get(element, "#d8c8a0"),
        "text": text,
    }


def _cast_chart(kw: dict[str, Any]) -> dict[str, Any]:
    try:
        from engines.western import natal
    except Exception as e:
        raise RuntimeError("未接天機") from e
    dt = str(kw.get("dt_local") or "").strip()
    if not dt:
        raise ValueError("星盤須提供 dt_local")
    raw = natal(
        dt_local=_parse_dt(dt),
        lat=float(kw.get("lat") or 22.3),
        lon=float(kw.get("lon") or 114.2),
        tz_offset_hours=float(kw.get("tz_offset_hours") or 8),
    )
    planets_in = raw.get("planets") or raw.get("行星") or []
    if isinstance(planets_in, dict):
        planets_in = [{"name": k, **(v if isinstance(v, dict) else {"黃經": v})} for k, v in planets_in.items()]
    colors = {
        "太陽": "#ffd9a0", "月亮": "#a8c4ff", "水星": "#9be8b8",
        "金星": "#ffb8d8", "火星": "#ff8a8a", "木星": "#c8a0ff", "土星": "#d8c8a0",
    }
    syms = {"太陽": "☉", "月亮": "☽", "水星": "☿", "金星": "♀", "火星": "♂", "木星": "♃", "土星": "♄"}
    out = []
    for i, p in enumerate(planets_in[:7]):
        name = p.get("name") or p.get("名") or ""
        lon = p.get("lon") if "lon" in p else p.get("黃經")
        if lon is None:
            continue
        out.append({
            "name": name,
            "sym": syms.get(name, "·"),
            "ring": (i % 4) + 1,
            "deg": float(lon) % 360,
            "color": colors.get(name, "#e8e0ff"),
            "hl": name == "太陽",
            "meaning": p.get("sign") or p.get("星座") or "",
        })
    return {
        "source": DISCLAIMER,
        "planets": out,
        "summary": DISCLAIMER,
    }


def _cast_bazi(kw: dict[str, Any]) -> dict[str, Any]:
    from engines.bazi import BirthInput, paipan

    dt = str(kw.get("dt_local") or "").strip()
    if not dt:
        raise ValueError("須提供 dt_local")
    raw = paipan(
        BirthInput(
            dt_local=_parse_dt(dt),
            tz_offset_hours=float(kw.get("tz_offset_hours") or 8),
            longitude=float(kw.get("lon") or 120),
            gender=str(kw.get("gender") or "男"),
        )
    )
    sizhu = raw.get("sizhu") or {}
    day = (sizhu.get("日柱") or {}).get("ganzhi") or ""
    order = ("年柱", "月柱", "日柱", "時柱")
    name = "　".join(f"{k[0]}{(sizhu.get(k) or {}).get('ganzhi') or ''}" for k in order)
    ge = (raw.get("geju") or {}).get("格") or ""
    yong = (raw.get("yongshen") or {}).get("說明") or ""
    first_dayun = ""
    steps = (raw.get("dayun") or {}).get("步數") or []
    if steps:
        first_dayun = str(steps[0].get("干支") or "")
    yao = []
    for key in order:
        gz = (sizhu.get(key) or {}).get("ganzhi") or "——"
        yao.append({"label": key, "yin": False, "mark": "柱", "desc": gz})
    yao.append({"label": "大運", "yin": True, "mark": "運", "desc": first_dayun or "——"})
    yao.append({"label": "警語", "yin": True, "mark": "注", "desc": DISCLAIMER})
    return {
        "source": DISCLAIMER,
        "trigram": day or name,
        "name": name,
        "mean": f"{ge}。{yong}".strip("。"),
        "yao": yao,
    }


def _cast_ziwei(kw: dict[str, Any]) -> dict[str, Any]:
    from engines.ziwei import paipan

    dt = _parse_dt(str(kw.get("dt_local") or "").strip())
    raw = paipan(
        dt.year,
        dt.month,
        dt.day,
        dt.hour,
        minute=dt.minute,
        gender=str(kw.get("gender") or "男"),
    )
    ming = raw.get("命宮") or ""
    ju = raw.get("五行局") or {}
    ju_name = ju.get("局") if isinstance(ju, dict) else str(ju or "")
    ziwei_at = raw.get("紫微星在") or ""
    sihua = raw.get("四化") or {}
    sihua_txt = "、".join(f"{k}{v}" for k, v in sihua.items()) if isinstance(sihua, dict) else ""
    gongs = raw.get("十二宮") or {}
    yao = []
    for label, key in (("命", "命宮"), ("身", "身宮"), ("官祿", "官祿"), ("財帛", "財帛"), ("夫妻", "夫妻"), ("福德", "福德")):
        if key in ("命宮", "身宮") and not isinstance(gongs.get(key), dict):
            desc = str(raw.get(key) or "")
        else:
            g = gongs.get(key) or {}
            stars = "、".join(g.get("主星") or []) if isinstance(g, dict) else ""
            desc = f"{(g.get('地支') if isinstance(g, dict) else '') or ''} {stars}".strip()
        yao.append({"label": label, "yin": False, "mark": "宮", "desc": desc or "——"})
    return {
        "source": DISCLAIMER,
        "trigram": ming,
        "name": ju_name,
        "mean": f"紫微在{ziwei_at}。四化：{sihua_txt or '—'}",
        "yao": yao,
    }


def _cast_meihua(kw: dict[str, Any]) -> dict[str, Any]:
    import re
    from engines.meihua import cast as meihua_cast

    numbers = kw.get("numbers")
    if not isinstance(numbers, (list, tuple)) or len(numbers) < 2:
        q = str(kw.get("question") or "")
        digits = [int(x) for x in re.findall(r"\d+", q)]
        numbers = digits[:2] if len(digits) >= 2 else [3, 8]
    raw = meihua_cast(method="number", numbers=[int(numbers[0]), int(numbers[1])])
    zhu = raw.get("zhu_gua") or {}
    hu = raw.get("hu_gua") or {}
    bian = raw.get("bian_gua") or {}
    rel = (raw.get("ti_yong") or {}).get("關係") or ""
    yao = [
        {"label": "上", "yin": False, "mark": "卦", "desc": str(zhu.get("upper") or "")},
        {"label": "下", "yin": True, "mark": "卦", "desc": str(zhu.get("lower") or "")},
        {"label": "互", "yin": False, "mark": "卦", "desc": str(hu.get("name") or "")},
        {"label": "變", "yin": True, "mark": "卦", "desc": str(bian.get("name") or "")},
        {"label": "動爻", "yin": False, "mark": "動", "desc": str(raw.get("動爻") or "")},
        {"label": "警語", "yin": True, "mark": "注", "desc": DISCLAIMER},
    ]
    return {
        "source": DISCLAIMER,
        "trigram": f"{zhu.get('symbol') or ''} {zhu.get('name') or ''}".strip(),
        "name": str(zhu.get("name") or ""),
        "mean": rel,
        "yao": yao,
    }


def _gua_shell(trigram: str, name: str, mean: str, yao: list[dict]) -> dict[str, Any]:
    return {
        "source": DISCLAIMER,
        "trigram": trigram,
        "name": name,
        "mean": mean,
        "yao": yao,
    }


def _cast_qimen(kw: dict[str, Any]) -> dict[str, Any]:
    from engines.qimen import pan

    dt = _parse_dt(str(kw.get("dt_local") or "").strip())
    raw = pan(dt.year, dt.month, dt.day, dt.hour)
    fu = raw.get("值符") or {}
    shi = raw.get("值使") or {}
    trigram = str(fu.get("星") or raw.get("陰陽遁") or "")
    name = f"{raw.get('節氣') or ''}　{raw.get('陰陽遁') or ''}{raw.get('局') or ''}".strip()
    mean = f"值符{fu.get('星') or ''}落{fu.get('落宮') or ''}。值使{shi.get('門') or ''}門落{shi.get('落宮') or ''}"
    yao = [
        {"label": "節氣", "yin": False, "mark": "氣", "desc": str(raw.get("節氣") or "——")},
        {"label": "局", "yin": False, "mark": "局", "desc": f"{raw.get('陰陽遁') or ''}{raw.get('局') or ''}"},
        {"label": "值符", "yin": False, "mark": "符", "desc": f"{fu.get('星') or ''}　{fu.get('落宮') or ''}"},
        {"label": "值使", "yin": True, "mark": "使", "desc": f"{shi.get('門') or ''}　{shi.get('落宮') or ''}"},
        {"label": "日時", "yin": False, "mark": "柱", "desc": f"{raw.get('日柱') or ''}　{raw.get('時柱') or ''}"},
        {"label": "警語", "yin": True, "mark": "注", "desc": DISCLAIMER},
    ]
    return _gua_shell(trigram, name, mean, yao)


def _cast_qizheng(kw: dict[str, Any]) -> dict[str, Any]:
    from engines.qizheng import positions

    dt = _parse_dt(str(kw.get("dt_local") or "").strip())
    raw = positions(dt.year, dt.month, dt.day, dt.hour)
    seven = raw.get("七政") or {}
    four = raw.get("四餘") or {}
    colors = {
        "太陽": "#ffd9a0", "月亮": "#a8c4ff", "水星": "#9be8b8",
        "金星": "#ffb8d8", "火星": "#ff8a8a", "木星": "#c8a0ff", "土星": "#d8c8a0",
    }
    syms = {"太陽": "☉", "月亮": "☽", "水星": "☿", "金星": "♀", "火星": "♂", "木星": "♃", "土星": "♄"}
    out = []
    for i, name in enumerate(("太陽", "月亮", "水星", "金星", "火星", "木星", "土星")):
        lon = seven.get(name)
        if lon is None:
            continue
        out.append({
            "name": name,
            "sym": syms.get(name, "·"),
            "ring": (i % 4) + 1,
            "deg": float(lon) % 360,
            "color": colors.get(name, "#e8e0ff"),
            "hl": name == "太陽",
            "meaning": "",
        })
    extra = "　".join(f"{k}{v}" for k, v in four.items() if v is not None)
    return {
        "source": DISCLAIMER,
        "planets": out,
        "summary": extra or DISCLAIMER,
    }


def _cast_xingming(kw: dict[str, Any]) -> dict[str, Any]:
    from engines.xingming import wuge

    surname, given = _name_parts(kw)
    if not surname or not given:
        raise ValueError("須提供姓名")
    raw = wuge(surname, given)
    ge = raw.get("五格") or {}
    zong = ge.get("總格") or {}
    yao = []
    for label in ("天格", "人格", "地格", "外格", "總格"):
        item = ge.get(label) or {}
        yao.append({
            "label": label,
            "yin": label in ("地格", "外格", "總格"),
            "mark": "格",
            "desc": f"{item.get('數') or '—'}　{item.get('吉凶') or ''}".strip(),
        })
    yao.append({"label": "警語", "yin": True, "mark": "注", "desc": DISCLAIMER})
    return _gua_shell(
        str(zong.get("數") or surname + given),
        f"{surname}{given}",
        f"總格{zong.get('數') or '—'}（{zong.get('吉凶') or '—'}）",
        yao,
    )


def _cast_numerology(kw: dict[str, Any]) -> dict[str, Any]:
    from engines.numerology import calculate

    dt_raw = str(kw.get("dt_local") or "").strip()
    year, month, day = kw.get("year"), kw.get("month"), kw.get("day")
    if dt_raw:
        dt = _parse_dt(dt_raw)
        year, month, day = dt.year, dt.month, dt.day
    if year is None or month is None or day is None:
        raise ValueError("須提供 dt_local")
    raw = calculate(int(year), int(month), int(day), str(kw.get("name") or ""))
    life = raw.get("生命靈數") or {}
    talent = raw.get("天賦數") or {}
    yao = [
        {"label": "生命", "yin": False, "mark": "數", "desc": f"{life.get('數')}　{life.get('解讀') or ''}".strip()},
        {"label": "天賦", "yin": True, "mark": "數", "desc": f"{talent.get('數')}　{talent.get('解讀') or ''}".strip()},
        {"label": "大師", "yin": False, "mark": "注", "desc": "是" if raw.get("大師數") else "否"},
        {"label": "出生", "yin": True, "mark": "日", "desc": str((raw.get("input") or {}).get("birth") or "")},
        {"label": "警語", "yin": True, "mark": "注", "desc": DISCLAIMER},
        {"label": "名", "yin": False, "mark": "名", "desc": str((raw.get("input") or {}).get("name") or "——")},
    ]
    return _gua_shell(str(life.get("數") or ""), str(talent.get("數") or ""), str(life.get("解讀") or ""), yao)


def _cast_lenormand(seed: Any) -> dict[str, Any]:
    from engines.lenormand import draw

    raw = draw(n=3, seed=_int_or_none(seed))
    cards = []
    for i, c in enumerate(raw.get("cards") or []):
        cards.append({
            "phase": c.get("position") or (("一", "二", "三")[i] if i < 3 else str(i + 1)),
            "img": "",
            "en": c.get("name") or "",
            "desc": f"{c.get('orientation') or ''}。{c.get('meaning') or ''}".strip("。"),
            "tip": c.get("orientation") or "",
        })
    return {
        "source": DISCLAIMER,
        "cards": cards,
        "delays": [400, 1500, 2700],
        "verdict": "、".join(c.get("en") or "" for c in cards),
    }


def _cast_fusion(kw: dict[str, Any]) -> dict[str, Any]:
    from engines.fusion import zonghe

    if not str(kw.get("dt_local") or "").strip():
        raise ValueError("須提供 dt_local")
    dt = _parse_dt(str(kw.get("dt_local") or "").strip())
    raw = zonghe(
        dt,
        tz_offset_hours=float(kw.get("tz_offset_hours") or 8),
        lon=float(kw.get("lon") or 120),
        lat=float(kw.get("lat") or 22.3),
        gender=str(kw.get("gender") or "男"),
    )
    faces = raw.get("合參") or {}
    bazi = raw.get("八字摘要") or {}
    natal = raw.get("占星摘要") or {}
    yao = []
    for label in ("性格", "事業", "財運", "感情", "健康"):
        face = faces.get(label) or {}
        yao.append({
            "label": label,
            "yin": label in ("財運", "感情", "健康"),
            "mark": str(face.get("判別") or "—"),
            "desc": f"{face.get('八字') or ''}／{face.get('占星') or ''}",
        })
    yao.append({"label": "警語", "yin": True, "mark": "注", "desc": DISCLAIMER})
    sizhu = bazi.get("四柱") or {}
    trigram = str(sizhu.get("日柱") or bazi.get("格局") or "")
    name = f"日{natal.get('太陽') or ''}　月{natal.get('月亮') or ''}　升{natal.get('上升') or ''}"
    character = (faces.get("性格") or {}).get("說明") or ""
    return _gua_shell(trigram, name, f"{bazi.get('格局') or ''}。{character}".strip("。"), yao)


def _name_parts(kw: dict[str, Any]) -> tuple[str, str]:
    surname = str(kw.get("surname") or "").strip()
    given = str(kw.get("given") or "").strip()
    if surname and given:
        return surname, given
    q = str(kw.get("question") or kw.get("name") or "").strip()
    q = q.replace("　", " ").strip()
    if " " in q:
        a, b = q.split(" ", 1)
        return a.strip(), b.strip()
    if len(q) >= 2:
        return q[0], q[1:]
    return surname, given


def _parse_dt(raw: str) -> datetime:
    if not raw:
        raise ValueError("須提供 dt_local")
    try:
        return datetime.fromisoformat(raw)
    except ValueError as e:
        raise ValueError("dt_local 須為 ISO 時間") from e


def _int_or_none(v: Any) -> int | None:
    if v is None or v == "":
        return None
    return int(v)
