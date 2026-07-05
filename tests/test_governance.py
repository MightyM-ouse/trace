import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS_DIR))

import check_changed_path_ownership as ownership  # noqa: E402
import validate_multi_agent_governance as governance  # noqa: E402


def test_governance_validator_passes():
    assert governance.main() == 0


def test_changed_path_ownership_allows_task_owned_paths():
    registry = {
        "status_vocabulary": ["IN_PROGRESS", "MERGED", "CLOSED"],
        "active_tasks": [
            {
                "task_id": "TASK-001",
                "branch": "codex/task-001",
                "status": "IN_PROGRESS",
                "writable_paths": ["src/server/", "tests/test_server.py"],
                "shared_paths": [],
            }
        ],
    }

    ok, unauthorized, reason = ownership.evaluate(
        registry,
        "codex/task-001",
        ["src/server/main.py", "tests/test_server.py"],
    )

    assert ok is True
    assert unauthorized == []
    assert "TASK-001" in reason


def test_changed_path_ownership_fails_closed_for_unregistered_branch():
    registry = {
        "status_vocabulary": ["IN_PROGRESS", "MERGED", "CLOSED"],
        "active_tasks": [],
    }

    ok, unauthorized, reason = ownership.evaluate(registry, "codex/missing", ["src/server/main.py"])

    assert ok is False
    assert unauthorized == ["src/server/main.py"]
    assert "no registered active task" in reason

