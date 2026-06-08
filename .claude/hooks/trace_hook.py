#!/usr/bin/env python3
"""TRACE lifecycle hook — dual sink.

Invoked by Claude Code for each configured lifecycle event:
    python3 trace_hook.py <EventName>

Reads the event JSON on stdin, then:
  1. Appends a normalized telemetry record to agent-logs/events.jsonl (durable
     write-ahead log — survives even if the dashboard server is offline).
  2. Best-effort POSTs the record to the local telemetry server.

Design rules:
  * Never block. Always exit 0. Telemetry must not interfere with the agent.
  * Stdlib only (no third-party deps in the hook path).
  * On SessionStart (resume/compact), echo the project status file to stdout so
    Claude Code re-injects it as context — TRACE's anti-context-rot rehydration.
"""
import json
import os
import sys
import urllib.request
from datetime import datetime, timezone

SERVER_URL = os.environ.get("TRACE_SERVER_URL", "http://127.0.0.1:8000/api/telemetry/hook")
INGEST_TOKEN = os.environ.get("TRACE_INGEST_TOKEN", "")


def project_dir() -> str:
    return os.environ.get("CLAUDE_PROJECT_DIR") or os.getcwd()


def read_event() -> dict:
    try:
        raw = sys.stdin.read()
        return json.loads(raw) if raw.strip() else {}
    except Exception:
        return {}


def _dig(d: dict, *keys):
    """Return the first present key from a dict."""
    for k in keys:
        if isinstance(d, dict) and k in d and d[k] is not None:
            return d[k]
    return None


def _summarize_intent(payload: dict) -> str:
    """Human-readable one-liner of what the tool is about to do / did."""
    name = payload.get("tool_name") or payload.get("hook_event_name") or "?"
    ti = payload.get("tool_input") or {}
    if isinstance(ti, dict):
        for k in ("command", "file_path", "path", "pattern", "url", "prompt", "description"):
            if ti.get(k):
                return f"{name}: {str(ti[k])[:160]}"
    if payload.get("prompt"):
        return f"{name}: {str(payload['prompt'])[:160]}"
    return name


def build_record(event_name: str, payload: dict) -> dict:
    tool_response = payload.get("tool_response") or {}
    duration_ms = _dig(payload, "duration_ms") or _dig(tool_response, "duration_ms", "totalDurationMs")
    total_tokens = _dig(tool_response, "totalTokens")
    usage = tool_response.get("usage") if isinstance(tool_response, dict) else None
    success = event_name != "PostToolUseFailure"
    if isinstance(tool_response, dict) and tool_response.get("status") == "error":
        success = False
    return {
        "ts": datetime.now(timezone.utc).isoformat(),
        "event": event_name,
        "session_id": payload.get("session_id"),
        "tool_name": payload.get("tool_name"),
        "tool_intent": _summarize_intent(payload),
        "duration_ms": duration_ms,
        "total_tokens": total_tokens,
        "total_tool_use_count": tool_response.get("totalToolUseCount") if isinstance(tool_response, dict) else None,
        "usage": usage,
        "agent_id": tool_response.get("agentId") if isinstance(tool_response, dict) else None,
        "success": success,
        "cwd": payload.get("cwd"),
    }


def append_jsonl(record: dict) -> None:
    logs = os.path.join(project_dir(), "agent-logs")
    os.makedirs(logs, exist_ok=True)
    with open(os.path.join(logs, "events.jsonl"), "a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


def post_server(record: dict) -> None:
    try:
        data = json.dumps(record).encode("utf-8")
        req = urllib.request.Request(SERVER_URL, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        if INGEST_TOKEN:
            req.add_header("X-TRACE-Token", INGEST_TOKEN)
        urllib.request.urlopen(req, timeout=1.0).read()
    except Exception:
        pass  # server offline is fine — JSONL is the durable record


def session_start_context() -> None:
    status = os.path.join(project_dir(), "PROJECT_STATUS_AND_NEXT_STEPS.md")
    if os.path.exists(status):
        try:
            with open(status, encoding="utf-8") as fh:
                body = fh.read()
            print("## TRACE context rehydration (resumed session)\n")
            print("Current project status below — continue from the task queue.\n")
            print(body)
        except Exception:
            pass


def main() -> int:
    event_name = sys.argv[1] if len(sys.argv) > 1 else "Unknown"
    payload = read_event()
    record = build_record(event_name, payload)
    if event_name == "PreCompact":
        record["context_rot_event"] = True
    try:
        append_jsonl(record)
    except Exception:
        pass
    post_server(record)
    if event_name == "SessionStart":
        session_start_context()
    return 0


if __name__ == "__main__":
    sys.exit(main())
