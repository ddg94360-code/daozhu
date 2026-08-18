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
