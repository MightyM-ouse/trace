#!/usr/bin/env python3
"""TRACE advisory AI reviewer.

Runs in CI on a pull request. Reviews the PR diff against the base branch and:
  1. writes a review-package under review-packages/<branch>/ai_review.md (evidence), and
  2. posts the review as a PR comment (so you read one ranked review, not every file).

ADVISORY ONLY. This script never fails the build on the basis of its findings —
deterministic checks (lint/tests/build) and human approval are the real gates.
It exits 0 even if the model flags issues; it only prints a warning and exits 0
if its own dependencies/keys are missing, so a misconfigured reviewer can't block.

Requires: ANTHROPIC_API_KEY (secret), GH_TOKEN (github.token), PR_NUMBER, BASE_REF.
"""
import os
import subprocess
import sys
from pathlib import Path

MODEL = "claude-sonnet-4-6"  # fast + cheap enough for per-PR review; swap as desired
MAX_DIFF_CHARS = 120_000     # keep the diff inside a sane token budget


def sh(*args: str) -> str:
    return subprocess.run(args, capture_output=True, text=True, check=False).stdout


def get_diff(base_ref: str) -> str:
    subprocess.run(["git", "fetch", "origin", base_ref, "--depth=1"], check=False)
    diff = sh("git", "diff", f"origin/{base_ref}...HEAD")
    if len(diff) > MAX_DIFF_CHARS:
        diff = diff[:MAX_DIFF_CHARS] + "\n\n[diff truncated for review budget]\n"
    return diff


PROMPT = """You are the Validator in a TRACE governed-execution loop. Review the
following pull-request diff and produce a concise, ranked review for a human who
will NOT read every file themselves.

Rules:
- Be specific: cite file + hunk. No generic praise.
- Rank findings by severity: [BLOCKER] / [MAJOR] / [MINOR] / [NIT].
- Flag scope creep (changes unrelated to the stated task), missing tests, and any
  claim in the code/comments that the diff does not actually support.
- End with a one-line recommendation: APPROVE, APPROVE-WITH-NITS, or REQUEST-CHANGES.
- Do not invent issues to seem thorough. If it's clean, say so.

DIFF:
```diff
{diff}
```"""


def main() -> int:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    base_ref = os.environ.get("BASE_REF", "main")
    pr_number = os.environ.get("PR_NUMBER", "")

    if not api_key:
        print("WARN: ANTHROPIC_API_KEY not set — skipping advisory review (non-blocking).")
        return 0

    diff = get_diff(base_ref).strip()
    if not diff:
        print("No diff against base — nothing to review.")
        return 0

    try:
        import anthropic
    except ImportError:
        print("WARN: anthropic SDK not installed — skipping advisory review.")
        return 0

    client = anthropic.Anthropic(api_key=api_key)
    resp = client.messages.create(
        model=MODEL,
        max_tokens=2000,
        messages=[{"role": "user", "content": PROMPT.format(diff=diff)}],
    )
    review = "".join(b.text for b in resp.content if getattr(b, "type", "") == "text")

    branch = sh("git", "rev-parse", "--abbrev-ref", "HEAD").strip() or "pr"
    out_dir = Path("review-packages") / branch.replace("/", "_")
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "ai_review.md").write_text(f"# Advisory AI review\n\n{review}\n")
    print(f"Wrote {out_dir / 'ai_review.md'}")

    # Post to the PR (best-effort; failure to comment must not fail the job).
    if pr_number and os.environ.get("GH_TOKEN"):
        body = f"## 🤖 TRACE advisory AI review\n\n{review}\n\n_Advisory only — does not gate merge._"
        subprocess.run(
            ["gh", "pr", "comment", pr_number, "--body", body],
            check=False, env={**os.environ},
        )
    print(review)
    return 0


if __name__ == "__main__":
    # Always exit 0: advisory reviewer must never block the pipeline.
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"WARN: advisory review errored (non-blocking): {exc}")
        sys.exit(0)
