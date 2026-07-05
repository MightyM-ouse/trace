# <TASK-ID> - <Outcome>

## Authority

- Product Owner or maintainer: `<name>`
- Instruction prepared by: `<role/person>`
- Instruction approval: `<approved reference and date>`
- Assigned worker: `<worker>`
- Role: `<role from trace/ROLE_REGISTRY.yaml>`
- Issue: `<number or URL>`
- Branch: `<unique task branch>`
- Starting commit: `<full SHA>`
- Pull request: `<number, URL, or pending>`

The approved packet authorizes autonomous execution only inside the envelope below. It does not authorize acceptance, merge, release, risk acceptance, or unlisted external effects.

## Synchronization Record

- Verdict: `SYNC_PASS | SYNC_BLOCKED | SYNC_UNVERIFIED_LOCAL_STATE`
- Checked at: `<ISO-8601>`
- Accepted baseline: `<full SHA>`
- Task branch/head: `<full SHA>`
- Sources checked: `<issue, task, PR, status, decisions, active-work registry, CI>`
- Known local/unpushed work: `<none or owner/status>`
- Discrepancies and resolution: `<none or exact record>`

Execution is forbidden unless the verdict is `SYNC_PASS`.

## Required Outcome

Describe the result and user value. Do not prescribe the solution unless an accepted contract or safety requirement makes the method mandatory.

## Acceptance Criteria

1. `<observable result>`
2. `<quality/security result>`
3. `<evidence result>`

## Ownership

- Writable paths: `<glob list>`
- Read-only paths: `<glob list>`
- Shared surfaces: `<list and designated owner>`
- Forbidden paths: `<list>`

## Validation And Evidence

- Required checks: `<list>`
- Security/provenance checks: `<list>`
- Independent review: `<required/not required and reason>`
- Light Curve: `trace/evidence/<TASK-ID>_LIGHT_CURVE.md`
- Markdown handoff: `trace/evidence/<TASK-ID>_HANDOFF.md`
- JSON handoff: `trace/evidence/<TASK-ID>_HANDOFF.json`

## Completion Response

Return only task status, branch/final commit/PR, validation summary, evidence paths, downloads/dependencies summary, deviations/risks, and decisions still required.

