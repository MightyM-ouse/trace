# TRACE Telemetry Server (FastAPI)

Local server that ingests TRACE lifecycle telemetry and serves it to the dashboard.

## Run
```bash
pip install -r requirements.txt
TRACE_PROJECT_DIR=/path/to/repo uvicorn main:app --host 127.0.0.1 --port 8000 --reload
# or, from repo root:  make server
```

## How data flows
The hook (`.claude/hooks/trace_hook.py`) appends every event to `agent-logs/events.jsonl`
(durable) and POSTs a wake-up here. The server ingests **from the JSONL** (single source of
truth) into SQLite (`agent-logs/trace.db`), so there's no double-counting and nothing is lost
if the server is offline — a background poll replays the backlog on startup and every few seconds.

## Endpoints
| Method | Path | Purpose |
|--------|------|---------|
| GET | `/api/health` | Liveness |
| POST | `/api/telemetry/hook` | Hook wake-up (triggers ingest + SSE broadcast) |
| GET | `/api/state` | Counters + recent events + context snapshot |
| GET | `/api/stream` | Server-Sent Events live feed |
| GET | `/api/roi` | Approximate token/cost/iterations (labeled approximate) |
| GET | `/api/evidence` | List of review-packages |

## Config (env)
- `TRACE_PROJECT_DIR` — repo root (defaults to two levels up from this file).
- `TRACE_INGEST_TOKEN` — if set, requires header `X-TRACE-Token` on POST.
- `TRACE_POLL_SECONDS` — background ingest interval (default 3).

## Notes
- Binds to `127.0.0.1` only.
- SQLite uses WAL on local disks, with automatic fallback to rollback-journal mode on
  filesystems that don't support WAL (some network/overlay mounts).
- Accurate session token/cost requires Claude Code OpenTelemetry; the v1 ROI panel is
  explicitly approximate.
