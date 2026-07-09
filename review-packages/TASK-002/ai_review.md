# Advisory review — TASK-002 (evidence browser lists files)

**Change:** `/api/evidence` now adds a `files` list (name + size) for each
review-package *directory*, so the dashboard evidence browser can show the actual
proof files inside a task folder instead of an opaque directory entry.

**Scope:** clean — only `src/server/main.py` and `tests/test_server.py` changed.

**Claim vs reality:** confirmed — `ruff` exit 0, `pytest` all green, including the
new `test_evidence_lists_files_inside_review_packages`.

Findings:
- [GOOD] Backward compatible: existing `name/is_dir/size_bytes` fields unchanged;
  `files` is additive, so the current UI won't break.
- [NIT] One level deep only (doesn't recurse into nested sub-dirs). Fine — review
  packages are flat today. Note it so a future nested layout isn't a surprise.
- [NIT] No explicit ordering guarantee surfaced to the client beyond sorted-by-name.

**Recommendation: APPROVE.**
