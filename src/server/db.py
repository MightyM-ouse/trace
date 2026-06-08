"""SQLite store for TRACE telemetry (WAL mode).

The JSONL write-ahead log is the source of truth; this SQLite DB is a queryable
projection built by replaying the log (see ingest.py). All dashboard aggregations
read from here.
"""
import json
import sqlite3
from contextlib import contextmanager
from typing import Any, Iterator

from paths import db_path

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
    id                   INTEGER PRIMARY KEY AUTOINCREMENT,
    ts                   TEXT,
    event                TEXT,
    session_id           TEXT,
    tool_name            TEXT,
    tool_intent          TEXT,
    duration_ms          REAL,
    total_tokens         INTEGER,
    total_tool_use_count INTEGER,
    usage_json           TEXT,
    agent_id             TEXT,
    success              INTEGER,
    context_rot          INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_event ON events(event);
CREATE INDEX IF NOT EXISTS idx_events_session ON events(session_id);
"""


@contextmanager
def connect() -> Iterator[sqlite3.Connection]:
    conn = sqlite3.connect(str(db_path()), timeout=5.0)
    conn.row_factory = sqlite3.Row
    try:
        # WAL gives safe concurrent reads/writes on local disks. Some networked /
        # overlay filesystems don't support it — fall back gracefully there.
        try:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA synchronous=NORMAL;")
        except sqlite3.OperationalError:
            conn.execute("PRAGMA journal_mode=DELETE;")
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db() -> None:
    with connect() as c:
        c.executescript(SCHEMA)


def get_meta(c: sqlite3.Connection, key: str, default: str = "0") -> str:
    row = c.execute("SELECT value FROM meta WHERE key=?", (key,)).fetchone()
    return row["value"] if row else default


def set_meta(c: sqlite3.Connection, key: str, value: str) -> None:
    c.execute(
        "INSERT INTO meta(key, value) VALUES(?, ?) "
        "ON CONFLICT(key) DO UPDATE SET value=excluded.value",
        (key, value),
    )


def insert_event(c: sqlite3.Connection, rec: dict[str, Any]) -> int:
    usage = rec.get("usage")
    cur = c.execute(
        """INSERT INTO events
           (ts, event, session_id, tool_name, tool_intent, duration_ms,
            total_tokens, total_tool_use_count, usage_json, agent_id, success, context_rot)
           VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
        (
            rec.get("ts"),
            rec.get("event"),
            rec.get("session_id"),
            rec.get("tool_name"),
            rec.get("tool_intent"),
            rec.get("duration_ms"),
            rec.get("total_tokens"),
            rec.get("total_tool_use_count"),
            json.dumps(usage) if usage is not None else None,
            rec.get("agent_id"),
            1 if rec.get("success", True) else 0,
            1 if rec.get("context_rot_event") else 0,
        ),
    )
    return cur.lastrowid


def recent_events(limit: int = 100) -> list[dict]:
    with connect() as c:
        rows = c.execute(
            "SELECT * FROM events ORDER BY id DESC LIMIT ?", (limit,)
        ).fetchall()
    return [dict(r) for r in rows][::-1]


def counters() -> dict:
    with connect() as c:
        total = c.execute("SELECT COUNT(*) n FROM events").fetchone()["n"]
        iterations = c.execute(
            "SELECT COUNT(*) n FROM events WHERE event='UserPromptSubmit'"
        ).fetchone()["n"]
        tool_calls = c.execute(
            "SELECT COUNT(*) n FROM events WHERE event IN ('PostToolUse','PostToolUseFailure')"
        ).fetchone()["n"]
        failures = c.execute(
            "SELECT COUNT(*) n FROM events WHERE event='PostToolUseFailure'"
        ).fetchone()["n"]
        tokens = c.execute(
            "SELECT COALESCE(SUM(total_tokens),0) s FROM events WHERE total_tokens IS NOT NULL"
        ).fetchone()["s"]
        duration = c.execute(
            "SELECT COALESCE(SUM(duration_ms),0) s FROM events WHERE duration_ms IS NOT NULL"
        ).fetchone()["s"]
        rot_events = c.execute(
            "SELECT COUNT(*) n FROM events WHERE context_rot=1"
        ).fetchone()["n"]
        last_session = c.execute(
            "SELECT session_id FROM events WHERE session_id IS NOT NULL ORDER BY id DESC LIMIT 1"
        ).fetchone()
        top_tools = c.execute(
            """SELECT tool_name, COUNT(*) n FROM events
               WHERE tool_name IS NOT NULL GROUP BY tool_name ORDER BY n DESC LIMIT 8"""
        ).fetchall()
    return {
        "total_events": total,
        "human_iterations": iterations,
        "tool_calls": tool_calls,
        "failures": failures,
        "subagent_tokens": int(tokens),
        "total_tool_duration_ms": round(duration, 1),
        "context_rot_events": rot_events,
        "active_session": last_session["session_id"] if last_session else None,
        "top_tools": [dict(r) for r in top_tools],
    }
