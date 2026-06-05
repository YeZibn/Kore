"""Tool system base types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable

from pydantic import BaseModel


@dataclass
class ToolDefinition:
    """Definition of a tool that can be called by the LLM."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema for parameters
    fn: Callable[..., Awaitable[Any]] | None = None
    category: str = "general"
    args_model: type[BaseModel] | None = None
    read_only: bool = False
    destructive: bool = False
    requires_confirmation: bool = False

    def to_openai_schema(self) -> dict[str, Any]:
        """Convert to OpenAI function calling schema."""
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters,
            },
        }


@dataclass
class ToolResult:
    """Result of a tool execution."""

    call_id: str
    name: str
    ok: bool
    output: str
    error_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
