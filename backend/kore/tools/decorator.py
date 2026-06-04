"""@tool decorator for simplified tool registration."""

from __future__ import annotations

import inspect
from typing import Any, Callable, Awaitable

from kore.tools.base import ToolDefinition


def tool(
    name: str,
    description: str,
    category: str = "general",
) -> Callable:
    """Decorator to register an async function as a tool.

    Usage:
        @tool(name="get_time", description="Get current time")
        async def get_time() -> str:
            return datetime.now().isoformat()
    """

    def decorator(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        # Build JSON Schema from function signature
        sig = inspect.signature(fn)
        properties: dict[str, Any] = {}
        required: list[str] = []

        for param_name, param in sig.parameters.items():
            param_type = "string"
            annotation = param.annotation
            if annotation is int:
                param_type = "integer"
            elif annotation is float:
                param_type = "number"
            elif annotation is bool:
                param_type = "boolean"

            properties[param_name] = {"type": param_type}

            if param.default is inspect.Parameter.empty:
                required.append(param_name)

        parameters_schema: dict[str, Any] = {
            "type": "object",
            "properties": properties,
        }
        if required:
            parameters_schema["required"] = required

        definition = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters_schema,
            fn=fn,
            category=category,
        )

        # Attach definition to the function
        fn._tool_definition = definition  # type: ignore[attr-defined]
        return fn

    return decorator


def get_definition(fn: Callable) -> ToolDefinition:
    """Extract ToolDefinition from a decorated function."""
    return fn._tool_definition  # type: ignore[attr-defined]
