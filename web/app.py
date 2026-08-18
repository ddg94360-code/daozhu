"""道樞本機儀表板 HTTP 入口。只聽 loopback；業務一律轉 daily/weekly/solarterm。"""
from __future__ import annotations

import os
import sys

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

_REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_MCP = os.path.join(_REPO, "mcp")
_STATIC = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")


def _mcp_on_path() -> None:
    if _MCP not in sys.path:
        sys.path.insert(0, _MCP)


_mcp_on_path()

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


@app.get("/api/healthz")
def healthz() -> dict:
    return {"ok": True}


# 靜態目錄在 Task 5 才放 index.html；此處若目錄尚無檔案，先不要 mount 以免測試炸。
# Task 5 再加：if os.path.isdir(_STATIC): app.mount("/", StaticFiles(directory=_STATIC, html=True), name="static")
