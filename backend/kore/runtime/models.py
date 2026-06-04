"""Core runtime models for Kore agent execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class RunMode(StrEnum):
    """Execution mode for a run."""

    DIRECT = "direct"
    PLAN = "plan"


class RunStatus(StrEnum):
    """Status of a run."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class RunContext:
    """Context for a single agent run."""

    run_id: str
    mode: RunMode = RunMode.DIRECT
    user_message: str = ""
    status: RunStatus = RunStatus.RUNNING
    total_tokens: int = 0
    total_tool_calls: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)
