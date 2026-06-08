# Contributing to TRACE

Thanks for your interest! TRACE is designed to be cloned, adapted, and improved.

## Ground rules
1. **Follow the TRACE algorithm.** Read `CLAUDE.md` and `PROJECT_ARCHITECTURE.md` before changing anything.
2. **Respect role boundaries.** If you're using an AI agent, keep it in its assigned role (see `agent-context/roles/`).
3. **Leave evidence.** Code PRs must link a review-package (diff + test logs + validation notes) in `review-packages/`.
4. **Keep the status file honest.** Update `PROJECT_STATUS_AND_NEXT_STEPS.md`; mark features CURRENT / PLANNED / BLOCKED.

## Workflow
```bash
git checkout -b feat/my-change
# ... make changes ...
make lint && make test
git commit -m "feat: short description"
git push origin feat/my-change
# open a PR; main is protected and requires review
```

## Dev setup
```bash
npm run init     # one-time interactive setup
make dev         # FastAPI :8000 + Vite :5173
make test        # backend + frontend tests
make lint        # ruff + eslint
```

## Reporting issues
Use the issue templates under `.github/ISSUE_TEMPLATE/`. Include your OS, Python/Node versions, and steps to reproduce.
