"""第三期：聊天窗、真會議、心鏡外掛 tianji。"""
from datetime import datetime

import daily
import memory_store as store
import router
import speech
import tianji_bridge


def test_router_expense_and_mood():
    exp = router.parse("午餐吃了 150")
    assert exp["intent"] == "expense"
    assert exp["slots"]["amount"] == 150
    assert "午餐" in exp["slots"]["item"]
    mood = router.parse("今天好煩")
    assert mood["intent"] == "mood"
    assert mood["slots"]["mood"] == "今天好煩"


def test_router_unknown():
    assert router.parse("量子力學是什麼")["intent"] == "unknown"
    assert router.parse("")["intent"] == "unknown"


def test_router_reminder_query_scope():
    due = router.parse("到期提醒")
    assert due["intent"] == "query_reminders"
    assert due["slots"].get("scope") == "due"
    pending = router.parse("待辦提醒")
    assert pending["intent"] == "query_reminders"
    assert pending["slots"].get("scope") == "pending"
    what = router.parse("有什麼待辦")
    assert what["intent"] == "query_reminders"
    assert what["slots"].get("scope") == "pending"


def test_router_generic_hao_is_not_mood():
    """「好」在 daily.POSITIVE 裡，但不能讓聊天把寒暄當情緒。"""
    assert router.parse("好")["intent"] == "unknown"
    assert router.parse("好的")["intent"] == "unknown"
    assert router.parse("我很好")["intent"] == "unknown"
    assert router.parse("今天好煩")["intent"] == "mood"
    assert router.parse("今天好開心")["intent"] == "mood"


def test_chat_expense_writes(client, isolated_memory):
    r = client.post("/api/chat", json={"text": "午餐吃了 150"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is True
    assert body["intent"] == "expense"
    assert body["source"] == "rule"
    assert "150" in body["reply"]
    listed = client.get("/api/expenses").json()
    assert listed["summary"]["total"] == 150


def test_chat_mood_writes(client, isolated_memory):
    r = client.post("/api/chat", json={"text": "今天好煩"})
    assert r.status_code == 200
    assert r.json()["ok"] is True
    assert r.json()["intent"] == "mood"
    assert client.get("/api/moods").json()["records"][0]["classification"] == "負向"


def test_chat_blank_400(client):
    r = client.post("/api/chat", json={"text": "  "})
    assert r.status_code == 400
    assert r.json()["error"] == "invalid"


def test_chat_unknown_200(client, isolated_memory, monkeypatch):
    monkeypatch.delenv("DAOZHU_LLM_API_KEY", raising=False)
    r = client.post("/api/chat", json={"text": "量子力學是什麼"})
    assert r.status_code == 200
    body = r.json()
    assert body["ok"] is False
    assert body["intent"] == "unknown"
    assert "聽不懂" in body["reply"] or "表單" in body["reply"]


def test_chat_missing_body_422(client):
    assert client.post("/api/chat").status_code == 422


def test_chat_note_and_query(client, isolated_memory, monkeypatch):
    monkeypatch.setattr(store, "_wall_clock", lambda: datetime.fromisoformat("2026-08-18T12:00:00"))
    added = daily.add_study_note("物理", "熵增", 0)
    assert added["record"]["subject"] == "物理"
    parsed = router.parse("記 物理：熵增")
    assert parsed["intent"] == "note"
    q = client.post("/api/chat", json={"text": "待複習"})
    assert q.json()["ok"] is True
    assert "物理" in q.json()["reply"]


def test_chat_query_pending_vs_due_reminders(client, isolated_memory, monkeypatch):
    monkeypatch.setattr(store, "_wall_clock", lambda: datetime.fromisoformat("2026-08-18T12:00:00"))
    daily.add_reminder("過期", "2026-08-18T10:00:00")
    daily.add_reminder("未來", "2026-08-19T10:00:00")
    due = client.post("/api/chat", json={"text": "到期提醒"}).json()
    assert due["ok"] is True
    assert "過期" in due["reply"]
    assert "未來" not in due["reply"]
    pending = client.post("/api/chat", json={"text": "待辦提醒"}).json()
    assert pending["ok"] is True
    assert "過期" in pending["reply"]
    assert "未來" in pending["reply"]


def test_convene_fills_bodies(client):
    preview = client.post("/api/cabinet/preview", json={"topic": "組員不做事該怎麼講"}).json()
    assert preview["stages"][0]["body"] == ""
    r = client.post("/api/cabinet/convene", json={"topic": "組員不做事該怎麼講"})
    assert r.status_code == 200
    body = r.json()
    assert body["source"] == "template"
    assert len(body["stages"]) == 5
    assert all(s["body"] for s in body["stages"])
    assert "非正式" in body["disclaimer"]


def test_convene_persist_logs_decision(client, isolated_memory):
    r = client.post("/api/cabinet/convene", json={"topic": "該不該接", "persist": True})
    assert r.status_code == 200
    assert r.json()["persisted"] is True
    recs = client.get("/api/decisions").json()["records"]
    assert recs[0]["verdict"] == "會議已開"
    assert recs[0]["topic"] == "該不該接"


def test_convene_blank_400(client):
    assert client.post("/api/cabinet/convene", json={"topic": ""}).status_code == 400


def test_speech_fill_does_not_mutate():
    preview = {
        "topic": "題",
        "core": [{"name": "儒家", "role": "主"}],
        "adjunct": [],
        "stages": [
            {"name": "開題", "who": "議長", "body": ""},
            {"name": "各抒己見", "who": "核心內閣", "body": ""},
            {"name": "列席補充", "who": "列席內閣", "body": ""},
            {"name": "議長結辯", "who": "議長", "body": ""},
            {"name": "您裁決", "who": "你", "body": ""},
        ],
    }
    filled = speech.fill(preview)
    assert preview["stages"][0]["body"] == ""
    assert filled[0]["body"]


def test_xinjing_status_default_unplugged(client, monkeypatch):
    monkeypatch.delenv("DAOZHU_TIANJI_DIR", raising=False)
    r = client.get("/api/xinjing/status")
    assert r.status_code == 200
    body = r.json()
    assert body["tianji"] is False
    assert "tarot" in body["modes"]


def test_xinjing_cast_unplugged_503(client, monkeypatch):
    monkeypatch.delenv("DAOZHU_TIANJI_DIR", raising=False)
    r = client.post("/api/xinjing/cast", json={"mode": "tarot"})
    assert r.status_code == 503
    assert r.json()["error"] == "unavailable"
    assert "天機" in r.json()["message"]


def test_xinjing_cast_unknown_mode_400(client):
    r = client.post("/api/xinjing/cast", json={"mode": "dream"})
    assert r.status_code == 400


def test_xinjing_cast_fake_tarot(client, tmp_path, monkeypatch):
    engines = tmp_path / "engines"
    engines.mkdir()
    (engines / "__init__.py").write_text("", encoding="utf-8")
    (engines / "tarot.py").write_text(
        "def draw(spread='three', seed=None):\n"
        "    return {'cards': [\n"
        "        {'name': '愚者', 'position': '過去', 'orientation': '正位', 'meaning': '開始'},\n"
        "        {'name': '星星', 'position': '現在', 'orientation': '正位', 'meaning': '希望'},\n"
        "        {'name': '世界', 'position': '未來', 'orientation': '逆位', 'meaning': '未竟'},\n"
        "    ]}\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DAOZHU_TIANJI_DIR", str(tmp_path))
    tianji_bridge.available.cache_clear() if hasattr(tianji_bridge.available, "cache_clear") else None
    # drop a previously imported fake/real engines
    import sys
    for key in list(sys.modules):
        if key == "engines" or key.startswith("engines."):
            del sys.modules[key]
    r = client.post("/api/xinjing/cast", json={"mode": "tarot", "seed": 1})
    assert r.status_code == 200
    body = r.json()
    assert body["mode"] == "tarot"
    assert len(body["data"]["cards"]) == 3
    assert "命理僅供參考" in body["disclaimer"]


def test_chat_pages_include_chat_shell(client):
    html = client.get("/").text
    assert 'id="chat-form"' in html
    cab = client.get("/cabinet").text
    assert "開會" in cab
    xin = client.get("/xinjing").text
    assert "真抽" in xin or "真起" in xin
