"""Filesystem locations for TRACE telemetry."""
import os
from pathlib import Path


def project_dir() -> Path:
    env = os.environ.get("TRACE_PROJECT_DIR") or os.environ.get("CLAUDE_PROJECT_DIR")
    if env:
        return Path(env)
    # src/server/paths.py -> project root is two parents up.
    return Path(__file__).resolve().parents[2]


def logs_dir() -> Path:
    d = project_dir() / "agent-logs"
    d.mkdir(parents=True, exist_ok=True)
    return d


def db_path() -> Path:
    return logs_dir() / "trace.db"


def jsonl_path() -> Path:
    return logs_dir() / "events.jsonl"


def context_path() -> Path:
    return logs_dir() / "context.json"


def review_packages_dir() -> Path:
    d = project_dir() / "review-packages"
    d.mkdir(parents=True, exist_ok=True)
    return d
