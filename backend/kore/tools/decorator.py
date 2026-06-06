"""@tool decorator for simplified tool registration."""

from __future__ import annotations

from typing import Any, Callable, Awaitable

from pydantic import BaseModel

from kore.tools.base import ToolDefinition


def tool(
    name: str,
    description: str,
    args_model: type[BaseModel] | None = None,
    category: str = "general",
    read_only: bool = False,
    destructive: bool = False,
    requires_confirmation: bool = False,
    timeout_seconds: float | None = None,
    retry_count: int | None = None,
) -> Callable:
    """Decorator to register an async function as a tool.

    Usage:
        class GetTimeArgs(BaseModel):
            timezone: str | None = None

        @tool(name="get_time", description="Get current time", args_model=GetTimeArgs)
        async def get_time(args: GetTimeArgs) -> str:
            return datetime.now().isoformat()
    """

    def decorator(fn: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        if args_model is not None and not issubclass(args_model, BaseModel):
            raise TypeError("args_model must be a pydantic BaseModel subclass")

        parameters_schema = args_model.model_json_schema() if args_model is not None else {
            "type": "object",
            "properties": {},
        }

        definition = ToolDefinition(
            name=name,
            description=description,
            parameters=parameters_schema,
            fn=fn,
            category=category,
            args_model=args_model,
            read_only=read_only,
            destructive=destructive,
            requires_confirmation=requires_confirmation,
            timeout_seconds=timeout_seconds,
            retry_count=retry_count,
        )

        # Attach definition to the function
        fn._tool_definition = definition  # type: ignore[attr-defined]
        return fn

    return decorator


def get_definition(fn: Callable) -> ToolDefinition:
    """Extract ToolDefinition from a decorated function."""
    return fn._tool_definition  # type: ignore[attr-defined]
