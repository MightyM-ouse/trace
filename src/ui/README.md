# TRACE Dashboard (React + Vite + Tailwind)

Real-time observability UI for the TRACE telemetry server.

## Run
```bash
npm install
npm run dev        # http://localhost:5173  (proxies /api -> :8000)
# or, from repo root:  make ui   (and `make server` in another terminal, or `make dev` for both)
```

## Panels
- **Context window** (real) — `remaining_percentage` from the status line; color-coded context-rot gauge.
- **Iterations / Tool calls / Tool time** (real) — from lifecycle events.
- **Subagent tokens** (approximate) — summed from `Agent` PostToolUse payloads.
- **Live tool timeline** (real) — streamed over SSE.
- **ROI** (approximate) — tokens/cost estimates, clearly labeled.
- **Evidence** (real) — review-packages on disk.

Badges: **real** = measured & git-committed · **approx** = estimated.

## Build
```bash
npm run build      # outputs to dist/
```
