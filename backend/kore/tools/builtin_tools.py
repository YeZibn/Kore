"""Built-in tools for testing and basic functionality."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel

from kore.tools.decorator import tool


class GetCurrentTimeArgs(BaseModel):
    pass


class CalculateArgs(BaseModel):
    expression: str


class EchoArgs(BaseModel):
    text: str


@tool(
    name="get_current_time",
    description="获取当前的日期和时间",
    args_model=GetCurrentTimeArgs,
    read_only=True,
)
async def get_current_time(args: GetCurrentTimeArgs) -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


@tool(
    name="calculate",
    description="计算数学表达式的结果，例如 '2 + 3 * 4' 或 'sqrt(16)'",
    args_model=CalculateArgs,
    read_only=True,
)
async def calculate(args: CalculateArgs) -> str:
    import math

    allowed_names = {k: v for k, v in math.__dict__.items() if not k.startswith("_")}
    allowed_names.update({"abs": abs, "round": round, "int": int, "float": float})

    try:
        result = eval(args.expression, {"__builtins__": {}}, allowed_names)  # noqa: S307
        return str(result)
    except Exception as e:
        return f"计算错误: {e}"


@tool(name="echo", description="回显输入的文本，用于测试工具调用", args_model=EchoArgs)
async def echo(args: EchoArgs) -> str:
    return args.text


def get_builtin_tools() -> list:
    """Return all built-in tool functions."""
    return [get_current_time, calculate, echo]
