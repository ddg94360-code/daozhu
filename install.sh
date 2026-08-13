#!/usr/bin/env bash
# 一鍵安裝道樞到目標專案
#
# 用法:
#   bash install.sh [目標目錄]   （預設 . = 當前目錄）
#
# 安裝內容：skills/daozhu + mcp/* 到 <目標>/.claude/
set -e

SRC="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET="${1:-.}"

echo "安裝道樞 → $TARGET/.claude/"
mkdir -p "$TARGET/.claude/skills" "$TARGET/.claude/daozhu-mcp/tests"

cp -r "$SRC/skills/daozhu" "$TARGET/.claude/skills/daozhu"
cp "$SRC"/mcp/*.py "$TARGET/.claude/daozhu-mcp/"
cp "$SRC/mcp/requirements.txt" "$SRC/mcp/config.yaml.example" "$TARGET/.claude/daozhu-mcp/"
cp "$SRC"/mcp/tests/*.py "$TARGET/.claude/daozhu-mcp/tests/"

echo ""
echo "✓ 道樞已安裝。接著三步即可啟用："
echo "  1) pip install -r $TARGET/.claude/daozhu-mcp/requirements.txt"
echo "  2) 依 .mcp.json.example 建立專案根 .mcp.json（含 daozhu server）"
echo "  3) .claude/settings.local.json 加 {\"enableAllProjectMcpServers\": true}"
echo "  4) Reload Window，/mcp 確認 daozhu Connected"
