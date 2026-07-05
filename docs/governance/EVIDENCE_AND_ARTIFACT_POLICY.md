# Evidence And Artifact Policy

## Commit To Git

- TRACE task packets and Light Curves.
- Requirement-to-change-to-test references.
- Concise test, build, and security summaries with commands and exit status.
- Key acceptance screenshots and small machine-readable reports.
- Architecture decisions, review findings, and release evidence.

## Store As Actions Artifacts

- Full raw logs, browser traces, videos, coverage HTML, large reports, generated ZIPs, dependency archives, and repeated screenshots.
- Link artifacts from the Light Curve or review package with workflow/run identity and retention.

## Never Store

Secrets, tokens, cookies, browser profiles, private keys, `.env` contents, personal data, private prompts containing credentials, or unredacted sensitive command output.

## Evidence Rules

- Preserve exact commands, tool versions, commit SHA, environment, result, and limitation.
- A file's existence is not proof that its claim is true.
- A test file is not proof that the test passed.
- A build does not prove product acceptance or release.
- Percentages require a defined numerator, denominator, method, and evidence source.
- Failed and skipped checks remain visible.

