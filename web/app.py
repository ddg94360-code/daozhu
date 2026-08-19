"""道樞本機儀表板 HTTP 入口。只聽 loopback；業務一律轉 daily/weekly/solarterm。"""
from __future__ import annotations

import os
import sys

from datetime import datetime

from collections.abc import Callable
from typing import Any

from fastapi import Body, FastAPI, HTTPException, Query, Request
from fastapi.exception_handlers import http_exception_handler, request_validation_exception_handler
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from fastapi.staticfiles import StaticFiles

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MCP = os.path.join(_REPO, "mcp")
_WEB = os.path.dirname(os.path.abspath(__file__))
_STATIC = os.path.join(_WEB, "static")
_XINJING = os.path.join(_REPO, "skills", "daozhu", "xinjing")
_XINJING_EXAMPLES = os.path.join(_XINJING, "examples")
_XINJING_MODES = ("tarot", "gua", "yuan", "chart", "fengshui", "star", "dream")


def _mcp_on_path() -> None:
    for p in (_WEB, _MCP, _XINJING):
        if p not in sys.path:
            sys.path.insert(0, p)


_mcp_on_path()

import config
import daily
import daozang
import memory_store as store
import solarterm
import weekly

import cabinet
import llm
import perception
import router
import cabinet_session
import speech
import tianji_bridge

app = FastAPI(title="道樞儀表板", docs_url=None, redoc_url=None)


@app.exception_handler(HTTPException)
async def _http_exc(request: Request, exc: HTTPException):
    return await http_exception_handler(request, exc)


@app.exception_handler(RequestValidationError)
async def _validation_exc(request: Request, exc: RequestValidationError):
    return await request_validation_exception_handler(request, exc)


@app.exception_handler(Exception)
async def _internal_error(_request: Request, _exc: Exception) -> JSONResponse:
    return JSONResponse({"error": "internal", "message": "內部錯誤"}, status_code=500)


@app.middleware("http")
async def loopback_only(request: Request, call_next: Callable) -> Any:
    host = (request.client.host if request.client else "") or ""
    if host not in {"127.0.0.1", "::1", "testclient", "localhost"}:
        return JSONResponse(
            {"error": "forbidden", "message": "僅限本機存取"},
            status_code=403,
        )
    try:
        return await call_next(request)
    except Exception:
        return JSONResponse({"error": "internal", "message": "內部錯誤"}, status_code=500)


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


def _err(code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse({"error": code, "message": message}, status_code=status)


@app.post("/api/expenses")
def api_post_expense(body: dict = Body(...)) -> Any:
    item = str(body.get("item", "")).strip()
    if not item:
        return _err("invalid", "項目不能空白", 400)
    try:
        amount = float(body.get("amount"))
    except (TypeError, ValueError):
        return _err("invalid", "金額必須是大於 0 的數字", 400)
    if amount <= 0:
        return _err("invalid", "金額必須是大於 0 的數字", 400)
    category = str(body.get("category") or "")
    return daily.log_expense(item, amount, category)


@app.post("/api/health")
def api_post_health(body: dict = Body(...)) -> Any:
    sleep = body.get("sleep_hours", 0) or 0
    try:
        sleep_f = float(sleep)
    except (TypeError, ValueError):
        return _err("invalid", "睡眠時數必須是數字", 400)
    exercise = str(body.get("exercise") or "").strip()
    water = str(body.get("water") or "").strip()
    if sleep_f <= 0 and not exercise and not water:
        return _err("invalid", "至少填一項健康紀錄", 400)
    return daily.log_health(sleep_f, exercise, water)


@app.post("/api/reminders")
def api_post_reminder(body: dict = Body(...)) -> Any:
    content = str(body.get("content", "")).strip()
    if not content:
        return _err("invalid", "提醒內容不能空白", 400)
    dt = str(body.get("datetime", "")).strip()
    try:
        datetime.fromisoformat(dt)
    except ValueError:
        return _err("invalid", "時間須為 ISO 格式", 400)
    recurring = bool(body.get("recurring", False))
    return daily.add_reminder(content, dt, recurring)


@app.post("/api/reminders/{reminder_id}/done")
def api_reminder_done(reminder_id: str) -> Any:
    res = daily.mark_reminder_done(reminder_id)
    if not res.get("matched"):
        return _err("not_found", "找不到這則提醒", 404)
    return res


@app.post("/api/shopping")
def api_post_shopping(body: dict = Body(...)) -> Any:
    item = str(body.get("item", "")).strip()
    if not item:
        return _err("invalid", "項目不能空白", 400)
    return daily.add_shopping(item)


@app.post("/api/shopping/{item_id}/check")
def api_shopping_check(item_id: str) -> Any:
    res = daily.check_shopping_by_id(item_id)
    if not res.get("matched"):
        return _err("not_found", "找不到這筆採買", 404)
    return res


@app.delete("/api/shopping/{item_id}")
def api_shopping_delete(item_id: str) -> Any:
    res = daily.remove_shopping_by_id(item_id)
    if not res.get("removed"):
        return _err("not_found", "找不到這筆採買", 404)
    return res


@app.post("/api/moods")
def api_post_mood(body: dict = Body(...)) -> Any:
    mood = str(body.get("mood", "")).strip()
    if not mood:
        return _err("invalid", "情緒不能空白", 400)
    return daily.log_mood(mood)


@app.get("/api/decisions")
def api_decisions() -> dict:
    return {"records": daily.review_decisions()[:20]}


@app.post("/api/decisions")
def api_post_decision(body: dict = Body(...)) -> Any:
    topic = str(body.get("topic", "")).strip()
    verdict = str(body.get("verdict", "")).strip()
    if not topic:
        return _err("invalid", "題目不能空白", 400)
    if not verdict:
        return _err("invalid", "裁決不能空白", 400)
    reason = str(body.get("reason") or "")
    return daily.log_decision(topic, verdict, reason)


@app.get("/api/daozang")
def api_daozang() -> dict:
    personae = {}
    for name in daozang.PERSONAE:
        personae[name] = daozang.recall(name)
    return {"personae": personae}


@app.get("/api/perception")
def api_perception() -> dict:
    return perception.infer()


@app.post("/api/cabinet/preview")
def api_cabinet_preview(body: dict = Body(...)) -> Any:
    topic = str(body.get("topic", "")).strip()
    if not topic:
        return _err("invalid", "議題不能空白", 400)
    return cabinet.preview(topic)


@app.post("/api/cabinet/convene")
def api_cabinet_convene(body: dict = Body(...)) -> Any:
    topic = str(body.get("topic", "")).strip()
    if not topic:
        return _err("invalid", "議題不能空白", 400)
    try:
        depth = speech.normalize_depth(body.get("depth"))
    except ValueError as e:
        return _err("invalid", str(e), 400)
    preview = cabinet.preview(topic)
    source = "template"
    stages = speech.fill(preview, depth)
    if llm.available():
        filled, source = _convene_with_llm(preview, stages, depth)
        stages = filled
    preview["stages"] = stages
    preview["source"] = source
    preview["depth"] = depth
    preview["disclaimer"] = (
        "模型發言，非正式會議紀錄。" if source == "llm"
        else "模板與模型混用，非正式會議紀錄。" if source == "mixed"
        else "模板發言，非正式會議紀錄。"
    )
    if body.get("persist"):
        closing = next((s.get("body") or "" for s in stages if s.get("name") == "議長結辯"), "")
        daily.log_decision(topic, "會議已開", closing[:200])
        preview["persisted"] = True
    else:
        preview["persisted"] = False
    preview["session"] = cabinet_session.save(topic, stages, depth)
    return preview


@app.post("/api/cabinet/followup")
def api_cabinet_followup(body: dict = Body(...)) -> Any:
    topic = str(body.get("topic", "")).strip()
    name = str(body.get("name", "")).strip()
    question = str(body.get("question", "")).strip()
    if not topic or not name or not question:
        return _err("invalid", "議題、內閣與追問不能空白", 400)
    try:
        speech.require_cabinet(name)
        stages = cabinet_session.stages_for_followup(body.get("stages"))
        template = speech.followup(name, topic, question, stages)
    except ValueError as e:
        return _err("invalid", str(e), 400)
    source = "template"
    text = template
    if llm.available():
        prior = speech.stage_context(name, stages)
        llm_text = llm.chat(
            [
                {"role": "system", "content": "你是道樞內閣。只輸出這一位的追問答覆，繁體中文，≤80字。不要 markdown。可引用先前發言，但不要改寫五階段原文。"},
                {"role": "user", "content": (
                    f"你是{name}。議題：{topic}。追問：{question}"
                    + (f"\n先前發言：{prior}" if prior else "")
                )},
            ],
            temperature=0.4,
        )
        if llm_text:
            text = llm_text
            source = "llm"
    return {
        "name": name,
        "topic": topic,
        "question": question,
        "body": text,
        "source": source,
        "disclaimer": (
            "模型追問，非正式會議紀錄。" if source == "llm"
            else "模板追問，非正式會議紀錄。"
        ),
    }


def _convene_with_llm(preview: dict, template_stages: list[dict], depth: str = "brief") -> tuple[list[dict], str]:
    stages = [dict(s) for s in template_stages]
    used_llm = False
    used_template = False
    names = "、".join(m.get("name", "") for m in (preview.get("core") or []) + (preview.get("adjunct") or []))
    topic = preview.get("topic") or ""
    limits = {
        "brief": "核心每人≤80字、列席≤60字、議長≤120字。",
        "deep": "核心每人兩句≤160字、列席一句並可再質詢≤80字、議長分共識／分歧／建議≤180字。",
        "flash": "只寫各抒一段合計≤150字。開題一句。列席與結辯不要寫。",
    }
    for stage in stages:
        name = stage.get("name")
        if name == "您裁決":
            continue
        if depth == "flash" and name in {"列席補充", "議長結辯"}:
            continue
        prompt = (
            f"議題：{topic}\n出席：{names}\n階段：{name}（{stage.get('who')}）\n深度：{depth}\n"
            f"用繁體中文寫這一段會議發言。{limits.get(depth, limits['brief'])}"
            "不要 markdown。"
        )
        text = llm.chat(
            [
                {"role": "system", "content": "你是道樞內閣會議書記。只輸出該階段正文。"},
                {"role": "user", "content": prompt},
            ],
            temperature=0.4,
        )
        if text:
            stage["body"] = text
            used_llm = True
        else:
            used_template = True
    if used_llm and used_template:
        return stages, "mixed"
    if used_llm:
        return stages, "llm"
    return stages, "template"


@app.post("/api/chat")
def api_chat(body: dict = Body(...)) -> Any:
    text = str(body.get("text", "")).strip()
    if not text:
        return _err("invalid", "內容不能空白", 400)
    parsed = router.parse(text)
    source = "rule"
    if parsed.get("intent") == "unknown" and llm.available():
        classified = llm.classify(text)
        if classified and classified.get("intent") not in (None, "unknown"):
            parsed = classified
            source = "llm"
    intent = str(parsed.get("intent") or "unknown")
    slots = parsed.get("slots") if isinstance(parsed.get("slots"), dict) else {}
    if intent not in router.INTENTS:
        intent = "unknown"
    if intent == "unknown":
        hint = str(slots.get("hint") or "聽不懂，請用表單或到內閣頁")
        return {"ok": False, "intent": "unknown", "source": "none" if source == "rule" else source, "reply": hint, "result": {}}
    return _dispatch_chat(intent, slots, source)


def _dispatch_chat(intent: str, slots: dict, source: str) -> dict:
    try:
        if intent == "expense":
            item = str(slots.get("item") or "").strip() or "未名項目"
            amount = float(slots.get("amount"))
            result = daily.log_expense(item, amount, str(slots.get("category") or ""))
            rec = result["record"]
            return _chat_ok(intent, source, f"已記入{rec['item']} {rec['amount']}（{rec['category']}）", result)
        if intent == "mood":
            mood = str(slots.get("mood") or "").strip()
            if not mood:
                return _chat_fail(intent, source, "情緒不能空白")
            result = daily.log_mood(mood)
            return _chat_ok(intent, source, f"已記下情緒（{result['record']['classification']}）", result)
        if intent == "shopping_add":
            item = str(slots.get("item") or "").strip()
            if not item:
                return _chat_fail(intent, source, "採買項目不能空白")
            result = daily.add_shopping(item)
            return _chat_ok(intent, source, f"已加入採買：{item}", result)
        if intent == "health":
            result = daily.log_health(
                float(slots.get("sleep_hours") or 0),
                str(slots.get("exercise") or ""),
                str(slots.get("water") or ""),
            )
            return _chat_ok(intent, source, "已打卡健康", result)
        if intent == "reminder":
            content = str(slots.get("content") or "").strip()
            dt = str(slots.get("datetime") or "").strip()
            if not content or not dt:
                return _chat_fail(intent, source, "提醒缺少內容或時間，請用表單")
            result = daily.add_reminder(content, dt, False)
            return _chat_ok(intent, source, f"已設提醒：{content}", result)
        if intent == "note":
            subject = str(slots.get("subject") or "").strip()
            content = str(slots.get("content") or "").strip()
            if not subject or not content:
                return _chat_fail(intent, source, "筆記須有科目與內容")
            result = daily.add_study_note(subject, content, int(slots.get("review_days") or 7))
            return _chat_ok(intent, source, f"已記入筆記：{subject}", result)
        if intent == "decision":
            topic = str(slots.get("topic") or "").strip()
            verdict = str(slots.get("verdict") or "").strip()
            if not topic or not verdict:
                return _chat_fail(intent, source, "裁決須有題目與結論")
            result = daily.log_decision(topic, verdict, str(slots.get("reason") or ""))
            return _chat_ok(intent, source, f"已記下裁決：{verdict}", result)
        if intent == "query_expense":
            summary = daily.month_expense_summary()
            return _chat_ok(intent, source, f"本月合計 {summary.get('currency') or ''}{summary['total']}", summary)
        if intent == "query_reminders":
            scope = str(slots.get("scope") or "due")
            recs = daily.pending_reminders() if scope == "pending" else daily.due_reminders()
            if not recs:
                reply = "沒有待辦提醒" if scope == "pending" else "沒有到期提醒"
            else:
                prefix = "待辦：" if scope == "pending" else "到期："
                reply = prefix + "、".join(r.get("content") or "" for r in recs[:8])
            return _chat_ok(intent, source, reply, {"records": recs, "scope": scope})
        if intent == "query_notes":
            recs = daily.due_study_notes()
            reply = "沒有到期筆記" if not recs else "待複習：" + "、".join(r.get("subject") or "" for r in recs[:8])
            return _chat_ok(intent, source, reply, {"records": recs})
    except (TypeError, ValueError):
        return _chat_fail(intent, source, "欄位不夠，請用表單")
    return _chat_fail(intent, source, "聽不懂，請用表單或到內閣頁")


def _chat_ok(intent: str, source: str, reply: str, result: Any) -> dict:
    return {"ok": True, "intent": intent, "source": source, "reply": reply, "result": result}


def _chat_fail(intent: str, source: str, reply: str) -> dict:
    return {"ok": False, "intent": intent, "source": source, "reply": reply, "result": {}}


@app.get("/api/xinjing/examples")
def api_xinjing_modes() -> dict:
    return {"modes": list(_XINJING_MODES)}


@app.get("/api/xinjing/examples/{mode}")
def api_xinjing_example(mode: str) -> Any:
    if mode not in _XINJING_MODES:
        return _err("not_found", "找不到這個心鏡模式", 404)
    path = os.path.join(_XINJING_EXAMPLES, f"{mode}.json")
    if not os.path.isfile(path):
        return _err("not_found", "找不到示範資料", 404)
    import json

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


@app.get("/api/xinjing/status")
def api_xinjing_status() -> dict:
    return tianji_bridge.status()


@app.post("/api/xinjing/cast")
def api_xinjing_cast(body: dict = Body(...)) -> Any:
    mode = str(body.get("mode", "")).strip()
    if mode in tianji_bridge.NARRATIVE_MODES or mode not in tianji_bridge.CAST_MODES:
        return _err("invalid", "此模式不算命", 400)
    try:
        return tianji_bridge.cast(
            mode,
            question=body.get("question"),
            seed=body.get("seed"),
            year=body.get("year"),
            gender=body.get("gender") or "男",
            dt_local=body.get("dt_local"),
            lat=body.get("lat"),
            lon=body.get("lon"),
            tz_offset_hours=body.get("tz_offset_hours"),
            numbers=body.get("numbers"),
            surname=body.get("surname"),
            given=body.get("given"),
            name=body.get("name"),
            month=body.get("month"),
            day=body.get("day"),
        )
    except RuntimeError as e:
        if str(e) == "未接天機":
            return _err("unavailable", "未接天機", 503)
        raise
    except ValueError as e:
        return _err("invalid", str(e) or "參數不正確", 400)


@app.post("/api/xinjing/render")
def api_xinjing_render(body: dict = Body(...)) -> Any:
    mode = str(body.get("mode", "")).strip()
    if mode not in _XINJING_MODES:
        return _err("invalid", "模式須為七模式之一", 400)
    data = body.get("data")
    if not isinstance(data, dict):
        return _err("invalid", "資料須為 JSON 物件", 400)
    from xinjing_render import render

    return Response(content=render(mode, data), media_type="text/html")


@app.post("/api/notes")
def api_post_note(body: dict = Body(...)) -> Any:
    subject = str(body.get("subject", "")).strip()
    content = str(body.get("content", "")).strip()
    if not subject:
        return _err("invalid", "科目不能空白", 400)
    if not content:
        return _err("invalid", "內容不能空白", 400)
    raw_days = body.get("review_days", 7)
    try:
        review_days = int(raw_days)
    except (TypeError, ValueError):
        return _err("invalid", "複習天數須為大於或等於 0 的整數", 400)
    if review_days < 0:
        return _err("invalid", "複習天數須為大於或等於 0 的整數", 400)
    return daily.add_study_note(subject, content, review_days)


@app.post("/api/notes/{note_id}/reviewed")
def api_note_reviewed(note_id: str) -> Any:
    res = daily.mark_study_note_reviewed_by_id(note_id)
    if not res.get("matched"):
        return _err("not_found", "找不到這則筆記", 404)
    return res


@app.delete("/api/notes/{note_id}")
def api_note_delete(note_id: str) -> Any:
    res = daily.delete_study_note_by_id(note_id)
    if not res.get("removed"):
        return _err("not_found", "找不到這則筆記", 404)
    return res


@app.get("/")
def index() -> FileResponse:
    return FileResponse(os.path.join(_STATIC, "index.html"))


@app.get("/cabinet")
def cabinet_page() -> FileResponse:
    return FileResponse(os.path.join(_STATIC, "cabinet.html"))


@app.get("/xinjing")
def xinjing_page() -> FileResponse:
    return FileResponse(os.path.join(_STATIC, "xinjing.html"))


app.mount("/static", StaticFiles(directory=_STATIC), name="static")
