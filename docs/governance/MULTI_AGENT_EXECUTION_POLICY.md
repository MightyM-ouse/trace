# Multi-Agent Execution Policy

## Purpose

This policy allows bounded multi-agent software delivery while preserving human authority, reviewable evidence, and project-neutral TRACE reuse.

Operating principle: precise outcome, bounded authority, independent method.

## Authority Model

- Product Owner or maintainer decides scope, priority, functional acceptance, risk acceptance, merge, and release.
- A system architect role synchronizes state, prepares bounded tasks, coordinates ownership, reviews evidence, and recommends the next gate.
- A worker may execute autonomously only inside an approved task envelope.
- Execution authority is not acceptance authority.
- `main` changes only through reviewed PRs.

## Synchronization Gate

Before an execution instruction and before file edits, compare:

1. Default branch and accepted commit.
2. Current-state map, decisions, risks, active-work registry, and routed context.
3. Active issue, task packet, branch, PR, checks, reviews, and evidence.
4. Writable paths, dependencies, shared surfaces, and integration order.
5. Known local or unpublished work that affects the task.

Record exactly one verdict:

- `SYNC_PASS`: proceed.
- `SYNC_BLOCKED`: stop, reconcile, and report.
- `SYNC_UNVERIFIED_LOCAL_STATE`: stop until the local state is accounted for.

Chat memory is not proof of current repository state.

## Task Packets

A task packet defines outcome, acceptance criteria, evidence, protected boundaries, ownership, dependencies, autonomy envelope, and escalation conditions.

It should not prescribe a solution, root cause, command sequence, or file list unless a safety, architecture, migration, or regulatory constraint requires it.

When status enters `IN_PROGRESS`, the packet is immutable. Scope or authority changes require a separate amendment and a new synchronization pass.

## Parallel Work

Parallel work is allowed only when each task has a unique task ID, branch, worktree, starting commit, PR, accountable worker, declared writable paths, and declared dependencies.

Writable paths are exclusive. Shared paths require one owner, a sequential phase, an amendment, or explicit reconciliation ownership.

## Protected Boundaries

Stop before personal/system paths, credentials/private sources, paid services, privileged/global changes, destructive operations, public/external side effects, material scope expansion, policy bypass, risk acceptance, merge, or release.

## Handoff Contract

Every meaningful worker result includes a concise summary, Markdown handoff, JSON handoff, validation record, exact failures/skips, downloads/dependency provenance, architecture/security impact, residual risk, and recommended next action.

Review recommendations are `APPROVE_TO_MERGE`, `CHANGES_REQUIRED`, or `BLOCKED`. Only the Product Owner or maintainer merges.

