"""道樞記憶層 MCP server。

提供日用集（記帳/健康/提醒/採買/情緒日記/學習筆記/決策日誌）、週報、系統狀態、
道藏與節氣工具。記憶資料存於 local_memory/（可經 DAOZHU_MEMORY_DIR 覆蓋）。

純轉發工具集中於 _TOOLS 迴圈註冊；工具描述取自底層函數 docstring。
"""
from mcp.server.fastmcp import FastMCP

import daily
import weekly
import daozang
import solarterm

mcp = FastMCP("daozhu")

_TOOLS = {
    # ---- 日用集：記帳
    "daozhu_log_expense": daily.log_expense,
    "daozhu_month_expense_summary": daily.month_expense_summary,
    # ---- 健康
    "daozhu_log_health": daily.log_health,
    # ---- 提醒
    "daozhu_add_reminder": daily.add_reminder,
    "daozhu_pending_reminders": daily.pending_reminders,
    # ---- 採買
    "daozhu_add_shopping": daily.add_shopping,
    "daozhu_list_shopping": daily.list_shopping,
    "daozhu_check_shopping": daily.check_shopping,
    "daozhu_remove_shopping": daily.remove_shopping,
    # ---- 情緒日記
    "daozhu_log_mood": daily.log_mood,
    # ---- 學習筆記
    "daozhu_add_study_note": daily.add_study_note,
    "daozhu_list_study_notes": daily.list_study_notes,
    "daozhu_due_study_notes": daily.due_study_notes,
    "daozhu_delete_study_note": daily.delete_study_note,
    # ---- 決策日誌
    "daozhu_log_decision": daily.log_decision,
    "daozhu_review_decisions": daily.review_decisions,
    # ---- 週報與狀態
    "daozhu_weekly_report": weekly.weekly_report,
    "daozhu_status": weekly.status,
    # ---- 道藏（成功案例）
    "daozhu_daozang_store": daozang.store,
    "daozhu_daozang_recall": daozang.recall,
    # ---- 陰陽時令
    "daozhu_solar_term": solarterm.current_solar_term,
}

for _name, _fn in _TOOLS.items():
    mcp.tool(name=_name)(_fn)


if __name__ == "__main__":
    mcp.run()
