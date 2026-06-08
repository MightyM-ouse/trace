# REPOSITORY_INFO

- **Name:** trace
- **Visibility:** public
- **License:** MIT
- **Owner:** Vinay (vl.vinay2@gmail.com)
- **Purpose:** Open-source AI agent orchestration template + observability tool for AI-assisted software development.
- **Default branch:** `main` (protected — changes land via reviewed PRs, operationalizing TRACE's human-approval gate)
- **Version:** v1 (alpha)

## Conventions
- Commits: Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`).
- Branches: `feat/<slug>`, `fix/<slug>`, `docs/<slug>`.
- Every PR that changes code links a review-package in `review-packages/`.
- ADRs live in `docs/adr/` and are numbered (`0001-...`).

## Local ports
- FastAPI telemetry server: `127.0.0.1:8000`
- Vite dashboard: `localhost:5173`
