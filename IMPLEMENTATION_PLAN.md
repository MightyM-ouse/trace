# TRACE — Implementation Plan (v1 & v2)

*Companion to `ARCHITECTURE_REVIEW.md`. Reflects the decisions locked 2026-06-08: personas in v1 / real subagents in v2, OTel-approximate ROI with real evidence, single-user in v1 / team in v2. This is a plan — no code is written until you approve it.*

---

## 0. Storage decision — SQLite vs "GitHub as the database"

Your question: *TRACE says use SQLite; can we use GitHub itself as the repository/database instead?*

The right answer is to **split the data into two classes**, because they have opposite requirements:

| Data class | Examples | Write pattern | Correct home |
|---|---|---|---|
| **Durable evidence & state** ("must be real") | ADRs, `PROJECT_STATUS_AND_NEXT_STEPS.md`, `review-packages/` (diffs, test logs, validation reports), agent-context indexes | Occasional, deliberate, human-reviewed | **GitHub** (the repo) ✅ |
| **Operational telemetry** ("can be approximate") | Tool intents, `duration_ms`, token/cost rollups, context-gauge samples | High-frequency, automatic, from a live process | **Local store** (JSONL → SQLite) |

**Use GitHub as the system of record for evidence — yes.** That's already TRACE's "repo as source of truth" philosophy, and it's exactly where your "what changed / what shipped must be real" principle belongs. Commits, PRs, and the review-package files *are* the durable, version-controlled, shareable record. GitHub is perfect for this.

**Do not use GitHub as the live telemetry database — no.** Git is not built for frequent small appends from a running process. You'd get commit spam, history bloat, merge conflicts, network latency on every event, and no real-time query. A dashboard polling a git repo for live metrics is impractical.

**Final decision (locked):**
- **Evidence → GitHub** (real, version-controlled record of what changed/shipped).
- **Telemetry → SQLite in v1** (the local store the FastAPI server reads/writes). SQLite runs in WAL mode for safe concurrent writes, lives at `agent-logs/trace.db` (git-ignored), and powers all dashboard aggregations.
- **Crash-safe raw fallback:** hooks also append each event as one JSONL line to `agent-logs/events.jsonl`. If the server is down when a hook fires, the event isn't lost — the server replays unprocessed JSONL lines into SQLite on startup. This gives SQLite's queryability *and* append-only durability.
- **v2:** the same SQLite gains cross-session analytics (historical ROI trends, baseline-vs-TRACE comparison, per-PR cost attribution).

Net: **GitHub for evidence (real), SQLite for telemetry (approximate, queryable), JSONL as the durable write-ahead fallback.**

---

## 1. Scope summary

### Version 1 — "Disciplined personas, real evidence, approximate ROI, single-user, local"
A professional, clonable OSS template where one developer runs a single Claude Code session governed by TRACE rules, with a local real-time dashboard. Roles are enforced by instructions + permission rules (not runtime isolation). Evidence is real and GitHub-committed; ROI is approximate and local.

### Version 2 — "Real subagents, enforced isolation, analytics, team"
Roles become real Claude Code subagents (per-agent token telemetry, enforced boundaries). SQLite analytics, multi-user/team telemetry, hosted dashboard option, published template distribution.

---

## 2. Version 1 — detailed build

### 2.1 Repository scaffold (professional baseline)
```
trace/
├── .claude/
│   ├── settings.json            # CORRECTED hook nesting + permission rules
│   ├── hooks/                   # hook scripts (emit.sh, preflight.sh, precompact.sh, statusline.sh)
│   └── agents/                  # (placeholder; populated in v2)
├── .github/
│   ├── workflows/ci.yml         # lint + test on PR
│   ├── PULL_REQUEST_TEMPLATE.md # requires linked review-package
│   └── ISSUE_TEMPLATE/
├── agent-context/               # AGENT_CONTEXT_INDEX.json, permission profiles, role defs
├── agent-logs/                  # JSONL telemetry (git-ignored) + committed session summaries
├── review-packages/             # portable evidence zips (committed)
├── docs/                        # architecture, ADRs, guides
├── scripts/
│   ├── setup.sh                 # interactive init (run via `npm run init` / `make init`)
│   └── preflight.sh             # Check-phase preflight
├── src/
│   ├── server/                  # FastAPI telemetry server
│   └── ui/                      # React + Vite + Tailwind dashboard
├── tests/
├── CLAUDE.md                    # agent rules (reframed — see 2.2)
├── PROJECT_ARCHITECTURE.md
├── PROJECT_STATUS_AND_NEXT_STEPS.md
├── TECH_STACK.md
├── REPOSITORY_INFO.md
├── README.md                    # feature table: CURRENT / PLANNED / BLOCKED
├── CONTRIBUTING.md
├── LICENSE                      # MIT (OSS)
├── .gitignore
├── Makefile                     # init, dev, test, lint
└── package.json                 # root scripts (init, dev)
```

### 2.2 TRACE governance layer
- **`CLAUDE.md`**: keep the TRACE algorithm, but reframe the telemetry rule — "observability hooks are non-blocking by design; safety gates *may* block." Removes the contradiction flagged in the review.
- **`AGENT_CONTEXT_INDEX.json`**: per-role `allowed_files` / `forbidden_files` (Planner/Builder/Validator).
- **Permission rules in `settings.json`**: translate each role's "Forbidden" column into real allow/deny rules (e.g., Validator denied `Edit(src/**)`; Builder denied `Edit(TECH_STACK.md)`). This is what actually *enforces* Route/Assign in v1.
- **`scripts/preflight.sh`**: the Check-phase stop-gate (verifies deps + that the task is ratified) — invoked manually and/or via a PreToolUse hook.

### 2.3 Hooks (corrected structure)
All defined with the proper `event → [{ matcher, hooks: [handler] }]` nesting. Every handler does two things: **POST to the server** (live) **and append JSONL to `agent-logs/`** (durable sink, so a downed server never loses data).

| Event | Type | Purpose |
|---|---|---|
| `PreToolUse` | http | Emit *intent* ("about to run X") to the UI; optional security note. Hard limits via permission rules, not the hook. |
| `PostToolUse` | http | Emit `tool_name`, `duration_ms`, success/failure (real). For `Agent` matches, capture `totalTokens`/`totalDurationMs` (rare in v1). |
| `PostToolUseFailure` | http | Emit failures distinctly. |
| `UserPromptSubmit` | command/http | Increment the human-iteration counter (the honest "effort" proxy). |
| `PreCompact` | command | Snapshot state → `PROJECT_STATUS_AND_NEXT_STEPS.md` **before** memory loss; alert UI. |
| `SessionStart` | command (non-interactive) | On `resume`/`compact`, inject current `PROJECT_STATUS` into context. **Not** the wizard. |
| `Stop` | command/http | Finalize the session's evidence summary. |
| `statusLine` (separate config) | command | Stream `context_window.remaining_percentage` (+ token/cost) to the context-rot gauge. |

### 2.4 Telemetry & ROI
- **Live + evidence:** JSONL in `agent-logs/` (source of truth for the dashboard).
- **Approximate ROI:** enable Claude Code OTel (`CLAUDE_CODE_ENABLE_TELEMETRY=1`, Prometheus exporter) for `claude_code.token.usage`, `cost.usage`, `active_time.total`. The server reads these for the token/cost panels, which are **clearly labeled "approximate."** If telemetry is disabled, panels show "n/a" rather than fake numbers.

### 2.5 FastAPI backend (`src/server/`)
- `POST /api/telemetry/hook` — ingest hook events → append JSONL + update in-memory state.
- `GET /api/state` — current snapshot (active persona/phase, last tools, counters).
- `GET /api/stream` — **SSE** live feed (simpler than WebSockets, auto-reconnect).
- `GET /api/roi` — approximate token/cost/active-time (from OTel/Prometheus).
- `GET /api/evidence` — list `review-packages/`.
- Pydantic models for all payloads; bind to `127.0.0.1` only; optional shared-secret header.

### 2.6 React dashboard (`src/ui/`, Vite + Tailwind)
Panels:
1. **Active persona / phase** (label-based in v1).
2. **Live tool-intent timeline** (real).
3. **Per-tool durations + success/failure** (real).
4. **Context-rot gauge** from `remaining_percentage` with threshold warnings (real). *(Note: `remaining_percentage` already nets out the ~33K autocompact buffer = true free space.)*
5. **Token / cost ROI** (approximate, labeled).
6. **Human iterations** counter (real, from `UserPromptSubmit`).
7. **Evidence browser** — review-packages (real).

### 2.7 Onboarding (`scripts/setup.sh`)
- Run explicitly via `npm run init` / `make init` (**not** `SessionStart`).
- Prompts: project name & description, roles, tech stack → populates `agent-context/`, `TECH_STACK.md`, `REPOSITORY_INFO.md`.
- Idempotent (sentinel file); safe to re-run.

### 2.8 GitHub setup (professional)
- Create repo (public OSS), MIT license, topics/description, README with badges and a CURRENT/PLANNED/BLOCKED feature table.
- **Branch protection on `main`** (no direct pushes) — this *operationalizes* TRACE's human-approval gate.
- PR template requiring a linked review-package; issue templates; `CODEOWNERS`.
- CI (`ci.yml`): lint (ruff/eslint) + tests on PR.
- `.gitignore` excludes `agent-logs/*.jsonl` and local env.

### 2.9 Token efficiency baked in (from the token-optimization skill)
TRACE should practice what it measures. Ship a documented recommended `~/.claude/settings.json`:
```json
{ "model": "sonnet",
  "env": { "MAX_THINKING_TOKENS": "10000", "CLAUDE_CODE_SUBAGENT_MODEL": "haiku" } }
```
Plus README guidance: `/clear` between unrelated tasks, `/compact` at breakpoints, `/cost` to check spend. (The `haiku` subagent setting becomes directly relevant in v2.)

### v1 Definition of Done
Clone → `npm run init` → run a Claude Code session → dashboard shows real live timeline, durations, context gauge, evidence, and an approximate ROI panel → PRs gated on `main` with a review-package. Hooks fire (corrected structure verified via `/hooks`).

---

## 3. Version 2 — detailed build

1. **Real subagents** — `.claude/agents/{planner,builder,validator}.md` with scoped `tools` + `permissions`. Unlocks **per-agent token telemetry** (`PostToolUse` on `Agent` completion) and **enforced** Route/Assign (runtime isolation, not just deny rules). Set `CLAUDE_CODE_SUBAGENT_MODEL=haiku` for cheap exploration.
2. **SQLite analytics** — derived from the JSONL; cross-session history, ROI trends, baseline-vs-TRACE A/B comparison, per-PR cost attribution.
3. **Team / multi-user** — authenticated ingest endpoint, multi-session aggregation, optional hosted dashboard, per-user/per-repo rollups.
4. **Advanced gates** — `PreToolUse` `prompt`/`agent` hooks for semantic security checks beyond path rules.
5. **Distribution** — published template repo / `degit` / cookiecutter, optional `npx create-trace` CLI.

---

## 4. Proposed implementation sequence (when you approve)

1. Scaffold repo structure + baseline files (README, LICENSE, .gitignore, status docs).
2. Fix & wire `.claude/settings.json` (corrected hooks) + permission rules + hook scripts.
3. FastAPI server (ingest, state, SSE, evidence) + JSONL sink.
4. React/Vite/Tailwind dashboard panels.
5. `setup.sh` init wizard + Makefile/package.json scripts.
6. statusLine + PreCompact context-rot loop.
7. OTel approximate-ROI wiring.
8. Tests + CI; verify hooks via `/hooks`; run an end-to-end TRACE session as the acceptance test.
9. Initialize git, push to GitHub, configure branch protection + templates.

---

## 5. Confirmations needed before implementation

1. **Storage:** OK with JSONL (v1) + GitHub-for-evidence, SQLite deferred to v2? *(my recommendation above)*
2. **Stack specifics:** Python 3.11+ / FastAPI / Uvicorn backend; React 18 + Vite + Tailwind frontend; package manager (npm vs pnpm) — OK?
3. **GitHub:** repo name (`trace`?), **public** or private, and your GitHub username/org. Auth method for pushing — GitHub connector, or you run `gh`/`git push` locally?
4. **License:** MIT (typical for OSS templates) — confirm.
