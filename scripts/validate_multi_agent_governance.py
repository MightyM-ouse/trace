#!/usr/bin/env python3
"""Validate project-neutral TRACE governance contracts."""

from __future__ import annotations

import json
import re
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
SHA = re.compile(r"^[0-9a-f]{40}$")

REQUIRED_FILES = [
    "AGENTS.md",
    "docs/governance/MULTI_AGENT_EXECUTION_POLICY.md",
    "docs/governance/EVIDENCE_AND_ARTIFACT_POLICY.md",
    "docs/governance/SOURCE_OF_TRUTH.md",
    "docs/adoption/apply-trace-to-your-project.md",
    "docs/architecture.md",
    "trace/ACTIVE_WORK_REGISTRY.yaml",
    "trace/ROLE_REGISTRY.yaml",
    "trace/WORKFLOWS.yaml",
    "trace/CELESTIAL_INDEX.json",
    "trace/AGENT_ROUTING_MATRIX.yaml",
    "trace/schemas/agent_handoff.schema.json",
]


def fail(message: str) -> None:
    raise AssertionError(message)


def load_json(path: str) -> Any:
    return json.loads((ROOT / path).read_text(encoding="utf-8"))


def load_yaml(path: str) -> Any:
    return yaml.safe_load((ROOT / path).read_text(encoding="utf-8"))


def require_text(path: str, tokens: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in text]
    if missing:
        fail(f"{path} missing required tokens: {missing}")


def validate_schema_shape(schema: dict[str, Any], status_vocabulary: list[str]) -> None:
    expected_required = {
        "schema_version",
        "task",
        "provenance",
        "repository_state",
        "synchronization",
        "outcome",
        "changes",
        "downloads",
        "validation",
        "deviations",
        "impacts",
        "decisions_required",
        "recommended_next_action",
    }
    missing = expected_required - set(schema.get("required", []))
    if missing:
        fail(f"handoff schema missing required keys: {sorted(missing)}")

    schema_status = schema["$defs"]["task_status"]["enum"]
    if schema_status != status_vocabulary:
        fail("handoff schema task_status enum must match ACTIVE_WORK_REGISTRY status_vocabulary")

    provenance = schema["properties"]["provenance"]
    required = set(provenance["required"])
    if not {"intended_reviewer", "review_status", "review_completed_by"}.issubset(required):
        fail("handoff provenance must distinguish intended reviewer from completed review")


def validate_active_work(registry: dict[str, Any]) -> None:
    vocabulary = registry["status_vocabulary"]
    tasks = registry.get("active_tasks", [])
    ids = [task["task_id"] for task in tasks]
    branches = [task["branch"] for task in tasks]
    if len(ids) != len(set(ids)):
        fail("active task IDs must be unique")
    if len(branches) != len(set(branches)):
        fail("active task branches must be unique")
    for task in tasks:
        if task.get("status") not in vocabulary:
            fail(f"{task['task_id']} has status outside governed vocabulary")
        if not task.get("writable_paths"):
            fail(f"{task['task_id']} must declare writable_paths")
        if "starting_commit" in task and not SHA.fullmatch(task["starting_commit"]):
            fail(f"{task['task_id']} starting_commit must be a full SHA")


def main() -> int:
    for path in REQUIRED_FILES:
        if not (ROOT / path).exists():
            fail(f"required governance file missing: {path}")

    active = load_yaml("trace/ACTIVE_WORK_REGISTRY.yaml")
    schema = load_json("trace/schemas/agent_handoff.schema.json")
    workflows = load_yaml("trace/WORKFLOWS.yaml")
    roles = load_yaml("trace/ROLE_REGISTRY.yaml")
    index = load_json("trace/CELESTIAL_INDEX.json")
    routing = load_yaml("trace/AGENT_ROUTING_MATRIX.yaml")

    validate_schema_shape(schema, active["status_vocabulary"])
    validate_active_work(active)

    outcomes = set(workflows["synchronization_gate"]["outcomes"])
    if outcomes != {"SYNC_PASS", "SYNC_BLOCKED", "SYNC_UNVERIFIED_LOCAL_STATE"}:
        fail("workflow synchronization outcomes are incomplete")
    if roles["meta"]["final_authority"] != "product_owner_or_maintainer":
        fail("role registry must preserve human final authority")
    if routing["agents"]["runtime_worker"]["status"] != "inactive":
        fail("runtime worker must remain inactive by default")

    routed = index["areas"]["trace-governance"]["source_files"]
    for required in ["trace/ACTIVE_WORK_REGISTRY.yaml", "trace/templates/", "trace/schemas/"]:
        if required not in routed:
            fail(f"CELESTIAL_INDEX does not route {required}")

    require_text("docs/architecture.md", ["```mermaid", "Telemetry Plane", "Worker Governance Plane"])
    require_text("README.md", ["docs/architecture.md", "Reusable governance templates"])
    require_text("TRACE_AUTO_RESEARCH_EXTENSION.md", ["Draft", "not a live autonomous dispatch system"])

    print("TRACE governance validation: PASS")
    print(f"governed status vocabulary: {len(active['status_vocabulary'])} values")
    print("handoff schema, routing matrix, and workflow contracts: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, TypeError, ValueError) as exc:
        print(f"TRACE governance validation: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
