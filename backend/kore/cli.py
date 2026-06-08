"""User-facing CLI for Kore."""

from __future__ import annotations

import os
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
from rich import box
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table
from rich.text import Text

DEFAULT_BASE_URL = "http://127.0.0.1:9899"
DEFAULT_TIMEOUT = 60.0
BACKEND_LOG_PATH = Path(tempfile.gettempdir()) / "kore-cli-backend.log"

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


def render_reply(reply: str, model: str, session_id: str) -> None:
    body = Markdown(reply) if reply.strip() else Text("(empty response)", style="dim")
    title = "Assistant"
    subtitle = f"{model}  session {session_id[:8]}"
    console.print(Panel(body, title=title, subtitle=subtitle, border_style="cyan"))


def render_status(base_url: str) -> None:
    health = request_json("GET", "/health", base_url=base_url)
    status = request_json("GET", "/api/status", base_url=base_url)
    models = request_json("GET", "/api/models/list", base_url=base_url)
    providers = request_json("GET", "/api/models/providers", base_url=base_url)

    summary = Table(box=box.SIMPLE, show_header=False)
    summary.add_row("backend", base_url)
    summary.add_row("health", health.get("status", "unknown"))
    summary.add_row("version", status.get("version", "unknown"))
    summary.add_row("current model", models.get("current_model", "unknown"))
    console.print(Panel(summary, title="Kore Status", border_style="blue"))

    provider_table = Table(box=box.SIMPLE_HEAVY)
    provider_table.add_column("Provider", style="bold")
    provider_table.add_column("Configured")
    provider_table.add_column("Base URL", overflow="fold")
    for provider in providers.get("providers", []):
        configured = "[green]yes[/]" if provider["configured"] else "[red]no[/]"
        provider_table.add_row(provider["name"], configured, provider["base_url"])
    console.print(provider_table)


def render_models(base_url: str) -> None:
    data = request_json("GET", "/api/models/list", base_url=base_url)
    current = data.get("current_model", "")

    table = Table(box=box.SIMPLE_HEAVY)
    table.add_column("Model", style="bold")
    table.add_column("Provider")
    table.add_column("Current")

    for item in data.get("models", []):
        marker = "[green]current[/]" if item["name"] == current else ""
        table.add_row(item["name"], item["provider"], marker)

    console.print(Panel(f"Current model: [bold]{current}[/]", border_style="blue"))
    console.print(table)


def render_config(base_url: str) -> None:
    data = request_json("GET", "/api/config/models", base_url=base_url)
    table = Table(box=box.SIMPLE_HEAVY)
    table.add_column("Provider", style="bold")
    table.add_column("API Key")
    table.add_column("Base URL", overflow="fold")
    table.add_column("Thinking")
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


def get_deepseek_thinking(base_url: str) -> str:
    data = request_json("GET", "/api/config/models", base_url=base_url)
    deepseek = data.get("providers", {}).get("deepseek", {})
    thinking = deepseek.get("thinking_enabled")
    return "on" if thinking else "off"


def run_chat_loop(base_url: str) -> None:
    ensure_backend(base_url)
    session_id = str(uuid.uuid4())
    models = request_json("GET", "/api/models/list", base_url=base_url)
    current_model = models.get("current_model", "unknown")

    intro = Table(box=None, show_header=False, pad_edge=False)
    intro.add_row("backend", base_url)
    intro.add_row("model", current_model)
    intro.add_row("thinking", get_deepseek_thinking(base_url))
    workspace = request_json("GET", "/api/config/workspace", base_url=base_url)
    intro.add_row("workspace", workspace.get("workspace_root", "unknown"))
    intro.add_row("session", session_id[:8])
    intro.add_row("tips", "/status  /model  /thinking  /workspace  /help  /quit")
    console.print(Panel(intro, title="Kore", border_style="blue"))

    while True:
        try:
            message = Prompt.ask("[bold cyan]you[/]").strip()
        except (KeyboardInterrupt, EOFError):
            console.print()
            break

        if not message:
            continue

        if message in {"/exit", "/quit"}:
            break
        if message == "/help":
            console.print(
                "Commands: /status, /model, /model <name>, /thinking, /thinking on, "
                "/thinking off, /workspace, /workspace <path>, /quit"
            )
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
            switch_model(base_url, model_name)
            continue

        try:
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
