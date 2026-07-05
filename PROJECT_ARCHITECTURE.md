# TRACE Project Architecture Blueprint

*Defines the physical structure of the TRACE template so any agent knows exactly what folders exist and what they mean.*

## 1. Directory structure

```
trace/
├── .claude/
│   ├── settings.json            # Lifecycle hooks (correct nesting) + permission rules
│   ├── hooks/                   # trace_hook.py (dual-sink), preflight.sh, statusline.sh
│   └── agents/                  # Subagent definitions (v2)
├── .github/
│   ├── workflows/ci.yml         # Lint + test on PR
│   ├── PULL_REQUEST_TEMPLATE.md # Requires a linked review-package
│   ├── ISSUE_TEMPLATE/
│   └── CODEOWNERS
├── agent-context/               # Context routing
│   ├── AGENT_CONTEXT_INDEX.json # Per-role allowed/forbidden files
│   ├── permission-profiles.json # Role → permission rules mapping
│   └── roles/                   # Planner / Builder / Validator role definitions
├── agent-logs/                  # Local telemetry (git-ignored): trace.db + events.jsonl
├── review-packages/             # Portable evidence (committed)
├── docs/                        # Architecture, ADRs, security
│   ├── governance/              # Source of truth, evidence, and multi-agent policy
│   └── adoption/                # How to apply TRACE to another project
├── scripts/                     # setup.sh (init wizard), preflight.sh
├── src/
│   ├── server/                  # FastAPI telemetry server (SQLite + SSE)
│   └── ui/                      # React + Vite + Tailwind dashboard
├── tests/
├── templates/                   # Reusable worker instruction templates
├── trace/                       # Project-neutral TRACE operating model
│   ├── templates/               # Task packet and handoff templates
│   ├── schemas/                 # JSON handoff schema
│   ├── tasks/                   # Adopting-project task packets
│   ├── evidence/                # Light Curves and governed handoffs
│   └── autoresearch/            # Draft/roadmap optimization extension
├── CLAUDE.md                    # Persistent agent instructions
├── PROJECT_ARCHITECTURE.md      # This file
├── PROJECT_STATUS_AND_NEXT_STEPS.md
├── TECH_STACK.md
├── REPOSITORY_INFO.md
├── README.md
├── CONTRIBUTING.md
├── LICENSE
├── Makefile
└── package.json
```

## 2. Telemetry dashboard (`src/server` & `src/ui`)

The local server listens on `http://127.0.0.1:8000`.

Endpoints:
- `POST /api/telemetry/hook` — ingest a lifecycle event (writes SQLite + appends JSONL WAL).
- `GET /api/state` — current snapshot (active role/phase, recent tools, counters).
- `GET /api/stream` — Server-Sent Events live feed.
- `GET /api/roi` — approximate token/cost/active-time (from OpenTelemetry; labeled approximate).
- `GET /api/evidence` — list of review-packages.

The React UI (Vite, `http://localhost:5173`) renders: active role/phase, live tool-intent timeline, per-tool durations + success/failure, a context-rot gauge (from the status line's `remaining_percentage`), an approximate ROI panel, a human-iteration counter, and an evidence browser.

## 3. Data: evidence vs telemetry

- **Evidence (real, committed to GitHub):** ADRs, `PROJECT_STATUS_AND_NEXT_STEPS.md`, `review-packages/`.
- **Telemetry (approximate, local):** `agent-logs/trace.db` (SQLite, WAL) is the queryable store; `agent-logs/events.jsonl` is the append-only write-ahead fallback replayed into SQLite on server start.

## 4. Reusable governance layer

TRACE ships a project-neutral governance layer under `trace/`:

- `TRACE_CONFIG.yaml` defines adopting-project posture and artifact paths.
- `STAR_MAP.md` is the human-readable current-state map.
- `ACTIVE_WORK_REGISTRY.yaml` is the canonical live task/ownership registry.
- `ROLE_REGISTRY.yaml`, `WORKFLOWS.yaml`, and `AGENT_ROUTING_MATRIX.yaml` define bounded roles, workflow gates, and routing defaults.
- `CELESTIAL_INDEX.json` routes context without requiring full-repo scans.
- `trace/templates/` and `trace/schemas/` define task packets and handoffs.

The architecture diagram is maintained as Mermaid in `docs/architecture.md`; PNG/SVG assets are fallback renders.

## 5. Interactive setup

`scripts/setup.sh` runs via `npm run init` / `make init` (an explicit human command — **not** a `SessionStart` hook, which cannot prompt interactively). It collects project name & description, roles, and tech stack, then populates `agent-context/`, `TECH_STACK.md`, and `REPOSITORY_INFO.md`. It is idempotent via a `.trace-initialized` sentinel.
