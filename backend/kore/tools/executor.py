"""Tool executor — executes tool calls from LLM responses."""

from __future__ import annotations

import json
import logging
from typing import Any

from pydantic import ValidationError

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
                ok=False,
                output=f"Error: tool '{call.name}' not found",
                error_type="not_found",
            )

        if definition.fn is None:
            return ToolResult(
                call_id=call.id,
                name=call.name,
                ok=False,
                output=f"Error: tool '{call.name}' has no implementation",
                error_type="execution_error",
            )

        # Parse arguments
        try:
            args = json.loads(call.arguments) if call.arguments else {}
        except json.JSONDecodeError:
            return ToolResult(
                call_id=call.id,
                name=call.name,
                ok=False,
                output="Error: invalid JSON arguments",
                error_type="invalid_arguments",
            )

        validated_args: Any = args
        if definition.args_model is not None:
            try:
                validated_args = definition.args_model.model_validate(args)
            except ValidationError as exc:
                return ToolResult(
                    call_id=call.id,
                    name=call.name,
                    ok=False,
                    output=f"Error: invalid arguments for tool '{call.name}': {exc}",
                    error_type="invalid_arguments",
                )

        # Execute with retry
        last_error = None
        for attempt in range(self.retry_count + 1):
            try:
                if definition.args_model is not None:
                    result = await definition.fn(validated_args)
                else:
                    result = await definition.fn()
                logger.debug("Tool %s executed successfully", call.name)
                return ToolResult(
                    call_id=call.id,
                    name=call.name,
                    ok=True,
                    output=str(result),
                    metadata={
                        "read_only": definition.read_only,
                        "destructive": definition.destructive,
                        "requires_confirmation": definition.requires_confirmation,
                    },
                )
            except Exception as e:
                last_error = e
                logger.warning("Tool %s failed (attempt %d): %s", call.name, attempt + 1, e)

        return ToolResult(
            call_id=call.id,
            name=call.name,
            ok=False,
            output=f"Error: tool '{call.name}' failed after {self.retry_count + 1} attempts: {last_error}",
            error_type="execution_error",
            metadata={
                "read_only": definition.read_only,
                "destructive": definition.destructive,
                "requires_confirmation": definition.requires_confirmation,
            },
        )
