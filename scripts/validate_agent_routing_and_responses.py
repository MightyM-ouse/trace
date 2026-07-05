#!/usr/bin/env python3
"""Validate TRACE routing matrix and response contract docs."""

from __future__ import annotations

import sys
from pathlib import Path

try:
    import yaml
except ImportError as exc:  # pragma: no cover
    raise SystemExit("PyYAML is required by the routing validator") from exc

ROOT = Path(__file__).resolve().parents[1]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def require_tokens(path: str, tokens: list[str]) -> None:
    text = (ROOT / path).read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in text]
    require(not missing, f"{path} missing required tokens: {missing}")


def main() -> int:
    matrix = yaml.safe_load((ROOT / "trace/AGENT_ROUTING_MATRIX.yaml").read_text(encoding="utf-8"))
    agents = matrix["agents"]
    require("builder" in agents, "routing matrix must define builder")
    require("independent_validator" in agents, "routing matrix must define independent validator")
    require(agents["runtime_worker"]["status"] == "inactive", "runtime worker must be inactive by default")
    require(matrix["final_authority"] == "product_owner_or_maintainer", "human authority must remain final")

    routes = matrix["routes"]
    for route in [
        "architecture_design",
        "product_implementation",
        "independent_qa_security",
        "status_reconciliation",
    ]:
        require(route in routes, f"missing default route: {route}")

    require_tokens("docs/governance/MULTI_AGENT_EXECUTION_POLICY.md", ["SYNC_PASS", "APPROVE_TO_MERGE"])
    require_tokens("templates/workers/AGENTS.md", ["TRACE", "SYNC_PASS", "Evidence"])

    print("TRACE routing validation: PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (AssertionError, KeyError, TypeError, ValueError) as exc:
        print(f"TRACE routing validation: FAIL: {exc}", file=sys.stderr)
        raise SystemExit(1) from exc
