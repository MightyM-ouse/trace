# Advisory review — TASK-003 (harden ingest token check)

**Change:** the `/api/telemetry/hook` auth check replaced the plain `!=` string
compare with `hmac.compare_digest(...)` over UTF-8 bytes. This removes a
timing-side-channel: `!=` can short-circuit on the first differing byte, letting an
attacker infer the secret byte-by-byte; `compare_digest` is constant-time.

**Scope:** clean — only `src/server/main.py` (added `import hmac`, 1 hunk) and
`tests/test_server.py` (1 new test). Nothing else touched.

**Claim vs reality:** confirmed — `ruff` exit 0; `pytest` 7 passed including the new
`test_ingest_hook_requires_correct_token` (wrong token → 401, correct token → 200).

Findings:
- [GOOD] Behavior unchanged for valid/invalid tokens; only the comparison method
  changed. Encoding to bytes avoids `compare_digest`'s ASCII-only TypeError on
  non-ASCII secrets.
- [GOOD] No-token mode (`INGEST_TOKEN == ""`) still skips auth, as before.
- [NIT] This is a defense-in-depth hardening; the server already binds to
  127.0.0.1, so exposure is low — but the fix is cheap and correct.

**Recommendation: APPROVE.**
