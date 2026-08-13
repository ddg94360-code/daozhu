#!/usr/bin/env python3
"""萬象心鏡動畫生成器：把模式與內容資料渲染成動畫 HTML。

用法：
  python xinjing_render.py <模式> <資料.json> [-o 輸出.html]

  模式：tarot | gua | yuan | chart | fengshui | star | dream
  資料：JSON 檔，各模式結構見下方 DATA_EXAMPLES 或 xinjing/README.md。

範例：
  python xinjing_render.py tarot examples/tarot.json -o /tmp/ta.html
  python xinjing_render.py gua   examples/gua.json   -o /tmp/gua.html
"""
import argparse
import json
import os
import sys

ENGINE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "xinjing_engine.html")


def render(mode: str, data: dict) -> str:
    """把資料嵌入引擎，回傳完整 HTML 字串。"""
    with open(ENGINE, "r", encoding="utf-8") as f:
        html = f.read()
    html = html.replace("__MODE__", mode)
    html = html.replace("__DATA__", json.dumps(data, ensure_ascii=False))
    return html


def main() -> int:
    ap = argparse.ArgumentParser(description="萬象心鏡動畫生成器")
    ap.add_argument("mode", choices=["tarot", "gua", "yuan", "chart", "fengshui", "star", "dream"],
                    help="七模式之一")
    ap.add_argument("data", help="內容資料 JSON 檔路徑")
    ap.add_argument("-o", "--output", default="", help="輸出 HTML 路徑（預設 <模式>_<時間戳>.html）")
    args = ap.parse_args()

    try:
        with open(args.data, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (OSError, json.JSONDecodeError) as e:
        print(f"讀取資料失敗: {e}", file=sys.stderr)
        return 1
    if not isinstance(data, dict):
        print("資料必須是 JSON 物件", file=sys.stderr)
        return 1

    out = args.output or f"xinjing_{args.mode}.html"
    with open(out, "w", encoding="utf-8") as f:
        f.write(render(args.mode, data))
    print(f"已生成: {os.path.abspath(out)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
