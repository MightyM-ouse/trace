# Apply TRACE To Your Project

Use this guide to adapt TRACE to another repository without carrying over project-specific context.

## 1. Initialize The Repository

1. Copy the TRACE scaffold or run the setup wizard.
2. Fill `REPOSITORY_INFO.md`, `TECH_STACK.md`, and `PROJECT_ARCHITECTURE.md`.
3. Keep telemetry local and evidence in Git.

## 2. Choose Roles

Start with Planner, Builder, and Validator. Add worker adapters only when they reflect real tools your team uses.

Worker names such as ChatGPT, Claude, Codex, Antigravity, or an optional runtime worker are configurable examples, not mandatory TRACE dependencies.

## 3. Add Governance Files

Use the templates under `trace/` and `templates/workers/` to define:

- current-state map;
- active-work registry;
- role registry;
- workflow model;
- context routes;
- task packet;
- handoff schema;
- evidence format.

## 4. Run Work Through A Task Packet

Each task should have:

- outcome and acceptance criteria;
- assigned worker and reviewer;
- branch and starting commit;
- writable and read-only paths;
- validation and evidence requirements;
- escalation boundaries.

Do not edit `main` directly. Use a PR and keep human acceptance separate from worker execution.

## 5. Produce Evidence

For code changes, create a review package or Light Curve with the exact diff, test logs, validation report, task prompt, and known limitations.

Use Actions artifacts for large raw logs, videos, traces, and generated archives.

## 6. Keep Status Honest

Use `CURRENT`, `PLANNED`, `DRAFT`, `BLOCKED`, or `ROADMAP` consistently. Do not describe a concept, draft, or local experiment as an implemented TRACE feature.

