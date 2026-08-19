"""第四期薄桌面殼：同一套 loopback 伺服器，用系統瀏覽器打開。"""
from __future__ import annotations

import webbrowser

import uvicorn

from web.app import app

URL = "http://127.0.0.1:8765"


def main() -> None:
    """啟動儀表板並嘗試打開系統瀏覽器。失敗則只印網址。"""
    print(f"桌面殼：請用系統瀏覽器打開 {URL} （第四期不內嵌視窗）")
    try:
        webbrowser.open(URL)
    except Exception:
        pass
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
