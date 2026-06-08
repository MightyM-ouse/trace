"""End-to-end tests for the TRACE telemetry server.

Run from repo root: `python3 -m pytest -q` (after `pip install -r src/server/requirements.txt`).
"""
import json
import os
import sys
from pathlib import Path

import pytest

SERVER_DIR = Path(__file__).resolve().parents[1] / "src" / "server"
sys.path.insert(0, str(SERVER_DIR))


@pytest.fixture()
def app_client(tmp_path, monkeypatch):
    # Isolate telemetry to a temp project dir.
    monkeypatch.setenv("TRACE_PROJECT_DIR", str(tmp_path))
    logs = tmp_path / "agent-logs"
    logs.mkdir()
    events = [
        {"ts": "2026-06-08T10:00:00Z", "event": "UserPromptSubmit", "session_id": "s1",
         "tool_intent": "user prompt", "success": True},
        {"ts": "2026-06-08T10:00:01Z", "event": "PreToolUse", "session_id": "s1",
         "tool_name": "Bash", "tool_intent": "Bash: pytest -q", "success": True},
        {"ts": "2026-06-08T10:00:02Z", "event": "PostToolUse", "session_id": "s1",
         "tool_name": "Bash", "duration_ms": 1234.5, "success": True},
        {"ts": "2026-06-08T10:00:03Z", "event": "PostToolUse", "session_id": "s1",
         "tool_name": "Agent", "duration_ms": 48211, "total_tokens": 12450,
         "total_tool_use_count": 7, "usage": {"input_tokens": 8320, "output_tokens": 4130},
         "success": True},
        {"ts": "2026-06-08T10:00:04Z", "event": "PostToolUseFailure", "session_id": "s1",
         "tool_name": "Edit", "duration_ms": 12.0, "success": False},
    ]
    with open(logs / "events.jsonl", "w", encoding="utf-8") as fh:
        for e in events:
            fh.write(json.dumps(e) + "\n")
    (logs / "context.json").write_text(json.dumps({
        "remaining_percentage": 41.0, "used_percentage": 59.0, "model": "Claude Opus",
        "total_cost_usd": 0.73, "total_duration_ms": 120000, "exceeds_200k_tokens": False,
    }))

    # Import fresh modules bound to this tmp project dir.
    for mod in ("main", "ingest", "db", "paths", "models"):
        sys.modules.pop(mod, None)
    import main  # noqa: E402
    from fastapi.testclient import TestClient

    with TestClient(main.app) as client:
        yield client


def test_state_aggregates(app_client):
    r = app_client.get("/api/state")
    assert r.status_code == 200
    body = r.json()
    c = body["counters"]
    assert c["human_iterations"] == 1
    assert c["tool_calls"] == 3          # 2 PostToolUse + 1 PostToolUseFailure
    assert c["failures"] == 1
    assert c["subagent_tokens"] == 12450
    assert body["context"]["remaining_percentage"] == 41.0
    assert len(body["recent_events"]) == 5


def test_roi_is_labeled_approximate(app_client):
    r = app_client.get("/api/roi")
    assert r.status_code == 200
    body = r.json()
    assert body["approximate"] is True
    assert body["subagent_tokens"] == 12450
    assert body["session_cost_usd"] == 0.73
    assert body["human_iterations"] == 1


def test_hook_post_is_idempotent(app_client):
    # Posting a wake-up should not double-count (JSONL is the source of truth).
    before = app_client.get("/api/state").json()["counters"]["total_events"]
    r = app_client.post("/api/telemetry/hook", json={"event": "ping"})
    assert r.status_code == 200
    after = app_client.get("/api/state").json()["counters"]["total_events"]
    assert after == before  # no new JSONL lines => no new rows


def test_health(app_client):
    assert app_client.get("/api/health").json()["status"] == "ok"
