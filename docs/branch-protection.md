# Branch protection — operationalizing the human-approval gate

TRACE's "E" (Evidence/approval) phase says no unreviewed code reaches `main`. On GitHub,
branch protection enforces that.

## Web UI
Repo → **Settings** → **Branches** → **Add branch ruleset** (or classic protection rule),
target `main`, then enable:
- **Require a pull request before merging** — blocks direct pushes to `main`.
- **Require status checks to pass** — select the CI jobs (Backend, Frontend).
- *(Optional)* **Require approvals** (1) once a second reviewer exists.
- **Do not allow bypassing the above settings** so the rule applies to admins too.

## `gh` CLI
```bash
gh api -X PUT repos/<owner>/trace/branches/main/protection --input - <<'JSON'
{
  "required_status_checks": { "strict": true, "contexts": ["Backend (FastAPI)", "Frontend (React + Vite)"] },
  "enforce_admins": true,
  "required_pull_request_reviews": { "required_approving_review_count": 0 },
  "restrictions": null
}
JSON
```

## Solo-maintainer note
GitHub won't let you approve your own PR. As a single maintainer, keep
`required_approving_review_count: 0` (you still get the PR + CI checkpoint before merge)
and raise it to `1` once someone else is on the repo. If you need to self-merge during
early development, set `enforce_admins: false`.
