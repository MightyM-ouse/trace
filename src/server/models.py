"""Pydantic models for TRACE telemetry payloads."""
from typing import Any

from pydantic import BaseModel, ConfigDict


class HookEvent(BaseModel):
    """A normalized lifecycle event as emitted by .claude/hooks/trace_hook.py.

    Lenient by design — the hook is the contract, and we accept extra fields so
    forward-compatible additions don't break ingestion.
    """

    model_config = ConfigDict(extra="allow")

    ts: str | None = None
    event: str | None = None
    session_id: str | None = None
    tool_name: str | None = None
    tool_intent: str | None = None
    duration_ms: float | None = None
    total_tokens: int | None = None
    total_tool_use_count: int | None = None
    usage: dict[str, Any] | None = None
    agent_id: str | None = None
    success: bool | None = True
    context_rot_event: bool | None = False
