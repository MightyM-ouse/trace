"""TRACE telemetry server (FastAPI).

Transport model:
  * Hooks append every event to agent-logs/events.jsonl (durable WAL) and POST a
    notification here. We ingest *from the JSONL* (single source of truth), so the
    POST body is only a wake-up — no double counting, and events survive downtime.
  * The dashboard reads /api/state (snapshot) and subscribes to /api/stream (SSE).

Binds to 127.0.0.1 only. Optional shared-secret via TRACE_INGEST_TOKEN.
"""
import asyncio
import json
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

import db
import ingest
from paths import context_path, review_packages_dir

INGEST_TOKEN = os.environ.get("TRACE_INGEST_TOKEN", "")
POLL_SECONDS = float(os.environ.get("TRACE_POLL_SECONDS", "3"))

_subscribers: set[asyncio.Queue] = set()


def _broadcast(records: list[dict]) -> None:
    for rec in records:
        for q in list(_subscribers):
            try:
                q.put_nowait(rec)
            except asyncio.QueueFull:
                pass


async def _ingest_and_broadcast() -> list[dict]:
    new = await asyncio.to_thread(ingest.ingest_new)
    if new:
        _broadcast(new)
    return new


async def _background_poll() -> None:
    while True:
        try:
            await _ingest_and_broadcast()
        except Exception:
            pass
        await asyncio.sleep(POLL_SECONDS)


@asynccontextmanager
async def lifespan(app: FastAPI):
    db.init_db()
    await asyncio.to_thread(ingest.ingest_new)  # replay backlog
    task = asyncio.create_task(_background_poll())
    try:
        yield
    finally:
        task.cancel()


app = FastAPI(title="TRACE Telemetry Server", version="1.0.0-alpha.1", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _read_context() -> dict:
    p = context_path()
    if p.exists():
        try:
            return json.loads(p.read_text(encoding="utf-8"))
        except Exception:
            return {}
    return {}


@app.get("/api/health")
async def health() -> dict:
    return {"status": "ok", "service": "trace-telemetry"}


@app.post("/api/telemetry/hook")
async def ingest_hook(request: Request, x_trace_token: str = Header(default="")) -> dict:
    if INGEST_TOKEN and x_trace_token != INGEST_TOKEN:
        raise HTTPException(status_code=401, detail="bad ingest token")
    # Body is only a wake-up; the JSONL log is the source of truth.
    try:
        await request.json()
    except Exception:
        pass
    new = await _ingest_and_broadcast()
    return {"ingested": len(new)}


@app.get("/api/state")
async def state() -> dict:
    return {
        "counters": db.counters(),
        "recent_events": db.recent_events(limit=80),
        "context": _read_context(),
    }


@app.get("/api/roi")
async def roi() -> dict:
    """Approximate ROI. Token/cost are estimates (clearly labeled); iteration and
    duration counts are real. For accurate session totals, enable Claude Code
    OpenTelemetry (CLAUDE_CODE_ENABLE_TELEMETRY=1) and feed claude_code.token.usage."""
    c = db.counters()
    ctx = _read_context()
    return {
        "approximate": True,
        "source": "subagent PostToolUse + status line snapshot",
        "note": "Token/cost are approximate. Enable OpenTelemetry for accurate session totals.",
        "subagent_tokens": c["subagent_tokens"],
        "session_cost_usd": ctx.get("total_cost_usd"),
        "session_duration_ms": ctx.get("total_duration_ms"),
        "human_iterations": c["human_iterations"],
        "tool_calls": c["tool_calls"],
        "total_tool_duration_ms": c["total_tool_duration_ms"],
    }


@app.get("/api/evidence")
async def evidence() -> dict:
    items = []
    for p in sorted(review_packages_dir().glob("*")):
        if p.name.lower() == "readme.md":
            continue
        items.append({
            "name": p.name,
            "is_dir": p.is_dir(),
            "size_bytes": p.stat().st_size if p.is_file() else None,
        })
    return {"review_packages": items}


@app.get("/api/stream")
async def stream() -> StreamingResponse:
    q: asyncio.Queue = asyncio.Queue(maxsize=1000)
    _subscribers.add(q)

    async def gen():
        try:
            # prime with a hello so the client knows it's connected
            yield "event: hello\ndata: {}\n\n"
            while True:
                try:
                    rec = await asyncio.wait_for(q.get(), timeout=20.0)
                    yield f"data: {json.dumps(rec)}\n\n"
                except asyncio.TimeoutError:
                    yield ": keep-alive\n\n"  # SSE comment, keeps connection open
        finally:
            _subscribers.discard(q)

    return StreamingResponse(gen(), media_type="text/event-stream")
