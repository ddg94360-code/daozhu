"""儀表板測試：隔離記憶庫 + FastAPI TestClient。"""
import os
import sys

import pytest

_REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_MCP = os.path.join(_REPO, "mcp")
_WEB = os.path.join(_REPO, "web")
for p in (_WEB, _MCP):
    if p not in sys.path:
        sys.path.insert(0, p)


@pytest.fixture()
def isolated_memory(tmp_path, monkeypatch):
    monkeypatch.setenv("DAOZHU_MEMORY_DIR", str(tmp_path))
    return tmp_path


@pytest.fixture()
def client(isolated_memory):
    from fastapi.testclient import TestClient

    from app import app

    with TestClient(app) as c:
        yield c


@pytest.fixture(autouse=True)
def _clear_cabinet_session():
    import cabinet_session

    cabinet_session.clear()
    yield
    cabinet_session.clear()
