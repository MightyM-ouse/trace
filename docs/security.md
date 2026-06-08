# TRACE Security & Trust Model

TRACE ships executable automation (Claude Code hooks). Treat any cloned `.claude/` directory as security-sensitive.

## What executes, and when
- **On opening the project in Claude Code:** `SessionStart` hooks run (non-interactive context injection only).
- **During a session:** `PreToolUse`, `PostToolUse`, `PreCompact`, and `Stop` hooks run, plus the `statusLine` command.
- All TRACE hooks are implemented by **in-repo, reviewable scripts** under `.claude/hooks/`.

## What TRACE's hooks do
1. Append the event to a local write-ahead log (`agent-logs/events.jsonl`).
2. Best-effort POST the event to the local telemetry server at `http://127.0.0.1:8000`.

They do **not** send any data off-machine, and they do **not** execute arbitrary remote code.

## Hardening choices
- The telemetry server binds to `127.0.0.1` only — not reachable from the network.
- An optional shared-secret header (`TRACE_INGEST_TOKEN`) can be required on the ingest endpoint so only the local hooks can write telemetry. Configure via `.claude/settings.json` `allowedEnvVars`.
- `agent-logs/` is git-ignored — telemetry never enters version history.

## Before you clone any TRACE-based repo
Review `.claude/settings.json` and `.claude/hooks/` first. A malicious fork could repoint a hook at an external URL or run arbitrary `SessionStart` commands. The honest record (evidence) is in git; the operational telemetry is local and disposable.
