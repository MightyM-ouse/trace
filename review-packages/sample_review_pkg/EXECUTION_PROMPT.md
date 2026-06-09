# Execution Prompt (sample)

> This is an illustrative review-package showing the evidence format. It is not a
> record of a real change — it documents what a Validator assembles for human approval.

## Task given to the Builder
Add a `/api/health` liveness endpoint to the TRACE telemetry server that returns
`{"status": "ok", "service": "trace-telemetry"}`.

## Context routed to the agent
- Role: Builder
- Allowed: `src/server/**`, `tests/**`
- Forbidden: `TECH_STACK.md`, `.claude/**`
- Ratified task from `PROJECT_STATUS_AND_NEXT_STEPS.md` task queue.

## Acceptance criteria
- Endpoint returns 200 with the documented body.
- A test asserts the contract.
- No changes outside `src/server/` and `tests/`.
