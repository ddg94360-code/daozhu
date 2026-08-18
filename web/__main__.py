"""python -m web → http://127.0.0.1:8765"""
import uvicorn

from app import app


def main() -> None:
    uvicorn.run(app, host="127.0.0.1", port=8765, log_level="info")


if __name__ == "__main__":
    main()
