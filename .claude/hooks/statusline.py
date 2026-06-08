#!/usr/bin/env python3
"""TRACE status line. Reads Claude Code session JSON on stdin, prints a status
line, and writes agent-logs/context.json for the dashboard's context-rot gauge."""
import sys, json, os

def main():
    project = os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()
    try:
        data = json.load(sys.stdin)
    except Exception:
        data = {}
    cw = data.get("context_window") or {}
    remaining = cw.get("remaining_percentage")
    used = cw.get("used_percentage")
    model_obj = data.get("model") or {}
    model = model_obj.get("display_name") or model_obj.get("id") or "claude"
    cost = data.get("cost") or {}
    try:
        logs = os.path.join(project, "agent-logs")
        os.makedirs(logs, exist_ok=True)
        with open(os.path.join(logs, "context.json"), "w", encoding="utf-8") as f:
            json.dump({
                "remaining_percentage": remaining,
                "used_percentage": used,
                "model": model,
                "total_cost_usd": cost.get("total_cost_usd"),
                "total_duration_ms": cost.get("total_duration_ms"),
                "total_lines_added": cost.get("total_lines_added"),
                "exceeds_200k_tokens": data.get("exceeds_200k_tokens"),
            }, f)
    except Exception:
        pass
    rem = f"{remaining:.0f}%" if isinstance(remaining, (int, float)) else "?"
    warn = ""
    if isinstance(remaining, (int, float)):
        if remaining <= 15:
            warn = "  [!] CONTEXT ROT RISK"
        elif remaining <= 30:
            warn = "  [.] context low"
    print(f"TRACE | {model} | ctx {rem} free{warn}")

if __name__ == "__main__":
    main()
