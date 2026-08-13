"""daozhu-mcp 二期測試：道藏、陰陽時令。

記憶庫隔離 fixture 見 conftest.py。
"""
from datetime import datetime

import daozang
import solarterm


# ---------------------------------------------------------------- 道藏
def test_daozang_store_recall(isolated_memory):
    r = daozang.store("daoist", "順勢而行，先做最簡單的部分", "天之道", "好焦慮")
    assert r["total"] == 1
    recs = daozang.recall("daoist")
    assert recs["count"] == 1
    assert recs["records"][0]["classify"] == "天之道"


def test_daozang_classify_filter(isolated_memory):
    r_bad = daozang.store("strategist", "揣情先行", "揣情", "怎麼談判")  # 錯誤 classify → error
    assert "error" in r_bad
    ok = daozang.store("strategist", "飛鉗鎖利", "攬", "怎麼談判")
    assert "error" not in ok
    recs = daozang.recall("strategist", classify="攬")
    assert recs["count"] == 1


def test_daozang_invalid_persona(isolated_memory):
    assert "error" in daozang.store("mohist", "x", "合")
    assert "error" in daozang.recall("unknown")


# ---------------------------------------------------------------- 陰陽時令
def test_all_solar_terms_count():
    terms = solarterm.all_solar_terms(2026)
    assert len(terms) == 24
    assert terms[0]["name"] == "小寒"
    assert terms[-1]["name"] == "冬至"
    # 季節映射：立春屬春、夏至屬夏
    by_name = {t["name"]: t for t in terms}
    assert by_name["立春"]["season"] == "春"
    assert by_name["夏至"]["season"] == "夏"
    assert by_name["秋分"]["season"] == "秋"
    assert by_name["冬至"]["season"] == "冬"


def test_solar_term_2026_known_dates():
    terms = solarterm.all_solar_terms(2026)
    by_name = {t["name"]: t for t in terms}
    # 壽星公式算出之近似日期（允許 ±1 天）
    assert abs(by_name["立春"]["day"] - 4) <= 1
    assert abs(by_name["春分"]["day"] - 20) <= 1
    assert abs(by_name["夏至"]["day"] - 21) <= 1
    assert abs(by_name["冬至"]["day"] - 21) <= 1


def test_solar_term_near_transition():
    # 春分前一天（2026-03-19）→ 臨近轉換
    res = solarterm.current_solar_term(datetime(2026, 3, 19))
    assert res["near_transition"] is True
    assert res["next"] == "春分"
    # 立秋當日（2026-08-07）→ 臨近
    res2 = solarterm.current_solar_term(datetime(2026, 8, 7))
    assert res2["near_transition"] is True
    assert res2["current"] == "立秋"
    assert "收斂" in res2["guide"]


def test_solar_term_mid_season_not_transition():
    # 夏至與小暑中間（2026-06-28）→ 不臨近轉換
    res = solarterm.current_solar_term(datetime(2026, 6, 28))
    assert res["near_transition"] is False
    assert res["current"] == "夏至"
