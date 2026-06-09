<div align="center">

# TRACE

**Template · Route · Assign · Check · Evidence**

An open-source AI agent orchestration template and observability tool that prevents context rot, enforces bounded agent responsibilities, and measures the real ROI (tokens, time, human effort) of AI-assisted development.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](./LICENSE)
[![Status: v1 alpha](https://img.shields.io/badge/status-v1%20alpha-orange.svg)](./PROJECT_STATUS_AND_NEXT_STEPS.md)
[![Backend: FastAPI](https://img.shields.io/badge/backend-FastAPI-009688.svg)](https://fastapi.tiangolo.com/)
[![Frontend: React + Vite](https://img.shields.io/badge/frontend-React%20%2B%20Vite-61dafb.svg)](https://vitejs.dev/)

</div>

---

## What is TRACE?

Normal AI-assisted development relies on one long chat window: context degrades as the conversation grows ("context rot"), the model hallucinates files, you repeat yourself, and there's no durable record of what changed. TRACE replaces that with **context engineering** — the repository itself is the source of truth, agents are routed only the context they need, responsibilities are bounded by role, and every change leaves real, reviewable evidence.

TRACE is two things:

1. **A methodology + template** — a standardized repo structure and a set of agent rules (`CLAUDE.md`) that govern how an AI works in your project.
2. **A live observability dashboard** — a local FastAPI + React app that shows, in real time, what the agent is doing, how long tools take, how close you are to a context-rot event, and an approximate token/cost ROI.

## The TRACE algorithm

| Phase | Meaning | What it produces |
|-------|---------|------------------|
| **T — Template** | Establish a rigid folder/file structure as the durable source of truth | `PROJECT_ARCHITECTURE.md`, `TECH_STACK.md`, ADRs |
| **R — Route** | Give each agent only the context it needs | `agent-context/AGENT_CONTEXT_INDEX.json` |
| **A — Assign** | Bound each agent to a role (Planner / Builder / Validator) | permission profiles + role definitions |
| **C — Check** | Preflight before execution; summarize after | `scripts/preflight.sh`, status updates |
| **E — Evidence** | Leave portable proof of work for human approval | `review-packages/` (diff, test logs, validation report) |

## The honest telemetry contract

TRACE is deliberate about what is **measured** vs **estimated**:

- **Real / deterministic** (committed to GitHub): what changed and what shipped — git diffs, review-packages, status-file updates, and the per-tool intent timeline (`tool_name`, `duration_ms`, success/failure). The context-rot gauge (from Claude Code's status line) is also real.
- **Approximate / labeled as such** (local only): session token totals, cost, and "effort saved." Sourced from OpenTelemetry; shown in the UI clearly marked as estimates.

> Evidence lives in **GitHub** (version-controlled, real). Telemetry lives in a local **SQLite** store (queryable, approximate), with a JSONL write-ahead fallback so no event is lost if the dashboard is offline.

## Feature status

| Feature | Status |
|---------|--------|
| Standardized TRACE repo template | **CURRENT** |
| Corrected lifecycle hooks (PreToolUse / PostToolUse / PreCompact / SessionStart / Stop) | **CURRENT** |
| Role personas + permission-rule boundaries | **CURRENT** |
| FastAPI telemetry server (SQLite + SSE) | **CURRENT** |
| React dashboard: live timeline, durations, context-rot gauge, evidence browser | **CURRENT** |
| Approximate ROI panel (subagent tokens + status-line cost snapshot) | **CURRENT** |
| OpenTelemetry token/cost integration (accurate session totals) | **PLANNED (v1.1)** |
| Interactive `npm run init` setup wizard | **CURRENT** |
| Real subagents with per-agent token telemetry | **PLANNED (v2)** |
| Cross-session analytics & baseline-vs-TRACE comparison | **PLANNED (v2)** |
| Team / multi-user telemetry + hosted dashboard | **PLANNED (v2)** |

## Quick start

```bash
# 1. Clone
git clone https://github.com/<your-username>/trace.git
cd trace

# 2. Initialize the project (interactive wizard)
npm run init

# 3. Start the dashboard (FastAPI :8000 + Vite :5173)
make dev
```

Open http://localhost:5173 for the dashboard. See [`docs/`](./docs) for the architecture deep-dive, [`ARCHITECTURE_REVIEW.md`](./ARCHITECTURE_REVIEW.md) for the design rationale, and [`IMPLEMENTATION_PLAN.md`](./IMPLEMENTATION_PLAN.md) for the v1/v2 roadmap.

Requires **Python 3.11+** and **Node 20+**. Hit a dependency snag? See [`docs/troubleshooting.md`](./docs/troubleshooting.md).

## Known limitations (v1)

TRACE v1 is deliberately scoped. Being honest about the edges:

- **Roles are advisory, not runtime-enforced.** Planner/Builder/Validator boundaries are conventions enforced by `CLAUDE.md` instructions and a small set of *universal* safety deny-rules in `.claude/settings.json`. Per-role permission enforcement arrives with real subagents in **v2**.
- **Token/cost ROI is approximate and whole-session.** Per-agent token attribution requires v2 subagents; accurate session totals require the OpenTelemetry integration (planned v1.1). The dashboard labels these numbers **approx**.
- **Single-user, local-first.** No auth, no multi-user aggregation; the server binds to `127.0.0.1`. Team telemetry is **v2**.
- **What's always real:** git diffs, review-packages, status-file updates, and the per-tool intent/duration timeline. Evidence is never estimated.

## Security & trust model

A repository's `.claude/settings.json` **executes hooks when the project is opened in Claude Code**. Before cloning and running any TRACE-based repo, review `.claude/settings.json` and `.claude/hooks/`. TRACE's own hooks only (a) append telemetry locally and (b) POST to `127.0.0.1:8000`; they never send data off-machine. The telemetry server binds to localhost only. See [`docs/security.md`](./docs/security.md).

## License

[MIT](./LICENSE) © 2026 Vinay
