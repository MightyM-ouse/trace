# TRACE Agent Instruction Manual

*This file is the persistent brain for any AI agent working in this repository. It enforces the TRACE methodology and prevents context rot. Read it before doing anything else.*

## Project Overview
TRACE (Template, Route, Assign, Check, Evidence) is an open-source orchestration framework and observability dashboard for AI-assisted software development. Goals: prevent context rot, track token/time/effort ROI, and enforce bounded agent execution with real, reviewable evidence.

## Agent Behavior Rules (the TRACE algorithm)
1. **Template (T):** Never start coding without verifying the project structure. Read `PROJECT_ARCHITECTURE.md` and `TECH_STACK.md` before adding new domains.
2. **Route (R):** Read only what your task needs. Consult `agent-context/AGENT_CONTEXT_INDEX.json` for your role's `allowed_files` / `forbidden_files`. Do not scan the whole repo.
3. **Assign (A):** Identify your role for the current task — **Planner**, **Builder**, or **Validator** (see `agent-context/roles/`) — and stay within its boundaries. Role boundaries are also enforced as permission rules in `.Codex/settings.json`; do not attempt actions your role forbids.
4. **Check (C):** Before large modifications, run a preflight (`scripts/preflight.sh`): read current file state, confirm dependencies, confirm the task is ratified. Do not begin building on an unratified plan.
5. **Evidence (E):** Never conclude a task without leaving evidence. Update `PROJECT_STATUS_AND_NEXT_STEPS.md`, and for code changes produce a review-package under `review-packages/`. Pause for human approval before committing to `main`.

## Telemetry model (important)
- **Observability hooks are non-blocking by design.** PreToolUse / PostToolUse / Stop hooks emit telemetry and must not be relied on to block anything.
- **Safety gates MAY block.** Hard boundaries are enforced by the permission system (allow/deny rules), not by telemetry hooks. A blocked tool call is expected behavior, not a hook failure.
- Do not edit `.Codex/settings.json` to disable telemetry. If a hook errors because the dashboard server is offline, that is fine — events are also written to the local JSONL write-ahead log and replayed later.

## Formatting and Code Style
- **Backend:** FastAPI (Python 3.11+). Pydantic models for all telemetry payloads. `ruff` for lint/format.
- **Frontend:** React 18 + Vite + TailwindCSS. ESLint.
- **Documentation:** Keep `README.md` and `PROJECT_STATUS_AND_NEXT_STEPS.md` continuously updated. Do not hallucinate capabilities; mark features as CURRENT, PLANNED, or BLOCKED.

## Honest data contract
What changed / what shipped must be **real** (git diffs, review-packages, status updates, per-tool events). Token/cost/effort ROI is **approximate** and must be labeled as such. Never present an estimated number as if it were measured.
