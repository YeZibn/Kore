"""Tool executor — executes tool calls from LLM responses."""

from __future__ import annotations

import asyncio
import json
import logging
import time
from typing import Any

from pydantic import ValidationError

from kore.llm.base import ToolCall
from kore.tools.base import ToolResult
from kore.tools.registry import ToolRegistry

logger = logging.getLogger(__name__)


class ToolExecutor:
    """Executes tool calls from LLM responses."""

    def __init__(
        self,
        registry: ToolRegistry,
        retry_count: int = 0,
        default_timeout_seconds: float | None = 30.0,
    ) -> None:
        self.registry = registry
        self.retry_count = retry_count
        self.default_timeout_seconds = default_timeout_seconds

    async def execute(self, tool_calls: list[ToolCall]) -> list[ToolResult]:
        """Execute a list of tool calls and return results."""
        results = []
        for call in tool_calls:
            result = await self._execute_single(call)
            results.append(result)
        return results

    async def _execute_single(self, call: ToolCall) -> ToolResult:
        """Execute a single tool call with retry."""
        started_at = time.perf_counter()
        definition = self.registry.get(call.name)

        if definition is None:
            return ToolResult(
                call_id=call.id,
                name=call.name,
                ok=False,
                output=f"Error: tool '{call.name}' not found",
                error_type="not_found",
                metadata=self._metadata(started_at),
            )

        if definition.fn is None:
            return ToolResult(
                call_id=call.id,
                name=call.name,
                ok=False,
                output=f"Error: tool '{call.name}' has no implementation",
                error_type="execution_error",
                metadata=self._metadata(started_at),
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
                metadata=self._metadata(started_at),
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
                    metadata=self._metadata(started_at),
                )

        base_metadata = {
            "read_only": definition.read_only,
            "destructive": definition.destructive,
            "requires_confirmation": definition.requires_confirmation,
        }

        if definition.requires_confirmation:
            return ToolResult(
                call_id=call.id,
                name=call.name,
                ok=False,
                output=f"Tool '{call.name}' requires user confirmation before execution.",
                error_type="confirmation_required",
                metadata=self._metadata(
                    started_at,
                    confirmation_required=True,
                    **base_metadata,
                )
            )

        retry_count = definition.retry_count
        if retry_count is None:
            retry_count = self.retry_count
        timeout_seconds = definition.timeout_seconds
        if timeout_seconds is None:
            timeout_seconds = self.default_timeout_seconds

        last_error = None
        attempt_count = 0
        for attempt in range(retry_count + 1):
            attempt_count = attempt + 1
            try:
                if definition.args_model is not None:
                    coro = definition.fn(validated_args)
                else:
                    coro = definition.fn()
                result = await asyncio.wait_for(coro, timeout=timeout_seconds)
                logger.debug("Tool %s executed successfully", call.name)
                return ToolResult(
                    call_id=call.id,
                    name=call.name,
                    ok=True,
                    output=str(result),
                    metadata=self._metadata(
                        started_at,
                        attempt_count=attempt_count,
                        **base_metadata,
                    ),
                )
            except TimeoutError as e:
                last_error = e
                logger.warning("Tool %s timed out (attempt %d)", call.name, attempt + 1)
            except Exception as e:
                last_error = e
                logger.warning("Tool %s failed (attempt %d): %s", call.name, attempt + 1, e)

        if isinstance(last_error, TimeoutError):
            return ToolResult(
                call_id=call.id,
                name=call.name,
                ok=False,
                output=f"Error: tool '{call.name}' timed out after {timeout_seconds} seconds",
                error_type="timeout",
                metadata=self._metadata(
                    started_at,
                    attempt_count=attempt_count,
                    timed_out=True,
                    **base_metadata,
                ),
            )

        return ToolResult(
            call_id=call.id,
            name=call.name,
            ok=False,
            output=f"Error: tool '{call.name}' failed after {retry_count + 1} attempts: {last_error}",
            error_type="execution_error",
            metadata=self._metadata(
                started_at,
                attempt_count=attempt_count,
                **base_metadata,
            ),
        )

    def _metadata(
        self,
        started_at: float,
        *,
        attempt_count: int = 0,
        timed_out: bool = False,
        confirmation_required: bool = False,
        **extra: Any,
    ) -> dict[str, Any]:
        return {
            "attempt_count": attempt_count,
            "duration_ms": int((time.perf_counter() - started_at) * 1000),
            "timed_out": timed_out,
            "confirmation_required": confirmation_required,
            **extra,
        }
