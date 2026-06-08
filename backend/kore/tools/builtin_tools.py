"""Built-in tools for testing and basic functionality."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

from pydantic import BaseModel, Field

from kore.tools.decorator import tool
from kore.tools.sandbox import FileSandbox


class GetCurrentTimeArgs(BaseModel):
    pass


class CalculateArgs(BaseModel):
    expression: str


class EchoArgs(BaseModel):
    text: str


class ListDirArgs(BaseModel):
    path: str = Field(default=".", description="Directory path relative to the workspace root.")
    max_entries: int = Field(default=200, ge=1, le=1000)


class ReadFileArgs(BaseModel):
    path: str = Field(description="File path relative to the workspace root.")
    max_chars: int = Field(default=20000, ge=1, le=200000)


class SearchTextArgs(BaseModel):
    path: str = Field(default=".", description="Directory or file path to search.")
    query: str = Field(min_length=1)
    max_results: int = Field(default=50, ge=1, le=500)


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


def create_file_tools(workspace_root: Path) -> list:
    """Create workspace-scoped read-only file tools."""
    sandbox = FileSandbox(workspace_root)

    @tool(
        name="list_dir",
        description="列出 workspace 内目录内容。访问 workspace 外路径时需要用户确认。",
        args_model=ListDirArgs,
        read_only=True,
        category="file",
    )
    async def list_dir(args: ListDirArgs) -> str:
        check = sandbox.check_path(args.path)
        if not check.resolved_path.exists():
            return f"Path not found: {check.resolved_path}"
        if not check.resolved_path.is_dir():
            return f"Not a directory: {check.resolved_path}"

        entries = []
        for index, child in enumerate(sorted(check.resolved_path.iterdir(), key=lambda p: p.name)):
            if index >= args.max_entries:
                entries.append(f"... truncated after {args.max_entries} entries")
                break
            suffix = "/" if child.is_dir() else ""
            entries.append(f"{child.name}{suffix}")
        return "\n".join(entries) if entries else "(empty directory)"

    @tool(
        name="read_file",
        description="读取 workspace 内文本文件。访问 workspace 外路径时需要用户确认。",
        args_model=ReadFileArgs,
        read_only=True,
        category="file",
    )
    async def read_file(args: ReadFileArgs) -> str:
        check = sandbox.check_path(args.path)
        if not check.resolved_path.exists():
            return f"Path not found: {check.resolved_path}"
        if not check.resolved_path.is_file():
            return f"Not a file: {check.resolved_path}"

        content = check.resolved_path.read_text(encoding="utf-8", errors="replace")
        if len(content) > args.max_chars:
            return content[: args.max_chars] + f"\n... truncated after {args.max_chars} chars"
        return content

    @tool(
        name="search_text",
        description="在 workspace 内文件或目录中搜索文本。访问 workspace 外路径时需要用户确认。",
        args_model=SearchTextArgs,
        read_only=True,
        category="file",
    )
    async def search_text(args: SearchTextArgs) -> str:
        check = sandbox.check_path(args.path)
        if not check.resolved_path.exists():
            return f"Path not found: {check.resolved_path}"

        files = [check.resolved_path] if check.resolved_path.is_file() else [
            path for path in check.resolved_path.rglob("*") if path.is_file()
        ]
        results = []
        for file_path in files:
            try:
                for line_number, line in enumerate(
                    file_path.read_text(encoding="utf-8", errors="replace").splitlines(),
                    start=1,
                ):
                    if args.query in line:
                        relative = file_path.relative_to(sandbox.workspace_root)
                        results.append(f"{relative}:{line_number}: {line}")
                        if len(results) >= args.max_results:
                            return "\n".join(results) + (
                                f"\n... truncated after {args.max_results} results"
                            )
            except OSError:
                continue
        return "\n".join(results) if results else "(no matches)"

    return [list_dir, read_file, search_text]


def get_builtin_tools(workspace_root: Path | None = None) -> list:
    """Return all built-in tool functions."""
    tools = [get_current_time, calculate, echo]
    if workspace_root is not None:
        tools.extend(create_file_tools(workspace_root))
    return tools
