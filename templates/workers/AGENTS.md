# AGENTS.md Template

This repository is governed by TRACE: Template, Route, Assign, Check, Evidence.
The repository is the durable source of truth; chat memory is not.

## Startup

Before making current-state claims or changing files:

1. Read this file and the applicable worker adapter.
2. Read `trace/STAR_MAP.md`, `trace/ACTIVE_WORK_REGISTRY.yaml`, the active issue or task packet, and the relevant PR.
3. Load context through `trace/CELESTIAL_INDEX.json`; broaden context only with a recorded reason.
4. Confirm role and workflow in `trace/ROLE_REGISTRY.yaml` and `trace/WORKFLOWS.yaml`.
5. Record one synchronization verdict: `SYNC_PASS`, `SYNC_BLOCKED`, or `SYNC_UNVERIFIED_LOCAL_STATE`.

Only `SYNC_PASS` permits execution.

## Authority

- Product Owner or repository maintainer owns scope, priority, functional acceptance, risk acceptance, merge, and release.
- Workers execute only inside an approved task envelope.
- Workers may not self-approve, merge, force-push, rewrite shared history, bypass policy, or silently expand scope.

## Parallel Work

- Use unique task IDs, branches, worktrees, starting commits, and PRs.
- Writable paths are exclusive while a task is active.
- Shared paths require one designated owner, a sequential phase, an amendment, or explicit reconciliation ownership.

## Evidence

Meaningful work is incomplete without reviewable evidence:

- Task packet under `trace/tasks/`
- Light Curve or review package
- Markdown handoff
- JSON handoff conforming to `trace/schemas/agent_handoff.schema.json`

Detailed evidence belongs in the repository. Chat output stays concise and points to evidence paths.

## Security

Never commit secrets, credentials, cookies, browser profiles, private keys, `.env` contents, personal data, or unredacted sensitive output.

Public source visibility does not authorize public runtime exposure, cloud execution, external messages, paid services, or privileged host changes.

