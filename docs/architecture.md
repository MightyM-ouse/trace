# TRACE Architecture

This page is the canonical editable architecture diagram. GitHub renders Mermaid diagrams directly in Markdown, so this file is the source of truth for the diagram. Existing PNG/SVG assets are fallback renders only.

## System Overview

```mermaid
flowchart TB
    subgraph Core["TRACE Core Methodology"]
        T["Template\nRepo structure and durable docs"]
        R["Route\nContext index and scoped sources"]
        A["Assign\nRoles and worker boundaries"]
        C["Check\nPreflight, CI, validation"]
        E["Evidence\nReview packages and handoffs"]
        T --> R --> A --> C --> E
    end

    subgraph Repo["Repository Source Of Truth"]
        Tasks["Task packets\ntrace/tasks"]
        Registry["Active work registry\ntrace/ACTIVE_WORK_REGISTRY.yaml"]
        Decisions["Decisions and status\ntrace/STAR_MAP.md"]
        Evidence["Evidence\nreview-packages and trace/evidence"]
        PRs["Issues and PRs\nhuman approval gate"]
    end

    subgraph Workers["Worker Governance Plane"]
        Architect["System Architect\nrouting and review"]
        Claude["Architecture worker\noptional"]
        Codex["Implementation worker\noptional"]
        Validator["Independent validator\noptional"]
        Runtime["Runtime worker\noptional, inactive by default"]
    end

    subgraph Validation["Validation Plane"]
        CI["Backend/frontend CI"]
        GovCI["Governance validators"]
        Ownership["Changed-path ownership check"]
        Handoff["Handoff schema validation"]
    end

    subgraph Telemetry["Telemetry Plane"]
        Hooks["Claude hooks"]
        JSONL["events.jsonl\nwrite-ahead fallback"]
        SQLite["SQLite projection\nlocal"]
        UI["Dashboard\napproximate ROI"]
    end

    Core --> Tasks
    Tasks --> Registry
    Registry --> Workers
    Workers --> PRs
    PRs --> CI
    PRs --> GovCI
    GovCI --> Ownership
    GovCI --> Handoff
    CI --> Evidence
    Ownership --> Evidence
    Handoff --> Evidence
    Evidence --> PRs
    Hooks --> JSONL --> SQLite --> UI
    C --> CI
    E --> Evidence
```

## Execution Flow

```mermaid
stateDiagram-v2
    [*] --> TaskIntake
    TaskIntake --> Classify
    Classify --> Plan
    Plan --> HumanPlanApproval
    HumanPlanApproval --> Implement: approved
    HumanPlanApproval --> Plan: changes requested
    Implement --> Validate
    Validate --> Implement: checks fail and retries remain
    Validate --> NeedsHuman: retries exhausted
    Validate --> Verify: checks pass
    Verify --> Implement: review fails and retries remain
    Verify --> NeedsHuman: retries exhausted
    Verify --> HumanCloseApproval: evidence ready
    HumanCloseApproval --> Implement: changes requested
    HumanCloseApproval --> EvidenceUpdate: approved
    EvidenceUpdate --> Closed
    NeedsHuman --> [*]
    Closed --> [*]
```

## Data Contract

```mermaid
flowchart LR
    Real["Real, committed evidence\nDiffs, tests, handoffs, PRs"] --> Git["GitHub / Git repository"]
    Approx["Approximate local telemetry\nTokens, cost, active time"] --> Local["agent-logs JSONL and SQLite"]
    Git --> Review["Human review and merge"]
    Local --> Dashboard["Local dashboard"]
```

