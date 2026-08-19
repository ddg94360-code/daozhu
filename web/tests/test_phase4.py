"""第四期：會議三檔＋追問、心鏡計算模式、桌面殼、側欄骨架。"""
import importlib
import json
import os
import sys

import speech
import tianji_bridge


def test_convene_flash_collapses_stages(client):
    r = client.post(
        "/api/cabinet/convene",
        json={"topic": "該不該接這個專案", "depth": "flash"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["depth"] == "flash"
    assert body["source"] == "template"
    by_name = {s["name"]: s["body"] for s in body["stages"]}
    assert by_name["開題"]
    assert by_name["各抒己見"]
    assert "即時共識" in by_name["列席補充"]
    assert "即時共識" in by_name["議長結辯"]
    assert "persist" in by_name["您裁決"] or "決策" in by_name["您裁決"]


def test_convene_invalid_depth_400(client):
    r = client.post(
        "/api/cabinet/convene",
        json={"topic": "該不該接", "depth": "nuclear"},
    )
    assert r.status_code == 400
    assert r.json()["error"] == "invalid"
    assert "深度" in r.json()["message"]


def test_convene_default_depth_is_brief(client):
    r = client.post("/api/cabinet/convene", json={"topic": "組員不做事該怎麼講"})
    assert r.status_code == 200
    assert r.json()["depth"] == "brief"
    assert all(s["body"] for s in r.json()["stages"])


def test_preview_still_empty_bodies(client):
    r = client.post("/api/cabinet/preview", json={"topic": "組員不做事該怎麼講"})
    assert r.status_code == 200
    assert all(s["body"] == "" for s in r.json()["stages"])
    assert "depth" not in r.json()


def test_followup_template(client):
    r = client.post(
        "/api/cabinet/followup",
        json={"topic": "組員不做事該怎麼講", "name": "儒家", "question": "先說哪一句"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["name"] == "儒家"
    assert body["source"] == "template"
    assert body["body"]
    assert "非正式" in body["disclaimer"]


def test_followup_unknown_name_400(client):
    r = client.post(
        "/api/cabinet/followup",
        json={"topic": "題", "name": "陰陽家", "question": "？"},
    )
    assert r.status_code == 400
    assert r.json()["error"] == "invalid"
    assert "內閣" in r.json()["message"]


def test_followup_blank_400(client):
    assert client.post(
        "/api/cabinet/followup",
        json={"topic": "", "name": "儒家", "question": "問"},
    ).status_code == 400
    assert client.post("/api/cabinet/followup").status_code == 422


def test_speech_followup_does_not_need_preview():
    text = speech.followup("法家", "該不該加班", "成本怎麼算")
    assert "法家" in text
    assert "該不該加班" in text


def test_followup_uses_stage_context(client):
    stages = [
        {"name": "各抒己見", "body": "【儒家·主】先正名，再開口。"},
        {"name": "議長結辯", "body": "先定名分與成本。"},
    ]
    r = client.post(
        "/api/cabinet/followup",
        json={
            "topic": "組員不做事該怎麼講",
            "name": "儒家",
            "question": "先說哪一句",
            "stages": stages,
        },
    )
    assert r.status_code == 200
    body = r.json()
    assert "正名" in body["body"] or "名分" in body["body"]
    assert body["source"] == "template"


def test_followup_without_stages_still_works(client):
    r = client.post(
        "/api/cabinet/followup",
        json={"topic": "組員不做事該怎麼講", "name": "儒家", "question": "先說哪一句"},
    )
    assert r.status_code == 200
    assert r.json()["body"]
    assert "非正式" in r.json()["disclaimer"]


def test_xinjing_status_lists_calc_and_narrative(client, monkeypatch):
    monkeypatch.delenv("DAOZHU_TIANJI_DIR", raising=False)
    body = client.get("/api/xinjing/status").json()
    for mode in (
        "tarot", "gua", "fengshui", "chart", "bazi", "ziwei", "meihua",
        "qimen", "qizheng", "xingming", "numerology", "lenormand", "fusion",
    ):
        assert mode in body["modes"]
    assert "dream" in body["narrative"]
    assert "yuan" in body["narrative"]
    assert "star" in body["narrative"]
    assert body["tianji"] is False


def test_xinjing_cast_narrative_400(client):
    for mode in ("dream", "yuan", "star"):
        r = client.post("/api/xinjing/cast", json={"mode": mode})
        assert r.status_code == 400
        assert "不算命" in r.json()["message"]


def test_xinjing_cast_fake_bazi(client, tmp_path, monkeypatch):
    engines = tmp_path / "engines"
    engines.mkdir()
    (engines / "__init__.py").write_text("", encoding="utf-8")
    (engines / "tarot.py").write_text("def draw(**kw): return {'cards': []}\n", encoding="utf-8")
    (engines / "bazi.py").write_text(
        "class BirthInput:\n"
        "    def __init__(self, dt_local, **kw):\n"
        "        self.dt_local = dt_local\n"
        "def paipan(b, include=None):\n"
        "    return {\n"
        "        'sizhu': {\n"
        "            '年柱': {'ganzhi': '甲子'},\n"
        "            '月柱': {'ganzhi': '丙寅'},\n"
        "            '日柱': {'ganzhi': '戊辰'},\n"
        "            '時柱': {'ganzhi': '庚午'},\n"
        "        },\n"
        "        'geju': {'格': '正官格'},\n"
        "        'yongshen': {'說明': '身弱喜印'},\n"
        "        'dayun': {'步數': [{'干支': '辛未'}]},\n"
        "    }\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DAOZHU_TIANJI_DIR", str(tmp_path))
    for key in list(sys.modules):
        if key == "engines" or key.startswith("engines."):
            del sys.modules[key]
    r = client.post(
        "/api/xinjing/cast",
        json={"mode": "bazi", "dt_local": "1990-05-15T08:00:00"},
    )
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "bazi"
    assert body["data"]["trigram"]
    assert "戊辰" in body["data"]["trigram"] or "戊辰" in body["data"]["name"]
    assert "命理僅供參考" in body["disclaimer"]


def test_xinjing_cast_bazi_needs_dt(client, tmp_path, monkeypatch):
    engines = tmp_path / "engines"
    engines.mkdir()
    (engines / "__init__.py").write_text("", encoding="utf-8")
    (engines / "tarot.py").write_text("def draw(**kw): return {'cards': []}\n", encoding="utf-8")
    monkeypatch.setenv("DAOZHU_TIANJI_DIR", str(tmp_path))
    for key in list(sys.modules):
        if key == "engines" or key.startswith("engines."):
            del sys.modules[key]
    r = client.post("/api/xinjing/cast", json={"mode": "bazi"})
    assert r.status_code == 400
    assert "dt_local" in r.json()["message"]


def test_desktop_module_has_main():
    from web import desktop

    assert callable(desktop.main)


def test_extension_sidebar_skeleton():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    pkg_path = os.path.join(root, "extension", "package.json")
    js_path = os.path.join(root, "extension", "extension.js")
    assert os.path.isfile(pkg_path)
    assert os.path.isfile(js_path)
    pkg = json.loads(open(pkg_path, encoding="utf-8").read())
    views = pkg["contributes"]["views"]
    ids = [v["id"] for group in views.values() for v in group]
    assert "daozhu.sidebar" in ids
    js = open(js_path, encoding="utf-8").read()
    assert "127.0.0.1:8765" in js
    assert "localhost" not in js


def test_cabinet_page_has_depth_and_followup(client):
    html = client.get("/cabinet").text
    assert "cabinet-depth" in html
    assert "追問" in html
    js = client.get("/static/cabinet.js").text
    assert "/api/cabinet/followup" in js
    assert "cabinet-depth" in js


def test_xinjing_js_reads_dt_local_from_json(client):
    js = client.get("/static/xinjing.js").text
    assert "parsed.dt_local" in js


def test_xinjing_cast_fake_lenormand(client, tmp_path, monkeypatch):
    engines = tmp_path / "engines"
    engines.mkdir()
    (engines / "__init__.py").write_text("", encoding="utf-8")
    (engines / "tarot.py").write_text("def draw(**kw): return {'cards': []}\n", encoding="utf-8")
    (engines / "lenormand.py").write_text(
        "def draw(n=3, seed=None):\n"
        "    return {'cards': [\n"
        "        {'name': '騎士', 'position': '一', 'orientation': '正位', 'meaning': '消息'},\n"
        "        {'name': '心', 'position': '二', 'orientation': '正位', 'meaning': '感情'},\n"
        "        {'name': '錨', 'position': '三', 'orientation': '逆位', 'meaning': '動搖'},\n"
        "    ]}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DAOZHU_TIANJI_DIR", str(tmp_path))
    for key in list(sys.modules):
        if key == "engines" or key.startswith("engines."):
            del sys.modules[key]
    r = client.post("/api/xinjing/cast", json={"mode": "lenormand", "seed": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "lenormand"
    assert len(body["data"]["cards"]) == 3
    assert "命理僅供參考" in body["disclaimer"]


def test_xinjing_cast_xingming_needs_name(client, tmp_path, monkeypatch):
    engines = tmp_path / "engines"
    engines.mkdir()
    (engines / "__init__.py").write_text("", encoding="utf-8")
    (engines / "tarot.py").write_text("def draw(**kw): return {'cards': []}\n", encoding="utf-8")
    monkeypatch.setenv("DAOZHU_TIANJI_DIR", str(tmp_path))
    for key in list(sys.modules):
        if key == "engines" or key.startswith("engines."):
            del sys.modules[key]
    r = client.post("/api/xinjing/cast", json={"mode": "xingming"})
    assert r.status_code == 400
    assert "姓名" in r.json()["message"] or "surname" in r.json()["message"]


def test_xinjing_cast_fake_qimen(client, tmp_path, monkeypatch):
    engines = tmp_path / "engines"
    engines.mkdir()
    (engines / "__init__.py").write_text("", encoding="utf-8")
    (engines / "tarot.py").write_text("def draw(**kw): return {'cards': []}\n", encoding="utf-8")
    (engines / "qimen.py").write_text(
        "def pan(year, month, day, hour=0, **kw):\n"
        "    return {\n"
        "        '陰陽遁': '陽遁', '局': '1局', '節氣': '立春',\n"
        "        '值符': {'星': '天蓬', '落宮': '坎'},\n"
        "        '值使': {'門': '休', '落宮': '坎'},\n"
        "        '九星': {'坎宮': '天蓬'},\n"
        "    }\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DAOZHU_TIANJI_DIR", str(tmp_path))
    for key in list(sys.modules):
        if key == "engines" or key.startswith("engines."):
            del sys.modules[key]
    r = client.post("/api/xinjing/cast", json={"mode": "qimen", "dt_local": "1990-05-15T08:00:00"})
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "qimen"
    assert body["data"]["trigram"]
    assert "命理僅供參考" in body["disclaimer"]


def test_cabinet_js_sends_followup_stages(client):
    js = client.get("/static/cabinet.js").text
    assert "stages:" in js or "stages :" in js
    assert "lastStages" in js
