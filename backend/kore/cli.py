"""User-facing CLI for Kore."""

from __future__ import annotations

import os
import json
import subprocess
import sys
import tempfile
import time
import uuid
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import httpx
import typer
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from prompt_toolkit.history import InMemoryHistory
from rich.align import Align
from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

DEFAULT_BASE_URL = "http://127.0.0.1:9899"
DEFAULT_TIMEOUT = 60.0
BACKEND_LOG_PATH = Path(tempfile.gettempdir()) / "kore-cli-backend.log"
REPL_COMMANDS = [
    "/help",
    "/status",
    "/model",
    "/thinking",
    "/thinking on",
    "/thinking off",
    "/trace on",
    "/trace off",
    "/workspace",
    "/chat restart",
    "/shutdown",
    "/server stop",
    "/server restart",
    "/quit",
    "/exit",
]
KORE_BANNER = r"""
                               =.
                               :
                               #=
      :+*##*+=.               =*+     .*
   =###+=::=+*###+.          =#=**
 :##+           :###+      +#*   +#*.
 ##=               =*+ .+#*:       .=*+=:..   .
.##:                 +##=.           =##*++. =+:
 ###             :*##=   =##*     +#*:
  =###:        *###+         =#* :#+
    .+##     ##*:              ###.
         ###                   .#+
                               :
                               =.

          __
         |  | __  ___   _ __   ___
         |  |/ / / _ \ | '__| / _ \
         |    < | (_) || |   |  __/
         |__|\_\ \___/ |_|    \___|
"""

console = Console()
app = typer.Typer(
    help="Kore user CLI.",
    add_completion=False,
    invoke_without_command=True,
    no_args_is_help=False,
    rich_markup_mode="rich",
)
model_app = typer.Typer(help="Inspect and switch models.", add_completion=False)
config_app = typer.Typer(help="Show and update provider config.", add_completion=False)
app.add_typer(model_app, name="model")
app.add_typer(config_app, name="config")


class BackendUnavailable(RuntimeError):
    """Raised when the local backend cannot be reached."""


def _base_url(value: str | None) -> str:
    return value or os.environ.get("KORE_CLI_BASE_URL", DEFAULT_BASE_URL)


def _client(base_url: str) -> httpx.Client:
    return httpx.Client(base_url=base_url, timeout=DEFAULT_TIMEOUT)


def _parse_host_port(base_url: str) -> tuple[str, int]:
    parsed = urlparse(base_url)
    host = parsed.hostname or "127.0.0.1"
    port = parsed.port or (443 if parsed.scheme == "https" else 80)
    return host, port


def _healthcheck(base_url: str) -> bool:
    try:
        with _client(base_url) as client:
            response = client.get("/health")
            return response.status_code == 200
    except httpx.HTTPError:
        return False


def _start_backend(base_url: str) -> None:
    host, port = _parse_host_port(base_url)
    log_file = BACKEND_LOG_PATH.open("w", encoding="utf-8")
    cmd = [
        sys.executable,
        "-m",
        "uvicorn",
        "kore.main:app",
        "--host",
        host,
        "--port",
        str(port),
    ]
    subprocess.Popen(
        cmd,
        stdout=log_file,
        stderr=subprocess.STDOUT,
        start_new_session=True,
    )


def _read_backend_log_tail() -> str:
    if not BACKEND_LOG_PATH.exists():
        return ""
    lines = BACKEND_LOG_PATH.read_text(encoding="utf-8", errors="ignore").splitlines()
    return "\n".join(lines[-8:])


def ensure_backend(base_url: str) -> None:
    if _healthcheck(base_url):
        return

    console.print(
        Panel(
            f"Local backend not reachable at [bold]{base_url}[/]. Starting it now.",
            title="Kore",
            border_style="yellow",
        )
    )
    _start_backend(base_url)

    for _ in range(40):
        if _healthcheck(base_url):
            console.print(
                Panel(
                    f"Backend is ready at [bold]{base_url}[/].",
                    title="Kore",
                    border_style="green",
                )
            )
            return
        time.sleep(0.25)

    log_tail = _read_backend_log_tail()
    message = f"Backend did not become ready at {base_url}."
    if log_tail:
        message = f"{message}\n\nLast startup log lines:\n{log_tail}"
    raise BackendUnavailable(message)


def request_json(
    method: str,
    path: str,
    *,
    base_url: str,
    json_body: dict[str, Any] | None = None,
) -> dict[str, Any]:
    ensure_backend(base_url)
    try:
        with _client(base_url) as client:
            response = client.request(method, path, json=json_body)
            response.raise_for_status()
            return response.json()
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text.strip() or str(exc)
        try:
            payload = exc.response.json()
            if isinstance(payload, dict) and payload.get("detail"):
                detail = str(payload["detail"])
        except ValueError:
            pass
        raise BackendUnavailable(detail) from exc
    except httpx.HTTPError as exc:
        raise BackendUnavailable(str(exc)) from exc


def render_error(message: str) -> None:
    console.print(Panel(message, title="Error", border_style="red"))


def center_ascii_art(art: str) -> str:
    """Trim shared indentation while preserving the art's internal spacing."""
    lines = [line.rstrip() for line in art.strip("\n").splitlines()]
    non_empty_lines = [line for line in lines if line.strip()]
    shared_indent = min(
        (len(line) - len(line.lstrip(" ")) for line in non_empty_lines),
        default=0,
    )
    return "\n".join(line[shared_indent:] if line.strip() else "" for line in lines)


def render_reply(reply: str, model: str, session_id: str) -> None:
    body = Markdown(reply) if reply.strip() else Text("(empty response)", style="dim")
    title = "Assistant"
    subtitle = f"{model}  session {session_id[:8]}"
    console.print(Panel(body, title=title, subtitle=subtitle, border_style="cyan"))


def render_help() -> None:
    """Render Chinese help for REPL commands."""
    table = Table(box=box.SIMPLE_HEAVY, expand=True)
    table.add_column("分类", style="bold cyan", width=12)
    table.add_column("命令", style="bold")
    table.add_column("说明", overflow="fold")

    rows = [
        ("对话", "直接输入内容", "发送消息给 Kore，进入普通 Agent 对话。"),
        ("对话", "/chat restart", "重开当前对话，生成新的 session，不重启后端。"),
        ("状态", "/status", "查看后端、健康状态、版本、模型、推理开关和工作空间等运行信息。"),
        ("模型", "/model", "列出当前正式可用模型，并标出当前模型。"),
        ("模型", "/model <模型名>", "切换当前模型；不存在或未接入的模型会提示错误。"),
        ("推理", "/thinking", "查看 DeepSeek thinking 当前开关状态。"),
        ("推理", "/thinking on", "开启 DeepSeek thinking。"),
        ("推理", "/thinking off", "关闭 DeepSeek thinking。"),
        ("轨迹", "/trace on", "开启实时执行轨迹，显示模型步骤和工具过程。"),
        ("轨迹", "/trace off", "关闭实时执行轨迹，只显示最终回答。"),
        ("工作空间", "/workspace", "查看当前文件工具沙箱的工作空间根目录。"),
        ("工作空间", "/workspace <路径>", "切换工作空间；路径必须存在且是目录。"),
        ("服务", "/shutdown", "关闭当前后端服务，并退出 REPL。"),
        ("服务", "/server stop", "/shutdown 的等价别名。"),
        ("服务", "/server restart", "重启当前后端服务，重启后留在 REPL 中继续使用。"),
        ("退出", "/quit", "只退出当前 REPL，不关闭后端服务。"),
        ("退出", "/exit", "/quit 的等价别名。"),
        ("帮助", "/help", "显示这份中文帮助。"),
    ]
    for row in rows:
        table.add_row(*row)

    console.print(Panel(table, title="Kore 帮助", subtitle="REPL 内部命令", border_style="blue"))


def render_welcome(
    *,
    base_url: str,
    model: str,
    thinking: str,
    trace: str,
    workspace_root: str,
    session_id: str,
    available_model_count: int,
) -> None:
    """Render the REPL welcome panel."""
    header = Align.center(
        Text(center_ascii_art(KORE_BANNER), style="bold cyan")
    )

    table = Table(box=box.SIMPLE, show_header=False, expand=True)
    table.add_row("后端", base_url)
    table.add_row("模型", model)
    table.add_row("可用模型", str(available_model_count))
    table.add_row("推理开关", thinking)
    table.add_row("Trace", trace)
    table.add_row("工作空间", workspace_root)
    table.add_row("Session", session_id[:8])
    table.add_row("常用命令", "/help  /status  /model  /trace on  /server restart")

    console.print(Panel(header, border_style="cyan"))
    console.print(Panel(table, title="Kore Runtime", border_style="blue"))


def render_status(base_url: str) -> None:
    health = request_json("GET", "/health", base_url=base_url)
    status = request_json("GET", "/api/status", base_url=base_url)
    models = request_json("GET", "/api/models/list", base_url=base_url)
    providers = request_json("GET", "/api/models/providers", base_url=base_url)
    workspace = request_json("GET", "/api/config/workspace", base_url=base_url)
    cli_config = request_json("GET", "/api/config/cli", base_url=base_url)

    summary = Table(box=box.SIMPLE, show_header=False, expand=True)
    summary.add_row("后端", base_url)
    summary.add_row("健康状态", health.get("status", "unknown"))
    summary.add_row("版本", status.get("version", "unknown"))
    summary.add_row("当前模型", models.get("current_model", "unknown"))
    summary.add_row("可用模型数", str(len(models.get("models", []))))
    summary.add_row("DeepSeek thinking", get_deepseek_thinking(base_url))
    summary.add_row("Trace", "on" if cli_config.get("trace_enabled") else "off")
    summary.add_row("工作空间", workspace.get("workspace_root", "unknown"))
    summary.add_row("工作空间有效", "yes" if workspace.get("is_directory") else "no")
    console.print(Panel(summary, title="Kore 状态", border_style="blue"))

    provider_table = Table(box=box.SIMPLE_HEAVY)
    provider_table.add_column("服务商", style="bold")
    provider_table.add_column("已配置")
    provider_table.add_column("Base URL", overflow="fold")
    for provider in providers.get("providers", []):
        configured = "[green]yes[/]" if provider["configured"] else "[red]no[/]"
        provider_table.add_row(provider["name"], configured, provider["base_url"])
    console.print(provider_table)


def render_trace_event(event: dict[str, Any]) -> None:
    """Render one public trace event using Rich panels."""
    event_type = event.get("type", "message")
    table = Table(box=box.SIMPLE, show_header=False, expand=True)
    border_style = "blue"
    title = event_type

    if event_type == "run_started":
        title = "Run Started"
        table.add_row("模型", str(event.get("model", "")))
        table.add_row("Session", str(event.get("session_id", ""))[:8])
        table.add_row("Run", str(event.get("run_id", ""))[:8])
    elif event_type == "llm_step_started":
        title = f"Agent Step {event.get('step')}"
        border_style = "cyan"
        table.add_row("阶段", "调用模型")
        table.add_row("模型", str(event.get("model", "")))
    elif event_type == "llm_step_completed":
        title = f"Step {event.get('step')} Completed"
        border_style = "cyan"
        table.add_row("工具调用数", str(event.get("tool_call_count", 0)))
        table.add_row("Tokens", str(event.get("tokens", 0)))
        if event.get("content_preview"):
            table.add_row("输出摘要", str(event.get("content_preview")))
    elif event_type == "llm_reasoning":
        title = f"Reasoning Step {event.get('step')}"
        border_style = "magenta"
        table.add_row("Provider", str(event.get("provider", "")))
        table.add_row("模型", str(event.get("model", "")))
        table.add_row("字符数", str(event.get("reasoning_chars", 0)))
        table.add_row("摘要", str(event.get("reasoning_preview", "")))
    elif event_type == "tool_call_started":
        title = "Tool Call"
        border_style = "yellow"
        table.add_row("工具", str(event.get("name", "")))
        table.add_row("状态", "running")
        table.add_row("参数", str(event.get("arguments", "")))
    elif event_type == "tool_call_completed":
        title = "Tool Result"
        border_style = "green" if event.get("ok") else "red"
        metadata = event.get("metadata") or {}
        table.add_row("工具", str(event.get("name", "")))
        table.add_row("状态", "ok" if event.get("ok") else "failed")
        table.add_row("错误类型", str(event.get("error_type") or "-"))
        table.add_row("耗时", f"{metadata.get('duration_ms', 0)}ms")
        table.add_row("输出摘要", str(event.get("output_preview", "")))
    elif event_type == "tool_confirmation_required":
        title = "Confirmation Required"
        border_style = "magenta"
        metadata = event.get("metadata") or {}
        table.add_row("工具", str(event.get("name", "")))
        table.add_row("请求路径", str(metadata.get("resolved_path", "")))
        table.add_row("工作空间", str(metadata.get("workspace_root", "")))
        table.add_row("原因", "workspace 外路径需要用户确认")
    elif event_type == "run_completed":
        title = "Run Completed"
        border_style = "green"
        table.add_row("Tokens", str(event.get("total_tokens", 0)))
        table.add_row("工具调用数", str(event.get("total_tool_calls", 0)))
    elif event_type == "run_failed":
        title = "Run Failed"
        border_style = "red"
        table.add_row("错误", str(event.get("error", "")))
    else:
        table.add_row("事件", json.dumps(event, ensure_ascii=False))

    console.print(Panel(table, title=title, border_style=border_style))


def stream_chat(base_url: str, message: str, session_id: str) -> dict[str, Any]:
    """Stream chat trace events and return the final event payload."""
    ensure_backend(base_url)
    final_event: dict[str, Any] = {}
    try:
        with _client(base_url) as client:
            with client.stream(
                "POST",
                "/api/chat/stream",
                json={"message": message, "session_id": session_id},
            ) as response:
                response.raise_for_status()
                data_lines: list[str] = []
                for line in response.iter_lines():
                    if not line:
                        if data_lines:
                            payload = json.loads("\n".join(data_lines))
                            render_trace_event(payload)
                            if payload.get("type") in {"run_completed", "run_failed"}:
                                final_event = payload
                            data_lines = []
                        continue
                    if line.startswith("event:"):
                        continue
                    elif line.startswith("data:"):
                        data_lines.append(line.split(":", 1)[1].strip())
                return final_event
    except httpx.HTTPStatusError as exc:
        detail = exc.response.text.strip() or str(exc)
        raise BackendUnavailable(detail) from exc
    except httpx.HTTPError as exc:
        raise BackendUnavailable(str(exc)) from exc


def render_models(base_url: str) -> None:
    data = request_json("GET", "/api/models/list", base_url=base_url)
    current = data.get("current_model", "")

    table = Table(box=box.SIMPLE_HEAVY)
    table.add_column("Model", style="bold")
    table.add_column("服务商")
    table.add_column("Current")

    for item in data.get("models", []):
        marker = "[green]current[/]" if item["name"] == current else ""
        table.add_row(item["name"], item["provider"], marker)

    console.print(Panel(f"Current model: [bold]{current}[/]", border_style="blue"))
    console.print(table)


def render_config(base_url: str) -> None:
    data = request_json("GET", "/api/config/models", base_url=base_url)
    table = Table(box=box.SIMPLE_HEAVY)
    table.add_column("服务商", style="bold")
    table.add_column("API Key")
    table.add_column("Base URL", overflow="fold")
    table.add_column("推理开关")
    for provider, cfg in data.get("providers", {}).items():
        thinking = cfg.get("thinking_enabled")
        thinking_text = "-" if thinking is None else ("on" if thinking else "off")
        table.add_row(provider, cfg.get("api_key", ""), cfg.get("base_url", ""), thinking_text)
    console.print(table)


def render_workspace(base_url: str) -> None:
    data = request_json("GET", "/api/config/workspace", base_url=base_url)
    table = Table(box=box.SIMPLE, show_header=False)
    table.add_row("path", data.get("workspace_root", ""))
    table.add_row("exists", "yes" if data.get("exists") else "no")
    table.add_row("directory", "yes" if data.get("is_directory") else "no")
    console.print(Panel(table, title="Workspace", border_style="blue"))


def update_workspace(base_url: str, workspace_root: str) -> None:
    data = request_json(
        "PUT",
        "/api/config/workspace",
        base_url=base_url,
        json_body={"workspace_root": workspace_root},
    )
    table = Table(box=box.SIMPLE, show_header=False)
    table.add_row("path", data.get("workspace_root", ""))
    table.add_row("exists", "yes" if data.get("exists") else "no")
    table.add_row("directory", "yes" if data.get("is_directory") else "no")
    console.print(Panel(table, title="Workspace Updated", border_style="green"))


def shutdown_backend(base_url: str) -> None:
    data = request_json("POST", "/api/server/shutdown", base_url=base_url)
    message = data.get("message", "Server shutdown requested.")
    console.print(Panel(message, title="Shutdown", border_style="yellow"))


def restart_backend(base_url: str) -> None:
    """Restart the local backend and wait until it becomes healthy again."""
    request_json("POST", "/api/server/shutdown", base_url=base_url)
    for _ in range(40):
        if not _healthcheck(base_url):
            break
        time.sleep(0.25)
    ensure_backend(base_url)
    console.print(Panel("Backend restarted.", title="Server Restarted", border_style="green"))


def get_deepseek_thinking(base_url: str) -> str:
    data = request_json("GET", "/api/config/models", base_url=base_url)
    deepseek = data.get("providers", {}).get("deepseek", {})
    thinking = deepseek.get("thinking_enabled")
    return "on" if thinking else "off"


def get_cli_trace(base_url: str) -> bool:
    data = request_json("GET", "/api/config/cli", base_url=base_url)
    return bool(data.get("trace_enabled"))


def update_cli_trace(base_url: str, enabled: bool) -> bool:
    data = request_json(
        "PUT",
        "/api/config/cli",
        base_url=base_url,
        json_body={"trace_enabled": enabled},
    )
    return bool(data.get("trace_enabled"))


def render_current_welcome(base_url: str, session_id: str, trace_enabled: bool | None = None) -> None:
    models = request_json("GET", "/api/models/list", base_url=base_url)
    workspace = request_json("GET", "/api/config/workspace", base_url=base_url)
    trace = get_cli_trace(base_url) if trace_enabled is None else trace_enabled
    render_welcome(
        base_url=base_url,
        model=models.get("current_model", "unknown"),
        thinking=get_deepseek_thinking(base_url),
        trace="on" if trace else "off",
        workspace_root=workspace.get("workspace_root", "unknown"),
        session_id=session_id,
        available_model_count=len(models.get("models", [])),
    )


def read_repl_input(prompt_session: PromptSession[str] | None) -> str:
    """Read one REPL input line with prompt_toolkit when attached to a TTY."""
    if prompt_session is None:
        return input("you> ")
    return prompt_session.prompt("you> ")


def run_chat_loop(base_url: str) -> None:
    ensure_backend(base_url)
    session_id = str(uuid.uuid4())
    trace_enabled = get_cli_trace(base_url)
    render_current_welcome(base_url, session_id, trace_enabled)
    prompt_session: PromptSession[str] | None = None
    if sys.stdin.isatty():
        prompt_session = PromptSession(
            history=InMemoryHistory(),
            completer=WordCompleter(REPL_COMMANDS, ignore_case=True, sentence=True),
            complete_while_typing=True,
        )

    while True:
        try:
            message = read_repl_input(prompt_session).strip()
        except (KeyboardInterrupt, EOFError):
            console.print()
            break

        if not message:
            continue

        if message in {"/exit", "/quit"}:
            break
        if message == "/help":
            render_help()
            continue
        if message == "/chat restart":
            session_id = str(uuid.uuid4())
            console.print(
                Panel(
                    f"已重开对话。新的 session: [bold]{session_id[:8]}[/]",
                    title="Chat Restarted",
                    border_style="green",
                )
            )
            render_current_welcome(base_url, session_id, trace_enabled)
            continue
        if message == "/status":
            render_status(base_url)
            continue
        if message == "/model":
            render_models(base_url)
            continue
        if message == "/thinking":
            console.print(f"DeepSeek thinking: [bold]{get_deepseek_thinking(base_url)}[/]")
            continue
        if message == "/trace on":
            trace_enabled = update_cli_trace(base_url, True)
            console.print(Panel("实时执行轨迹：on（已持久化）", title="Trace", border_style="green"))
            continue
        if message == "/trace off":
            trace_enabled = update_cli_trace(base_url, False)
            console.print(Panel("实时执行轨迹：off（已持久化）", title="Trace", border_style="yellow"))
            continue
        if message == "/workspace":
            try:
                render_workspace(base_url)
            except BackendUnavailable as exc:
                render_error(str(exc))
            continue
        if message.startswith("/workspace "):
            workspace_root = message.split(" ", 1)[1].strip()
            if not workspace_root:
                render_error("Provide a workspace path.")
                continue
            try:
                update_workspace(base_url, workspace_root)
            except BackendUnavailable as exc:
                render_error(str(exc))
            continue
        if message in {"/shutdown", "/server stop"}:
            try:
                shutdown_backend(base_url)
            except BackendUnavailable as exc:
                render_error(str(exc))
                continue
            break
        if message == "/server restart":
            try:
                restart_backend(base_url)
                session_id = str(uuid.uuid4())
                trace_enabled = get_cli_trace(base_url)
                render_current_welcome(base_url, session_id, trace_enabled)
            except BackendUnavailable as exc:
                render_error(str(exc))
            continue
        if message in {"/thinking on", "/thinking off"}:
            enabled = message.endswith("on")
            try:
                request_json(
                    "PUT",
                    "/api/config/models",
                    base_url=base_url,
                    json_body={
                        "provider": "deepseek",
                        "api_key": "",
                        "base_url": "",
                        "thinking_enabled": enabled,
                    },
                )
            except BackendUnavailable as exc:
                render_error(str(exc))
                continue
            console.print(
                Panel(
                    f"DeepSeek thinking: [bold]{'on' if enabled else 'off'}[/]",
                    title="Thinking Updated",
                    border_style="green",
                )
            )
            continue
        if message.startswith("/model "):
            model_name = message.split(" ", 1)[1].strip()
            try:
                switch_model(base_url, model_name)
            except BackendUnavailable as exc:
                render_error(str(exc))
            continue

        try:
            if trace_enabled:
                final_event = stream_chat(base_url, message, session_id)
                render_reply(
                    final_event.get("reply", ""),
                    final_event.get("model", "unknown"),
                    session_id,
                )
                continue
            response = request_json(
                "POST",
                "/api/chat/send",
                base_url=base_url,
                json_body={"message": message, "session_id": session_id},
            )
        except BackendUnavailable as exc:
            render_error(str(exc))
            continue

        render_reply(
            response.get("reply", ""),
            response.get("model", "unknown"),
            session_id,
        )

    console.print(Panel("Session closed.", title="Kore", border_style="dim"))


def switch_model(base_url: str, model: str) -> None:
    data = request_json(
        "POST",
        "/api/models/switch",
        base_url=base_url,
        json_body={"model": model},
    )
    console.print(
        Panel(
            f"Current model: [bold]{data.get('current_model', model)}[/]",
            title="Model Switched",
            border_style="green",
        )
    )


@app.callback(invoke_without_command=True)
def main(
    ctx: typer.Context,
    base_url: str = typer.Option(
        DEFAULT_BASE_URL,
        "--base-url",
        help="Local Kore backend base URL.",
        envvar="KORE_CLI_BASE_URL",
    ),
) -> None:
    """Open chat mode when no subcommand is provided."""
    if ctx.invoked_subcommand is None:
        try:
            run_chat_loop(_base_url(base_url))
        except BackendUnavailable as exc:
            render_error(str(exc))
            raise typer.Exit(code=1) from exc


@app.command()
def ask(
    message: str = typer.Argument(..., help="Message to send to Kore."),
    base_url: str = typer.Option(
        DEFAULT_BASE_URL,
        "--base-url",
        help="Local Kore backend base URL.",
        envvar="KORE_CLI_BASE_URL",
    ),
) -> None:
    """Send a single message and print the reply."""
    session_id = str(uuid.uuid4())
    try:
        response = request_json(
            "POST",
            "/api/chat/send",
            base_url=_base_url(base_url),
            json_body={"message": message, "session_id": session_id},
        )
    except BackendUnavailable as exc:
        render_error(str(exc))
        raise typer.Exit(code=1) from exc

    render_reply(response.get("reply", ""), response.get("model", "unknown"), session_id)


@app.command()
def status(
    base_url: str = typer.Option(
        DEFAULT_BASE_URL,
        "--base-url",
        help="Local Kore backend base URL.",
        envvar="KORE_CLI_BASE_URL",
    ),
) -> None:
    """Show backend and model status."""
    try:
        render_status(_base_url(base_url))
    except BackendUnavailable as exc:
        render_error(str(exc))
        raise typer.Exit(code=1) from exc


@model_app.command("list")
def model_list(
    base_url: str = typer.Option(
        DEFAULT_BASE_URL,
        "--base-url",
        help="Local Kore backend base URL.",
        envvar="KORE_CLI_BASE_URL",
    ),
) -> None:
    """List available models."""
    try:
        render_models(_base_url(base_url))
    except BackendUnavailable as exc:
        render_error(str(exc))
        raise typer.Exit(code=1) from exc


@model_app.command("switch")
def model_switch(
    model: str = typer.Argument(..., help="Model name to activate."),
    base_url: str = typer.Option(
        DEFAULT_BASE_URL,
        "--base-url",
        help="Local Kore backend base URL.",
        envvar="KORE_CLI_BASE_URL",
    ),
) -> None:
    """Switch the current runtime model."""
    try:
        switch_model(_base_url(base_url), model)
    except BackendUnavailable as exc:
        render_error(str(exc))
        raise typer.Exit(code=1) from exc


@config_app.command("show")
def config_show(
    base_url: str = typer.Option(
        DEFAULT_BASE_URL,
        "--base-url",
        help="Local Kore backend base URL.",
        envvar="KORE_CLI_BASE_URL",
    ),
) -> None:
    """Show masked provider configuration."""
    try:
        render_config(_base_url(base_url))
    except BackendUnavailable as exc:
        render_error(str(exc))
        raise typer.Exit(code=1) from exc


@config_app.command("set")
def config_set(
    provider: str = typer.Option(..., "--provider", help="Provider name: deepseek/openai/qwen."),
    api_key: str | None = typer.Option(None, "--api-key", help="API key to persist into backend/.env."),
    base_url_value: str | None = typer.Option(None, "--base-url", help="Provider base URL to persist."),
    thinking_enabled: bool | None = typer.Option(
        None,
        "--thinking/--no-thinking",
        help="Enable or disable provider thinking mode when supported.",
    ),
    request_base_url: str = typer.Option(
        DEFAULT_BASE_URL,
        "--server",
        help="Local Kore backend base URL.",
        envvar="KORE_CLI_BASE_URL",
    ),
) -> None:
    """Update provider configuration and persist it to backend/.env."""
    if not api_key and not base_url_value and thinking_enabled is None:
        render_error("Provide at least one of --api-key, --base-url, or --thinking/--no-thinking.")
        raise typer.Exit(code=1)

    try:
        request_json(
            "PUT",
            "/api/config/models",
            base_url=_base_url(request_base_url),
            json_body={
                "provider": provider,
                "api_key": api_key or "",
                "base_url": base_url_value or "",
                "thinking_enabled": thinking_enabled,
            },
        )
    except BackendUnavailable as exc:
        render_error(str(exc))
        raise typer.Exit(code=1) from exc

    updated = Table(box=box.SIMPLE, show_header=False)
    updated.add_row("provider", provider)
    if api_key:
        updated.add_row("api key", "updated")
    if base_url_value:
        updated.add_row("base url", base_url_value)
    if thinking_enabled is not None:
        updated.add_row("thinking", "on" if thinking_enabled else "off")
    console.print(Panel(updated, title="Config Updated", border_style="green"))


if __name__ == "__main__":
    app()
