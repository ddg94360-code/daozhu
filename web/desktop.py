"""桌面殼：預設系統瀏覽器；--window 才開 pywebview 真視窗。"""
from __future__ import annotations

import argparse
import socket
import sys
import threading
import time
import webbrowser

import uvicorn

from web.app import app

URL = "http://127.0.0.1:8765"
HOST = "127.0.0.1"
PORT = 8765


def _port_in_use() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(0.3)
        return sock.connect_ex((HOST, PORT)) == 0


def _serve() -> None:
    uvicorn.run(app, host=HOST, port=PORT, log_level="info")


def _wait_ready(timeout: float = 8.0) -> bool:
    deadline = time.time() + timeout
    while time.time() < deadline:
        if _port_in_use():
            return True
        time.sleep(0.1)
    return False


def _open_window() -> None:
    try:
        import webview
    except ImportError:
        print("未裝 pywebview，請 pip install -r mcp/requirements-web.txt", file=sys.stderr)
        raise SystemExit(1)
    webview.create_window("道樞", URL, width=1100, height=800)
    webview.start()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="道樞桌面殼")
    parser.add_argument(
        "--window",
        action="store_true",
        help="用 pywebview 開本機視窗（系統標題列）",
    )
    args = parser.parse_args(argv)

    if args.window:
        own_server = False
        if _port_in_use():
            print(f"8765 已在聽，只開視窗連 {URL}")
        else:
            own_server = True
            thread = threading.Thread(target=_serve, daemon=True)
            thread.start()
            if not _wait_ready():
                print("伺服器未在 8765 起來", file=sys.stderr)
                raise SystemExit(1)
        _open_window()
        return

    print(f"桌面殼：請用系統瀏覽器打開 {URL} （第四期不內嵌視窗）")
    try:
        webbrowser.open(URL)
    except Exception:
        pass
    _serve()


if __name__ == "__main__":
    main()
