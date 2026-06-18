"""End-to-end tests for the TRACE telemetry server.

Run from repo root: `python3 -m pytest -q` (after `pip install -r src/server/requirements.txt`).
"""
import json
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


def test_sse_broadcast_fanout(app_client):
    # Proves the SSE fan-out: a broadcast reaches a subscribed queue. (We test the
    # mechanism directly rather than an HTTP stream, which would block on an open
    # connection.)
    import asyncio

    import main

    async def run():
        q: asyncio.Queue = asyncio.Queue()
        main._subscribers.add(q)
        try:
            main._broadcast([{"event": "PostToolUse", "tool_name": "Bash"}])
            return await asyncio.wait_for(q.get(), timeout=1.0)
        finally:
            main._subscribers.discard(q)

    rec = asyncio.run(run())
    assert rec["tool_name"] == "Bash"


def test_ingest_ignores_partial_trailing_line(tmp_path, monkeypatch):
    # A half-written final line must not be consumed until it's complete.
    monkeypatch.setenv("TRACE_PROJECT_DIR", str(tmp_path))
    logs = tmp_path / "agent-logs"
    logs.mkdir()
    jsonl = logs / "events.jsonl"
    jsonl.write_text(
        json.dumps({"event": "UserPromptSubmit"}) + "\n" + '{"event": "PostToolU'  # truncated
    )
    for mod in ("ingest", "db", "paths"):
        sys.modules.pop(mod, None)
    import db as dbmod
    import ingest as ingestmod

    dbmod.init_db()
    first = ingestmod.ingest_new()
    assert len(first) == 1  # only the complete line
    # Complete the line; next ingest picks it up exactly once.
    with open(jsonl, "a", encoding="utf-8") as fh:
        fh.write('se", "tool_name": "Bash"}\n')
    second = ingestmod.ingest_new()
    assert len(second) == 1
    assert dbmod.counters()["total_events"] == 2


def test_ingest_hook_requires_correct_token(tmp_path, monkeypatch):
    # With a token configured, a wrong token is rejected and the right one passes.
    monkeypatch.setenv("TRACE_PROJECT_DIR", str(tmp_path))
    monkeypatch.setenv("TRACE_INGEST_TOKEN", "s3cret")
    (tmp_path / "agent-logs").mkdir()
    for mod in ("main", "ingest", "db", "paths", "models"):
        sys.modules.pop(mod, None)
    import main
    from fastapi.testclient import TestClient

    with TestClient(main.app) as client:
        bad = client.post(
            "/api/telemetry/hook", headers={"x-trace-token": "wrong"}, json={}
        )
        assert bad.status_code == 401
        good = client.post(
            "/api/telemetry/hook", headers={"x-trace-token": "s3cret"}, json={}
        )
        assert good.status_code == 200
