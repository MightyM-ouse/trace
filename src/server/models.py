"""Pydantic models for TRACE telemetry payloads."""
from typing import Any, Optional

from pydantic import BaseModel, ConfigDict


class HookEvent(BaseModel):
    """A normalized lifecycle event as emitted by .claude/hooks/trace_hook.py.

    Lenient by design — the hook is the contract, and we accept extra fields so
    forward-compatible additions don't break ingestion.
    """

    model_config = ConfigDict(extra="allow")

    ts: Optional[str] = None
    event: Optional[str] = None
    session_id: Optional[str] = None
    tool_name: Optional[str] = None
    tool_intent: Optional[str] = None
    duration_ms: Optional[float] = None
    total_tokens: Optional[int] = None
    total_tool_use_count: Optional[int] = None
    usage: Optional[dict[str, Any]] = None
    agent_id: Optional[str] = None
    success: Optional[bool] = True
    context_rot_event: Optional[bool] = False
