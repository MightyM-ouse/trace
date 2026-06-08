# Review Packages

Portable, **real** evidence the human reviews as the final approval gate (the "E" in TRACE).
Each code change produces one package — a folder or zip named like `taskflow_review_pkg_v1/`:

| File | What it proves |
|------|----------------|
| `git_diff.patch` | Exact code mutations proposed |
| `test_logs.txt` | Raw output from the test runners (pytest / vitest) |
| `validation_report.json` | Structured pass/fail metrics + identified risks |
| `EXECUTION_PROMPT.md` | The original context/instructions given to the agent |

The Validator role assembles the package; the Builder never self-approves. The dashboard's
Evidence panel lists what's here. These files are committed to git — they are the durable,
version-controlled record of what shipped (unlike the local, approximate telemetry).

> Tip: the Validator can build a package with
> `git diff > review-packages/<name>/git_diff.patch` plus the test logs and a short
> `validation_report.json` of the form `{ "passed": 12, "failed": 0, "risks": [] }`.
