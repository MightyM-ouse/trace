#!/usr/bin/env python3
"""Task-specific changed-path ownership check for TRACE."""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit(
        "PyYAML is required. Install it with: python3 -m pip install -r scripts/governance-requirements.txt"
    ) from exc

ROOT = Path(__file__).resolve().parents[1]
REGISTRY_PATH = "trace/ACTIVE_WORK_REGISTRY.yaml"
INACTIVE_STATUSES = {"MERGED", "CLOSED"}


class OwnershipError(Exception):
    """Fail-closed identity/ownership error."""


def load_registry() -> dict[str, Any]:
    return yaml.safe_load((ROOT / REGISTRY_PATH).read_text(encoding="utf-8"))


def identify_task(registry: dict[str, Any], branch: str) -> dict[str, Any]:
    if not branch:
        raise OwnershipError("task identity missing: no branch provided")
    matches = [task for task in registry.get("active_tasks", []) if task.get("branch") == branch]
    if not matches:
        raise OwnershipError(f"no registered active task for branch '{branch}'")
    if len(matches) > 1:
        raise OwnershipError(f"ambiguous task identity for branch '{branch}'")
    task = matches[0]
    if task.get("status") in INACTIVE_STATUSES:
        raise OwnershipError(f"task '{task.get('task_id')}' is not active")
    if task.get("status") not in registry.get("status_vocabulary", []):
        raise OwnershipError(f"task '{task.get('task_id')}' status is outside vocabulary")
    return task


def allowed_paths_for_task(task: dict[str, Any]) -> set[str]:
    allowed = set(task.get("writable_paths", []))
    allowed.update(task.get("shared_paths", []))
    phase = task.get("correction_phase_modifies") or {}
    allowed.update(phase.get("files", []))
    allowed.add(REGISTRY_PATH)
    return allowed


def is_covered(path: str, allowed: set[str]) -> bool:
    return any(path == entry or (entry.endswith("/") and path.startswith(entry)) for entry in allowed)


def evaluate(registry: dict[str, Any], branch: str, changed: list[str]) -> tuple[bool, list[str], str]:
    try:
        task = identify_task(registry, branch)
    except OwnershipError as exc:
        return False, changed, str(exc)
    allowed = allowed_paths_for_task(task)
    unauthorized = [path for path in changed if not is_covered(path, allowed)]
    if unauthorized:
        return False, unauthorized, f"paths outside task '{task.get('task_id')}' envelope"
    return True, [], f"all paths within task '{task.get('task_id')}' envelope"


def resolve_branch(explicit: str | None) -> str:
    if explicit:
        return explicit
    env = os.environ.get("GITHUB_HEAD_REF") or os.environ.get("TRACE_BRANCH")
    if env:
        return env
    try:
        return subprocess.check_output(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    except Exception:
        return ""


def changed_via_git(base: str) -> list[str]:
    out = subprocess.check_output(["git", "diff", "--name-only", f"{base}...HEAD"], cwd=ROOT, text=True)
    return [line for line in out.splitlines() if line.strip()]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base")
    parser.add_argument("--branch")
    parser.add_argument("--paths", nargs="*")
    args = parser.parse_args()

    branch = resolve_branch(args.branch)
    if args.paths is not None:
        changed = args.paths
    elif args.base:
        changed = changed_via_git(args.base)
    else:
        parser.error("provide --base <ref> or --paths <files...>")

    ok, unauthorized, reason = evaluate(load_registry(), branch, changed)
    if not ok:
        print(f"changed-path ownership: FAIL (branch='{branch}'): {reason}", file=sys.stderr)
        for path in unauthorized:
            print(f"  unauthorized changed path: {path}", file=sys.stderr)
        return 1

    print(f"changed-path ownership: PASS (branch='{branch}', {len(changed)} changed file(s))")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
