# TRACE Auto-Research & Loop Engineering Extension

*Version 1.0 - Draft / roadmap*

This is a design proposal, not a live autonomous dispatch system. It must not be presented
as implemented TRACE runtime behavior until an orchestrator, policy gate, scorer isolation,
and evidence workflow exist in the repository and pass review.

## Purpose

This document outlines an extension to the TRACE methodology that integrates loop engineering concepts and Karpathy-style auto‑research. The objective is to automate repetitive agent workflows, preserve project memory and governance, and accelerate optimization through measurable, autonomous experimentation. The extension builds on the TRACE core principles of repository sovereignty, clear roles, and evidence, and adds a loop engine to manage stateful agent workflows plus an auto‑research engine for objective improvements.

## Goals

- Reduce manual intervention in multi-agent loops.
- Ensure that every task follows a governed state machine with explicit stop conditions and human approval gates.
- Enable autonomous optimization of measurable assets (e.g. code runtime, prompt quality, context efficiency) using auto‑research cycles.
- Maintain transparency, evidence, and governance as defined in the TRACE core.

## Layered architecture

The extension adds two layers on top of the existing TRACE core:

1. **Loop Engine** – A state machine that routes tasks through predefined steps: intake, planning, review, implementation, validation, verification, final review, evidence, and closure. Each step is associated with a role and a tool. Transitions enforce retries and approval gates.

2. **Auto‑Research Engine** – A parallel mechanism for tasks that have an objective scoring function. It iteratively modifies an asset, runs a locked scorer, compares results, and keeps the better version. This loop continues until a stop condition is met.

These layers interact with TRACE’s repository artifacts (task packets, context indexes, evidence) without replacing them. The loop engine reads from and writes to `trace/tasks/` and `trace/evidence/`, while the auto‑research engine reads from `trace/autoresearch/` and writes experiment logs and winners.

## Loop Engine details

The loop engine is defined in `trace/ORBITAL_PATHS.yaml`. It specifies states, transitions, roles, tools, and max retries. An example state machine for an execution task is:

```yaml
workflow_id: governed_execution_v1
states:
  - task_intake
  - classify_mode
  - plan
  - review_plan
  - human_plan_approval
  - implement
  - validate
  - verify
  - final_review
  - evidence_update
  - human_close_approval
  - closed
transitions:
  task_intake:
    next: classify_mode
  classify_mode:
    if_investigation_needed: route_context
    if_execution_ready: plan
  plan:
    role: architect
    next: review_plan
  review_plan:
    role: reviewer
    if_approved: human_plan_approval
    if_rejected: plan
  human_plan_approval:
    required: true
    next: implement
  implement:
    role: developer
    next: validate
  validate:
    role: validator
    checks: [lint, tests, build]
    if_pass: verify
    if_fail: implement
    max_retries: 3
  verify:
    role: verifier
    if_pass: final_review
    if_fail: implement
    max_retries: 2
  final_review:
    role: final_reviewer
    if_approved: evidence_update
    if_rejected: implement
  evidence_update:
    output: trace/evidence/{task_id}_light_curve.md
    next: human_close_approval
  human_close_approval:
    required: true
    next: closed
```

Developers can customize this YAML for different modes (investigation, review, mixed).

## Auto‑Research Engine details

Auto‑research is suitable when the outcome can be measured by an objective metric with fast feedback. Each auto‑research task is defined by a YAML template stored in `trace/autoresearch/`. It contains:

- **goal** – the optimization objective.
- **locked_instructions** – a markdown file describing what the AI must not change.
- **editable_assets** – the files the AI is allowed to modify.
- **scorer** – a script or benchmark that produces a numerical score.
- **baseline** – the current best score.
- **success_rules** – criteria for keeping a new variant.
- **loop** – maximum iterations, time limits, and whether human review is required before accepting a winner.

### Example: Codex prompt optimization

```yaml
task_id: TRACE-OPT-001
mode: optimization
goal:
  improve: "Codex implementation prompt quality"
  target_metric: "test pass rate"
locked_instructions:
  path: trace/autoresearch/instructions/codex_prompt_guidelines.md
editable_assets:
  - trace/prompts/CODEX_IMPLEMENTATION_PROMPT.md
scorer:
  path: trace/autoresearch/scorers/codex_success_scorer.py
baseline:
  current_score: 0.68
success_rules:
  keep_change_if:
    score_improves_by_at_least: 0.03
    no_required_check_fails: true
    no_scope_violation: true
loop:
  max_iterations: 20
  max_runtime_minutes: 120
  require_human_review_before_merge: true
```

During auto‑research, the orchestrator clones the editable asset to a temporary file, generates a variation via an AI agent, runs the scorer on the variation and baseline, and compares scores. If the new score is better and passes all checks, it becomes the new baseline. All experiments and their outcomes are logged to `trace/autoresearch/EXPERIMENT_LEDGER.jsonl`.

### Directory structure for auto‑research

```
trace/autoresearch/
  instructions/            # Locked prompts that define the optimization goal
  scorers/                 # Objective scoring scripts
  baselines/               # Current best versions and scores
  winners/                 # Accepted improvements
  experiment_ledger.jsonl  # Append-only log of all experiments
  AUTO_RESEARCH_TASK_TEMPLATE.yaml  # Template for new tasks
```

### When to apply auto‑research

Only use auto‑research when all of the following are true:

1. The goal maps to an objective number (latency, accuracy, cost).
2. The feedback loop is fast (minutes or hours, not weeks).
3. The AI can modify the asset directly.
4. Failures are cheap and sandboxed.
5. The scorer is hard to game (e.g. multiple benchmarks or randomized tests).

Do not use auto‑research for subjective or slow‑feedback tasks such as UI aesthetics, product strategy, or long‑tail SEO rankings.

## Implementation guidelines

1. **Create `trace/ORBITAL_PATHS.yaml`** to define state machines for each workflow mode.
2. **Add `trace/autoresearch/`** with the template and initial scorer scripts.
3. **Update `trace/ROLE_REGISTRY.yaml` and `trace/prompts/`** to include specialized prompts for optimization and ensure roles are bound to the right tools.
4. **Implement orchestrator logic** (in Python or a workflow engine) that reads the YAML definitions, invokes the correct model (Claude, ChatGPT, Codex, etc.), applies permission rules from `agent-context/`, runs the scorer scripts, and writes evidence to `review-packages/`.
5. **Record all experiments** in `EXPERIMENT_LEDGER.jsonl` with fields: iteration, hypothesis, files changed, baseline score, new score, kept, and reason.
6. **Add benchmark suites** in `trace/benchmarks/` for regression tests and scoring reproducibility.
7. **Provide human approval gates** before accepting a winning variant into the repository.

## Recommended first optimization tasks

- **Codex implementation prompt** – reduce retries and scope violations.
- **Context routing rules** – increase context efficiency (relevant files read / total files read).
- **Test runtime** – reduce average test execution time.
- **Token cost** – minimize token usage per completed task without reducing quality.

## Conclusion

This extension allows TRACE to govern not only execution and review tasks but also continuous improvement via measurable optimization. By combining repository‑native memory (TRACE), stateful agent workflows (loop engineering), and objective experimentation (auto‑research), teams can reduce manual overhead, maintain trust and governance, and achieve faster, data‑driven improvements.
