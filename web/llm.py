"""可選 OpenAI 相容 chat。沒有 API key 時 available() 為 False，不打網路。"""
from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

DEFAULT_BASE = "https://api.openai.com/v1"
DEFAULT_MODEL = "gpt-4o-mini"

CLASSIFY_SYSTEM = (
    "你是道樞意圖分類器。只回 JSON 物件，不要 markdown。"
    "intent 必須是以下之一："
    "expense,mood,shopping_add,health,reminder,note,decision,"
    "query_expense,query_reminders,query_notes,unknown。"
    "slots 為物件，鍵用 item/amount/mood/content/datetime/"
    "subject/sleep_hours/exercise/water/topic/verdict。"
)


def available() -> bool:
    """有非空白 API key 才視為可呼叫。"""
    return bool((os.environ.get("DAOZHU_LLM_API_KEY") or "").strip())


def classify(text: str) -> dict[str, Any] | None:
    """請模型分類一句話。不可用或解析失敗回 None。"""
    raw = chat(
        [
            {"role": "system", "content": CLASSIFY_SYSTEM},
            {"role": "user", "content": text},
        ],
        temperature=0,
    )
    if not raw:
        return None
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return None
    if not isinstance(data, dict):
        return None
    intent = str(data.get("intent") or "unknown")
    slots = data.get("slots") if isinstance(data.get("slots"), dict) else {}
    return {"intent": intent, "slots": slots}


def chat(messages: list[dict[str, str]], temperature: float = 0.4) -> str | None:
    """打 /v1/chat/completions。沒 key 回 None。"""
    key = (os.environ.get("DAOZHU_LLM_API_KEY") or "").strip()
    if not key:
        return None
    base = (os.environ.get("DAOZHU_LLM_BASE_URL") or DEFAULT_BASE).rstrip("/")
    model = os.environ.get("DAOZHU_LLM_MODEL") or DEFAULT_MODEL
    payload = json.dumps(
        {"model": model, "messages": messages, "temperature": temperature},
        ensure_ascii=False,
    ).encode("utf-8")
    req = urllib.request.Request(
        base + "/chat/completions",
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            body = json.loads(resp.read().decode("utf-8"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, OSError):
        return None
    choices = body.get("choices") if isinstance(body, dict) else None
    if not choices:
        return None
    content = ((choices[0] or {}).get("message") or {}).get("content")
    return str(content).strip() if content else None
