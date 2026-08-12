"""daozhu-mcp 共用測試配置：記憶庫隔離 fixture。"""
import os
import sys

import pytest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.fixture()
def isolated_memory(tmp_path, monkeypatch):
    """隔離記憶庫：DAOZHU_MEMORY_DIR 指向臨時目錄。

    memory_store.base_dir() 惰性讀取環境變數，setenv 即生效，無需碰內部變數。
    """
    monkeypatch.setenv("DAOZHU_MEMORY_DIR", str(tmp_path))
    return tmp_path
