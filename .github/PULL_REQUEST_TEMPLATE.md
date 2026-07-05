<!-- TRACE PR template — the human is the final approval gate (the "E" in TRACE). -->

## What changed
<!-- A short, factual summary of what was implemented. Must be real — no hallucinated capabilities. -->

## TRACE phase
- [ ] Template
- [ ] Route / Assign
- [ ] Check (preflight passed)
- [ ] Evidence

## Evidence (required for code changes)
Link the review-package in `review-packages/` and confirm it contains:
- [ ] `git_diff.patch` — exact code mutations
- [ ] `test_logs.txt` — raw test runner output
- [ ] `validation_report.json` — pass/fail metrics + identified risks
- [ ] `EXECUTION_PROMPT.md` — the context/instructions given to the agent

## Status
- [ ] `PROJECT_STATUS_AND_NEXT_STEPS.md` updated (features marked CURRENT / PLANNED / BLOCKED)

## Checklist
- [ ] CI green (backend tests + frontend build)
- [ ] Governance checks green when TRACE contracts, task packets, routing, or evidence schemas changed
- [ ] No secrets committed; `agent-logs/` not included
