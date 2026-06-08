# TECH_STACK

*The authoritative technology choices for TRACE. Agents must read this before implementation and must not silently change it (the Builder role is forbidden from altering this file).*

## Backend
- **Language:** Python 3.11+
- **Framework:** FastAPI
- **Server:** Uvicorn (ASGI)
- **Data validation:** Pydantic v2
- **Telemetry store:** SQLite (WAL mode) at `agent-logs/trace.db`
- **Write-ahead fallback:** append-only JSONL at `agent-logs/events.jsonl`
- **Lint/format:** ruff

## Frontend
- **Framework:** React 18
- **Build tool:** Vite
- **Styling:** TailwindCSS
- **Live updates:** Server-Sent Events (EventSource)
- **Lint:** ESLint

## Tooling / runtime
- **Package manager:** npm
- **Task runner:** Makefile + npm scripts
- **AI runtime:** Claude Code (lifecycle hooks + status line + permissions)
- **Approximate ROI telemetry:** Claude Code OpenTelemetry export (`CLAUDE_CODE_ENABLE_TELEMETRY=1`)

## Versioning policy
- v1: prompt personas, single-user, local dashboard, approximate ROI.
- v2: real subagents, SQLite analytics, team telemetry.
