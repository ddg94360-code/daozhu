"""道樞本機儀表板 HTTP 入口。只聽 loopback；業務一律轉 daily/weekly/solarterm。"""
from __future__ import annotations

import os
import sys

from fastapi import FastAPI, Query, Request
from fastapi.responses import JSONResponse, Response
from fastapi.staticfiles import StaticFiles

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MCP = os.path.join(_REPO, "mcp")
_STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


def _mcp_on_path() -> None:
    if _MCP not in sys.path:
        sys.path.insert(0, _MCP)


_mcp_on_path()

import config
import daily
import memory_store as store
import solarterm
import weekly

app = FastAPI(title="道樞儀表板", docs_url=None, redoc_url=None)


@app.middleware("http")
async def loopback_only(request: Request, call_next):
    host = (request.client.host if request.client else "") or ""
    if host not in {"127.0.0.1", "::1", "testclient", "localhost"}:
        return JSONResponse(
            {"error": "forbidden", "message": "僅限本機存取"},
            status_code=403,
        )
    return await call_next(request)


def _month_summary(month: str) -> dict:
    recs = [r for r in store.all_records("expenses") if r.get("date", "").startswith(month)]
    cats: dict[str, float] = {}
    for r in recs:
        cat = r.get("category", "其他")
        cats[cat] = cats.get(cat, 0) + r["amount"]
    return {
        "month": month,
        "total": round(sum(cats.values()), 2),
        "by_category": {k: round(v, 2) for k, v in cats.items()},
        "currency": config.currency_symbol(),
    }


def _recent(name: str, limit: int) -> list:
    recs = store.all_records(name)
    recs = list(reversed(recs))
    return recs[: max(1, min(limit, 100))]


@app.get("/api/healthz")
def healthz() -> dict:
    return {"ok": True}


@app.get("/api/overview")
def api_overview() -> dict:
    return {
        "status": weekly.status(),
        "report": weekly.weekly_report(),
        "solar_term": solarterm.current_solar_term(),
        "memory_dir": store.base_dir(),
    }


@app.get("/api/expenses")
def api_expenses(month: str = "") -> dict:
    month = month or store.now()[:7]
    if month == store.now()[:7]:
        summary = daily.month_expense_summary()
    else:
        summary = _month_summary(month)
    recs = [r for r in store.all_records("expenses") if r.get("date", "").startswith(month)]
    recs = list(reversed(recs))[:15]
    return {"summary": summary, "recent": recs}


@app.get("/api/health")
def api_health(limit: int = Query(10, ge=1, le=100)) -> dict:
    return {"records": _recent("health", limit)}


@app.get("/api/reminders")
def api_reminders() -> dict:
    now = store.now()
    recs = []
    for r in daily.pending_reminders():
        recs.append({**r, "due": r.get("datetime", "") <= now})
    return {"records": recs}


@app.get("/api/shopping")
def api_shopping() -> dict:
    return {"records": daily.list_shopping()}


@app.get("/api/moods")
def api_moods(limit: int = Query(15, ge=1, le=100)) -> dict:
    return {"records": _recent("mood_log", limit)}


@app.get("/api/notes")
def api_notes() -> dict:
    due = daily.due_study_notes()
    due_keys = {(r.get("date"), r.get("subject"), r.get("original")) for r in due}
    recent = [
        r for r in daily.list_study_notes()
        if (r.get("date"), r.get("subject"), r.get("original")) not in due_keys
    ]
    return {"due": due, "recent": recent}


@app.get("/api/expenses.csv")
def api_expenses_csv(month: str = "") -> Response:
    return Response(
        content=daily.export_expenses_csv(month),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="expenses.csv"'},
    )


# 靜態目錄在 Task 5 才放 index.html；此處若目錄尚無檔案，先不要 mount 以免測試炸。
# Task 5 再加：if os.path.isdir(_STATIC): app.mount("/", StaticFiles(directory=_STATIC, html=True), name="static")
