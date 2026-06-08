# ADR 0001 — Evidence in GitHub, telemetry in SQLite

- Status: Accepted
- Date: 2026-06-08

## Context
TRACE produces two very different kinds of data: durable **evidence** of what changed (must be real, reviewable, version-controlled) and high-frequency operational **telemetry** (token/time/intent samples, can be approximate). A single store cannot serve both well. We considered: (a) committing telemetry to git, (b) SQLite only, (c) JSONL only, (d) a split.

## Decision
Split by data class:
- **Evidence → GitHub.** ADRs, status file, and `review-packages/` (diff, test logs, validation report) are committed. Git is the system of record for "what shipped."
- **Telemetry → SQLite (WAL) at `agent-logs/trace.db`**, the queryable store the dashboard reads. A **JSONL write-ahead log** (`agent-logs/events.jsonl`) captures every event even if the server is offline; the server replays unprocessed lines on startup.

## Why not "GitHub as the database"
Git is unsuited to frequent small appends from a live process: commit spam, history bloat, merge conflicts, network latency, and no real-time query. GitHub is correct for evidence, wrong for live telemetry.

## Consequences
- The dashboard's ROI numbers are local and approximate (sourced from OpenTelemetry), and are labeled as such.
- No telemetry pollutes git history (`agent-logs/` is ignored).
- v2 reuses the same SQLite for cross-session analytics.
