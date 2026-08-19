"""本場內閣會議行程暫存。只留最近一場，不寫碟。"""
from __future__ import annotations

import copy
import secrets
from typing import Any

_SLOT: dict[str, Any] | None = None


def clear() -> None:
    global _SLOT
    _SLOT = None


def get() -> dict[str, Any] | None:
    return _SLOT


def save(topic: str, stages: list, depth: str) -> str:
    global _SLOT
    sid = secrets.token_hex(4)
    _SLOT = {
        "id": sid,
        "topic": topic,
        "stages": copy.deepcopy(list(stages)),
        "depth": depth,
    }
    return sid


def stages_for_followup(body_stages: Any) -> list:
    if isinstance(body_stages, list):
        return body_stages
    if _SLOT and isinstance(_SLOT.get("stages"), list):
        return _SLOT["stages"]
    raise ValueError("尚無本場會議")
