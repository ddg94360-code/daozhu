"""daozhu-mcp 強化測試：CONFIG 載入、匯出 CSV、健康連續天數、節氣多年份。"""
import os
import sys
from datetime import datetime

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import config
import daily
import solarterm
import weekly


@pytest.fixture(autouse=True)
def reset_config():
    """每個測試後重置 config 全域狀態，避免互相污染。"""
    yield
    config._config = None


# ---------------------------------------------------------------- CONFIG
def test_config_defaults(isolated_memory):
    cfg = config.load()
    assert cfg["currency"] == ""
    assert cfg["timezone"] == "Asia/Taipei"
    assert cfg["high_speed_threshold"] == 80
    assert config.currency_symbol() == ""


def test_config_from_yaml(isolated_memory, tmp_path, monkeypatch):
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text("daozhu:\n  currency: TWD\n  timezone: Asia/Hong_Kong\n", encoding="utf-8")
    monkeypatch.setattr(config, "_config_path", lambda: str(yaml_file))
    cfg = config.load()
    assert cfg["currency"] == "TWD"
    assert cfg["timezone"] == "Asia/Hong_Kong"
    assert config.currency_symbol() == "NT$"


def test_config_ignores_unknown_keys(isolated_memory, tmp_path, monkeypatch):
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text("daozhu:\n  currency: USD\n  unknown_key: 123\n", encoding="utf-8")
    monkeypatch.setattr(config, "_config_path", lambda: str(yaml_file))
    cfg = config.load()
    assert "unknown_key" not in cfg
    assert cfg["currency"] == "USD"


def test_config_missing_file_uses_defaults(isolated_memory, tmp_path, monkeypatch):
    monkeypatch.setattr(config, "_config_path", lambda: str(tmp_path / "no_such.yaml"))
    cfg = config.load()
    assert cfg["currency"] == ""


# ---------------------------------------------------------------- 匯出 CSV
def test_export_expenses_csv(isolated_memory):
    daily.log_expense("午餐", 150)
    daily.log_expense("買書,學費", 320)  # 含逗號 → 測轉義
    csv_text = daily.export_expenses_csv()
    lines = csv_text.strip().splitlines()
    assert lines[0] == "date,category,item,amount,currency"
    assert len(lines) == 3  # 標頭 + 2 筆
    assert '"買書,學費"' in csv_text  # 逗號欄位被引號包住
    assert "午餐" in csv_text


def test_export_empty_month(isolated_memory):
    csv_text = daily.export_expenses_csv("2030-01")
    assert csv_text.strip().splitlines() == ["date,category,item,amount,currency"]


# ---------------------------------------------------------------- 健康連續天數
def test_health_consecutive_days(isolated_memory, monkeypatch):
    import memory_store as store
    for d in ["2026-08-10T08:00:00", "2026-08-11T08:00:00"]:
        monkeypatch.setattr(store, "_wall_clock", lambda d=d: datetime.fromisoformat(d))
        r = daily.log_health(sleep_hours=7)
    assert r["consecutive_days"] == 2
    # 未達成的一天打斷連續
    monkeypatch.setattr(store, "_wall_clock", lambda: datetime.fromisoformat("2026-08-12T08:00:00"))
    daily.log_health()  # 無睡眠無運動
    assert daily._consecutive_health_days() == 0


def test_health_consecutive_requires_calendar_adjacency(isolated_memory, monkeypatch):
    """隔一天沒打卡不算連續——必須是日曆相鄰。"""
    import memory_store as store
    monkeypatch.setattr(store, "_wall_clock", lambda: datetime.fromisoformat("2026-08-10T08:00:00"))
    daily.log_health(sleep_hours=7)
    monkeypatch.setattr(store, "_wall_clock", lambda: datetime.fromisoformat("2026-08-12T08:00:00"))  # 跳過 8/11
    r = daily.log_health(sleep_hours=7)
    assert r["consecutive_days"] == 1


# ---------------------------------------------------------------- 週報 currency 欄位
def test_weekly_report_currency(isolated_memory):
    report = weekly.weekly_report()
    assert "currency" in report
    assert report["currency"] == ""  # 預設無貨幣


def test_energy_insight_respects_config_threshold(isolated_memory, monkeypatch, tmp_path):
    """精力分析門檻讀 energy_analysis_days，不是寫死 7。"""
    yaml_file = tmp_path / "config.yaml"
    yaml_file.write_text("daozhu:\n  energy_analysis_days: 3\n", encoding="utf-8")
    monkeypatch.setattr(config, "_config_path", lambda: str(yaml_file))
    config.load()
    moods = [
        {"date": "2026-08-10T09:00:00", "classification": "正向"},
        {"date": "2026-08-11T10:00:00", "classification": "中性"},
        {"date": "2026-08-12T11:00:00", "classification": "負向"},
    ]
    insight = weekly._energy_insight(moods)
    assert "數據不足" not in insight
    assert "活躍時段" in insight


# ---------------------------------------------------------------- 節氣多年份
def test_solar_term_multiple_years():
    for year in (2025, 2026, 2027):
        terms = solarterm.all_solar_terms(year)
        assert len(terms) == 24
        assert terms[0]["name"] == "小寒"
        assert terms[-1]["name"] == "冬至"


def test_solar_term_cross_year_boundary():
    # 2027-01-01 落於 2026 冬至區間，下一節氣小寒
    res = solarterm.current_solar_term(datetime(2027, 1, 1))
    assert res["current"] == "冬至"
    assert res["next"] == "小寒"
    assert res["current_season"] == "冬"


def test_solar_term_known_2026_dates():
    terms = {t["name"]: t for t in solarterm.all_solar_terms(2026)}
    assert abs(terms["立春"]["day"] - 4) <= 1
    assert abs(terms["春分"]["day"] - 20) <= 1
    assert abs(terms["夏至"]["day"] - 21) <= 1
    assert abs(terms["冬至"]["day"] - 21) <= 1
