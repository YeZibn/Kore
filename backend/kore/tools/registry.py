"""Tool registry — central registry for all available tools."""

from __future__ import annotations

from typing import Any

from kore.tools.base import ToolDefinition


class ToolRegistry:
    """Central registry for tool definitions."""

    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}

    def register(self, definition: ToolDefinition) -> None:
        """Register a tool definition."""
        self._tools[definition.name] = definition

    def get(self, name: str) -> ToolDefinition | None:
        """Get a tool by name."""
        return self._tools.get(name)

    def list_tools(self) -> list[ToolDefinition]:
        """List all registered tools."""
        return list(self._tools.values())

    def get_schemas(self) -> list[dict[str, Any]]:
        """Get OpenAI-compatible tool schemas for all registered tools."""
        return [tool.to_openai_schema() for tool in self._tools.values()]

    def has(self, name: str) -> bool:
        """Check if a tool is registered."""
        return name in self._tools
