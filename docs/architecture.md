# TRACE Architecture

This is the canonical architecture document for TRACE. It uses Mermaid because GitHub
renders Mermaid directly in Markdown, making the diagram readable in the repository and in
pull requests without separate tooling.

Existing PNG/SVG files are fallback renders only. Update this file first when the
architecture changes.

## Reading Guide

TRACE separates three concerns that are often mixed together in AI-assisted development:

| Concern | Purpose | Durable location |
|---|---|---|
| Governance | Decide who may do what, under which task envelope | `trace/`, `docs/governance/`, `templates/workers/` |
| Evidence | Prove what changed, what passed, what failed, and what remains | `review-packages/`, `trace/evidence/`, PRs |
| Telemetry | Observe local agent/tool activity and approximate ROI | `agent-logs/`, SQLite, dashboard |

The repository is the source of truth. Chat is a coordination surface, not the system of
record.

## Architecture Overview

```mermaid
flowchart TB
    User["Product Owner / Maintainer"]

    subgraph Governance["Governance Plane"]
        AGENTS["AGENTS.md\nRepository rules"]
        WorkerTemplates["templates/workers\nWorker adapters"]
        TraceConfig["trace/*.yaml + CELESTIAL_INDEX.json\nRoles, routes, workflow, ownership"]
        Policies["docs/governance\nSource of truth, evidence, execution policy"]
    end

    subgraph Work["Work Execution Plane"]
        TaskPacket["trace/tasks\nApproved task packet"]
        Branch["Task branch / worktree"]
        PR["Pull request\nHuman review gate"]
        Main["main\nAccepted history"]
    end

    subgraph Workers["Worker Governance Plane"]
        Architect["System architect\nsync, route, review"]
        Planner["Planner\narchitecture and requirements"]
        Builder["Builder\nimplementation and tests"]
        Validator["Validator\nindependent review"]
        Runtime["Optional runtime worker\ninactive by default"]
    end

    subgraph Validation["Validation Plane"]
        ProductCI["Backend/frontend CI"]
        GovCI["Governance validators"]
        Ownership["Changed-path ownership"]
        Schema["Handoff schema validation"]
    end

    subgraph Evidence["Evidence Plane"]
        ReviewPkg["review-packages\nDiffs, logs, validation reports"]
        LightCurve["trace/evidence\nLight Curves and handoffs"]
        Decisions["PROJECT_STATUS + PR history\nCurrent status and decisions"]
    end

    subgraph Telemetry["Telemetry Plane"]
        Hooks["Claude hooks\nTool events"]
        Jsonl["agent-logs/events.jsonl\nWrite-ahead fallback"]
        Sqlite["agent-logs/trace.db\nLocal projection"]
        Dashboard["React dashboard\nApproximate ROI"]
    end

    User --> AGENTS
    AGENTS --> WorkerTemplates
    AGENTS --> TraceConfig
    TraceConfig --> TaskPacket
    Policies --> TaskPacket

    TaskPacket --> Architect
    Architect --> Planner
    Architect --> Builder
    Architect --> Validator
    Architect -. activation required .-> Runtime

    Builder --> Branch
    Planner --> Branch
    Validator --> Branch
    Branch --> PR
    PR --> ProductCI
    PR --> GovCI
    GovCI --> Ownership
    GovCI --> Schema
    ProductCI --> PR
    Ownership --> PR
    Schema --> PR
    PR --> Main

    PR --> ReviewPkg
    PR --> LightCurve
    Main --> Decisions

    Hooks --> Jsonl
    Jsonl --> Sqlite
    Sqlite --> Dashboard
```

## Governed Task Lifecycle

Every meaningful change moves through an approved task envelope. Workers may choose the
method, but they may not widen scope, modify another task's owned paths, self-approve, or
merge.

```mermaid
stateDiagram-v2
    [*] --> Intake: request or issue
    Intake --> Route: identify outcome and context
    Route --> Packet: create task packet
    Packet --> SyncGate: verify repo state
    SyncGate --> Blocked: SYNC_BLOCKED or unverified local state
    SyncGate --> Assigned: SYNC_PASS
    Assigned --> Execute: worker acts inside envelope
    Execute --> Validate: run checks
    Validate --> Execute: fix within scope
    Validate --> Handoff: checks and limitations recorded
    Handoff --> Review: independent/system review
    Review --> Execute: CHANGES_REQUIRED
    Review --> Blocked: BLOCKED
    Review --> OwnerDecision: APPROVE_TO_MERGE recommendation
    OwnerDecision --> Main: maintainer merges
    Main --> StatusUpdate: reconcile status and evidence
    StatusUpdate --> [*]
    Blocked --> [*]
```

## Data And Evidence Flow

TRACE deliberately separates real evidence from approximate telemetry.

```mermaid
flowchart LR
    subgraph Real["Real / committed evidence"]
        Diff["Git diff"]
        Tests["Test and build logs"]
        Handoff["Markdown + JSON handoff"]
        PRRecord["PR discussion and review"]
    end

    subgraph Approx["Approximate / local telemetry"]
        ToolEvents["Tool events"]
        ContextGauge["Context-window gauge"]
        TokenCost["Token and cost snapshots"]
    end

    Diff --> Git["Git repository"]
    Tests --> Git
    Handoff --> Git
    PRRecord --> Git
    Git --> HumanGate["Human acceptance and merge"]

    ToolEvents --> Jsonl["events.jsonl"]
    ContextGauge --> Jsonl
    TokenCost --> Jsonl
    Jsonl --> Db["SQLite projection"]
    Db --> UI["Local dashboard"]
```

## Component Responsibilities

| Component | Responsibility | What it must not do |
|---|---|---|
| `AGENTS.md` | Repository-level TRACE rules | Override human authority |
| `templates/workers/` | Reusable worker adapter templates | Make a worker mandatory |
| `trace/ACTIVE_WORK_REGISTRY.yaml` | Live task status and path ownership | Become a broad allowlist |
| `trace/WORKFLOWS.yaml` | Synchronization and lifecycle rules | Replace PR review |
| `trace/schemas/agent_handoff.schema.json` | Machine-checkable handoff contract | Claim a review happened before evidence exists |
| Governance validators | Check contracts, status vocabulary, routing, and ownership | Merge, accept risk, or make product decisions |
| Telemetry hooks | Observe local tool activity | Block security-sensitive actions by themselves |
| Dashboard | Display local live state and approximate ROI | Claim product acceptance or release |

## Important Boundaries

- Runtime workers are optional and inactive by default.
- Auto-research is draft/roadmap, not a live autonomous dispatch system.
- Evidence in Git is real; token, cost, and effort metrics are approximate unless explicitly
  backed by measured data.
- Public source visibility does not authorize public runtime exposure, cloud execution,
  external messaging, paid services, or credential use.

