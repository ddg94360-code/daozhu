def test_healthz_ok(client):
    r = client.get("/api/healthz")
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_rejects_non_loopback(isolated_memory):
    # Starlette 0.47 TestClient.get() 無 client=；改打 ASGI scope。
    import asyncio
    import json

    from app import app

    async def _call():
        scope = {
            "type": "http",
            "asgi": {"version": "3.0"},
            "http_version": "1.1",
            "method": "GET",
            "scheme": "http",
            "path": "/api/healthz",
            "raw_path": b"/api/healthz",
            "query_string": b"",
            "headers": [],
            "client": ("203.0.113.10", 50000),
            "server": ("127.0.0.1", 8765),
        }
        messages = []

        async def receive():
            return {"type": "http.request", "body": b"", "more_body": False}

        async def send(message):
            messages.append(message)

        await app(scope, receive, send)
        start = next(m for m in messages if m["type"] == "http.response.start")
        assert start["status"] == 403
        raw = b"".join(
            m.get("body", b"") for m in messages if m["type"] == "http.response.body"
        )
        body = json.loads(raw)
        assert body["error"] == "forbidden"
        assert "本機" in body["message"]

    asyncio.run(_call())


from datetime import datetime

import daily
import memory_store as store


def test_overview_empty_ok(client, isolated_memory):
    r = client.get("/api/overview")
    assert r.status_code == 200
    body = r.json()
    assert body["status"]["status"] == "ok"
    assert body["report"]["expense_total"] == 0
    assert "current" in body["solar_term"]
    assert body["memory_dir"] == str(isolated_memory)


def test_expenses_lists_recent_after_log(client, isolated_memory):
    daily.log_expense("午餐", 150, "飲食")
    r = client.get("/api/expenses")
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["total"] == 150
    assert body["summary"]["by_category"]["飲食"] == 150
    assert len(body["recent"]) == 1
    assert body["recent"][0]["item"] == "午餐"


def test_reminders_mark_due(client, isolated_memory, monkeypatch):
    monkeypatch.setattr(store, "_wall_clock", lambda: datetime.fromisoformat("2026-08-18T12:00:00"))
    daily.add_reminder("過期", "2026-08-18T10:00:00")
    daily.add_reminder("未來", "2026-08-19T10:00:00")
    r = client.get("/api/reminders")
    assert r.status_code == 200
    recs = {x["content"]: x for x in r.json()["records"]}
    assert recs["過期"]["due"] is True
    assert recs["未來"]["due"] is False


def test_notes_create_review_delete(client, isolated_memory, monkeypatch):
    monkeypatch.setattr(store, "_wall_clock", lambda: datetime.fromisoformat("2026-08-18T12:00:00"))
    r = client.post("/api/notes", json={"subject": "物理", "content": "熵增", "review_days": 0})
    assert r.status_code == 200
    rec = r.json()["record"]
    assert rec["id"]
    assert rec["subject"] == "物理"
    listed = client.get("/api/notes").json()
    assert len(listed["due"]) == 1
    assert listed["due"][0]["id"] == rec["id"]
    done = client.post(f"/api/notes/{rec['id']}/reviewed")
    assert done.status_code == 200
    assert client.get("/api/notes").json()["due"] == []
    deleted = client.delete(f"/api/notes/{rec['id']}")
    assert deleted.status_code == 200
    assert client.get("/api/notes").json()["recent"] == []


def test_notes_missing_id_404(client):
    assert client.post("/api/notes/deadbeef/reviewed").status_code == 404
    assert client.delete("/api/notes/deadbeef").status_code == 404


def test_notes_blank_400(client):
    r = client.post("/api/notes", json={"subject": "", "content": "x"})
    assert r.status_code == 400
    assert r.json()["error"] == "invalid"


def test_decision_roundtrip(client, isolated_memory):
    r = client.post("/api/decisions", json={"topic": "是否接專案", "verdict": "接", "reason": "時程可行"})
    assert r.status_code == 200
    assert r.json()["record"]["verdict"] == "接"
    listed = client.get("/api/decisions").json()["records"]
    assert listed[0]["topic"] == "是否接專案"


def test_decision_blank_400(client):
    r = client.post("/api/decisions", json={"topic": "x", "verdict": ""})
    assert r.status_code == 400


def test_daozang_empty_ok(client, isolated_memory):
    r = client.get("/api/daozang")
    assert r.status_code == 200
    body = r.json()["personae"]
    assert set(body) == {"daoist", "strategist", "legalist", "confucian"}
    assert body["daoist"]["records"] == []


def test_perception_empty_disclaimer(client, isolated_memory):
    r = client.get("/api/perception")
    assert r.status_code == 200
    body = r.json()
    assert "真實對話" in body["disclaimer"]
    keys = [x["key"] for x in body["layers"]]
    assert keys == ["emotion", "task", "interpersonal", "complexity", "concise", "tone", "energy"]
    assert all(x["on"] is False for x in body["layers"])


def test_perception_lights_from_memory(client, isolated_memory, monkeypatch):
    monkeypatch.setattr(store, "_wall_clock", lambda: datetime.fromisoformat("2026-08-18T12:00:00"))
    daily.log_mood("今天好煩")
    daily.add_study_note("物理", "熵增", review_days=0)
    daily.log_decision("是否接", "接")
    body = client.get("/api/perception").json()
    by = {x["key"]: x for x in body["layers"]}
    assert by["emotion"]["on"] is True
    assert "負向" in by["emotion"]["hint"]
    assert by["task"]["on"] is True
    assert by["complexity"]["on"] is True
    assert by["interpersonal"]["on"] is False


def test_cabinet_preview_interpersonal(client):
    r = client.post("/api/cabinet/preview", json={"topic": "組員不做事該怎麼講"})
    assert r.status_code == 200
    body = r.json()
    assert body["core"][0]["name"] == "儒家"
    assert body["adjunct"][0]["name"] == "縱橫家"
    assert len(body["stages"]) == 5
    assert body["stages"][0]["body"] == ""


def test_cabinet_preview_default(client):
    r = client.post("/api/cabinet/preview", json={"topic": "隨便想一件事"})
    assert r.status_code == 200
    names = [x["name"] for x in r.json()["core"]]
    assert names == ["儒家", "法家", "道家"]


def test_cabinet_preview_blank_400(client):
    r = client.post("/api/cabinet/preview", json={"topic": "  "})
    assert r.status_code == 400


def test_xinjing_example_and_render(client):
    modes = client.get("/api/xinjing/examples")
    assert modes.status_code == 200
    assert "tarot" in modes.json()["modes"]
    ex = client.get("/api/xinjing/examples/tarot")
    assert ex.status_code == 200
    assert "cards" in ex.json()
    rendered = client.post("/api/xinjing/render", json={"mode": "tarot", "data": ex.json()})
    assert rendered.status_code == 200
    assert "text/html" in rendered.headers["content-type"]
    assert "萬象心鏡" in rendered.text


def test_xinjing_bad_payload(client):
    bad_mode = client.post("/api/xinjing/render", json={"mode": "nope", "data": {}})
    assert bad_mode.status_code == 400
    bad_data = client.post("/api/xinjing/render", json={"mode": "tarot", "data": []})
    assert bad_data.status_code == 400
    missing = client.get("/api/xinjing/examples/nope")
    assert missing.status_code == 404


def test_missing_body_still_422(client):
    r = client.post("/api/notes")
    assert r.status_code == 422


def test_internal_error_shape(client, monkeypatch):
    import app as webapp

    def boom():
        raise RuntimeError("secret-stack")

    monkeypatch.setattr(webapp.weekly, "status", boom)
    r = client.get("/api/overview")
    assert r.status_code == 500
    body = r.json()
    assert body["error"] == "internal"
    assert body["message"] == "內部錯誤"
    assert "secret-stack" not in r.text


def test_cabinet_and_xinjing_pages(client):
    cab = client.get("/cabinet")
    xin = client.get("/xinjing")
    assert cab.status_code == 200
    assert xin.status_code == 200
    assert "道樞" in cab.text
    assert "道樞" in xin.text
    assert "text/html" in cab.headers["content-type"]


def test_expenses_csv(client, isolated_memory):
    daily.log_expense("午餐", 150)
    r = client.get("/api/expenses.csv")
    assert r.status_code == 200
    assert "text/csv" in r.headers["content-type"]
    assert "午餐" in r.text


def test_post_expense_then_get(client, isolated_memory):
    r = client.post("/api/expenses", json={"item": "午餐", "amount": 80})
    assert r.status_code == 200
    assert r.json()["record"]["amount"] == 80
    listed = client.get("/api/expenses").json()
    assert listed["summary"]["total"] == 80


def test_post_expense_bad_amount(client):
    r = client.post("/api/expenses", json={"item": "午餐", "amount": 0})
    assert r.status_code == 400
    assert r.json()["error"] == "invalid"
    assert "金額" in r.json()["message"]


def test_mark_missing_reminder_404(client):
    r = client.post("/api/reminders/deadbeef/done")
    assert r.status_code == 404
    assert r.json()["error"] == "not_found"


def test_shopping_check_by_id_not_fuzzy(client, isolated_memory):
    a = client.post("/api/shopping", json={"item": "咖啡"}).json()["record"]
    b = client.post("/api/shopping", json={"item": "咖啡"}).json()["record"]
    r = client.post(f"/api/shopping/{a['id']}/check")
    assert r.status_code == 200
    recs = {x["id"]: x for x in client.get("/api/shopping").json()["records"]}
    assert recs[a["id"]]["checked"] is True
    assert recs[b["id"]]["checked"] is False


def test_delete_shopping_404(client):
    r = client.delete("/api/shopping/nope")
    assert r.status_code == 404


def test_health_requires_one_field(client):
    r = client.post("/api/health", json={})
    assert r.status_code == 400
    assert r.json()["error"] == "invalid"


def test_mood_roundtrip(client, isolated_memory):
    r = client.post("/api/moods", json={"mood": "今天好煩"})
    assert r.status_code == 200
    assert r.json()["record"]["classification"] == "負向"
    listed = client.get("/api/moods").json()["records"]
    assert listed[0]["mood"] == "今天好煩"


def test_index_html(client):
    r = client.get("/")
    assert r.status_code == 200
    assert "text/html" in r.headers["content-type"]
    assert "道樞" in r.text


def test_static_assets(client):
    js = client.get("/static/app.js")
    css = client.get("/static/app.css")
    assert js.status_code == 200
    assert css.status_code == 200
    assert "javascript" in js.headers.get("content-type", "") or js.text.startswith("const $")
    assert "refreshAll" in js.text


def test_loopback_ignores_x_forwarded_for(client):
    r = client.get("/api/healthz", headers={"X-Forwarded-For": "8.8.8.8"})
    assert r.status_code == 200
    assert r.json() == {"ok": True}


def test_expenses_other_month_uses_app_summary(client, isolated_memory):
    daily.log_expense("午餐", 150, "飲食")
    r = client.get("/api/expenses", params={"month": "1999-01"})
    assert r.status_code == 200
    body = r.json()
    assert body["summary"]["month"] == "1999-01"
    assert body["summary"]["total"] == 0
    assert body["recent"] == []


def test_health_and_moods_and_shopping_lists(client, isolated_memory):
    daily.log_health(sleep_hours=7)
    daily.log_mood("平靜")
    daily.add_shopping("牛奶")
    assert client.get("/api/health").status_code == 200
    assert len(client.get("/api/health").json()["records"]) == 1
    assert client.get("/api/moods").json()["records"][0]["mood"] == "平靜"
    assert client.get("/api/shopping").json()["records"][0]["item"] == "牛奶"
    clamped = client.get("/api/health", params={"limit": 1})
    assert len(clamped.json()["records"]) == 1
