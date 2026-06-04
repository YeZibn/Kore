"""Tool executor — executes tool calls from LLM responses."""

from __future__ import annotations

import json
import logging
from typing import Any

from kore.llm.base import ToolCall
from kore.tools.base import ToolResult
from kore.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes tool calls from LLM responses."""

    def __init__(self, registry: ToolRegistry, retry_count: int = 1) -> None:
        self.registry = registry
        self.retry_count = retry_count

    async def execute(self, tool_calls: list[ToolCall]) -> list[ToolResult]:
        """Execute a list of tool calls and return results."""
        results = []
        for call in tool_calls:
            result = await self._execute_single(call)
            results.append(result)
        return results

    async def _execute_single(self, call: ToolCall) -> ToolResult:
        """Execute a single tool call with retry."""
        definition = self.registry.get(call.name)

        if definition is None:
            return ToolResult(
                call_id=call.id,
                name=call.name,
                output=f"Error: tool '{call.name}' not found",
                is_error=True,
            )

        if definition.fn is None:
            return ToolResult(
                call_id=call.id,
                name=call.name,
                output=f"Error: tool '{call.name}' has no implementation",
                is_error=True,
            )

        # Parse arguments
        try:
            args = json.loads(call.arguments) if call.arguments else {}
        except json.JSONDecodeError:
            args = {}

        # Execute with retry
        last_error = None
        for attempt in range(self.retry_count + 1):
            try:
                result = await definition.fn(**args)
                logger.debug("Tool %s executed successfully", call.name)
                return ToolResult(
                    call_id=call.id,
                    name=call.name,
                    output=str(result),
                )
            except Exception as e:
                last_error = e
                logger.warning("Tool %s failed (attempt %d): %s", call.name, attempt + 1, e)

        return ToolResult(
            call_id=call.id,
            name=call.name,
            output=f"Error: tool '{call.name}' failed after {self.retry_count + 1} attempts: {last_error}",
            is_error=True,
        )
