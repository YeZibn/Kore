"""Tool system base types."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable


@dataclass
class ToolDefinition:
    """Definition of a tool that can be called by the LLM."""

    name: str
    description: str
    parameters: dict[str, Any]  # JSON Schema for parameters
    fn: Callable[..., Awaitable[Any]] | None = None
    category: str = "general"

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
    output: str
    is_error: bool = False
