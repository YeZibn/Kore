"""Kore configuration management."""

from __future__ import annotations

from pathlib import Path

from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


BACKEND_ROOT = Path(__file__).resolve().parents[1]
ENV_FILE_PATH = BACKEND_ROOT / ".env"
ENV_EXAMPLE_PATH = BACKEND_ROOT / ".env.example"


class AgentConfig(BaseModel):
    """Agent execution configuration."""

    chat_model: str = "deepseek-v4-flash"
    router_model: str = "deepseek-v4-flash"
    embedding_model: str = "text-embed-3-small"
    max_direct_steps: int = 10
    max_plan_steps: int = 6
    max_steps_per_step: int = 8
    context_max_tokens: int = 8000
    memory_top_k: int = 5
    knowledge_top_k: int = 3
    tool_retry_count: int = 0
    tool_timeout_seconds: float | None = 30.0
    llm_retry_count: int = 2
    llm_retry_delay: float = 1.0


class LLMProviderConfig(BaseModel):
    """LLM provider API keys and endpoints."""

    openai_api_key: str = ""
    openai_base_url: str = "https://api.openai.com/v1"
    anthropic_api_key: str = ""
    deepseek_api_key: str = ""
    deepseek_base_url: str = "https://api.deepseek.com/v1"
    deepseek_thinking_enabled: bool = False
    qwen_api_key: str = ""
    qwen_base_url: str = "https://dashscope.aliyuncs.com/compatible-mode/v1"


class ServerConfig(BaseModel):
    """FastAPI server configuration."""

    host: str = "127.0.0.1"
    port: int = 9899
    cors_origins: list[str] = ["*"]


class KoreConfig(BaseSettings):
    """Root configuration for Kore."""

    data_dir: Path = Field(default_factory=lambda: Path("data"))
    skills_dir: Path = Field(default_factory=lambda: Path("skills"))
    agent: AgentConfig = Field(default_factory=AgentConfig)
    llm: LLMProviderConfig = Field(default_factory=LLMProviderConfig)
    server: ServerConfig = Field(default_factory=ServerConfig)
    system_prompt: str = (
        "你是 Kore，一个强大的个人 AI 助手。你可以帮助用户完成各种任务，"
        "包括信息搜索、文件操作、代码编写、数据分析等。"
        "你善于使用工具来解决问题，会主动规划复杂任务，"
        "并能记住与用户的交流历史。"
    )

    model_config = {
        "env_file": ENV_FILE_PATH,
        "env_prefix": "KORE_",
        "env_nested_delimiter": "__",
        "extra": "ignore",
    }

    def ensure_dirs(self) -> None:
        """Create necessary directories."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        (self.data_dir / "memory").mkdir(exist_ok=True)
        (self.data_dir / "knowledge").mkdir(exist_ok=True)
        (self.data_dir / "traces").mkdir(exist_ok=True)
        self.skills_dir.mkdir(parents=True, exist_ok=True)


def load_config() -> KoreConfig:
    """Load configuration from environment and defaults."""
    return KoreConfig()


def update_env_file(updates: dict[str, str], env_file: Path = ENV_FILE_PATH) -> None:
    """Persist key=value updates to backend/.env while preserving unrelated lines."""
    source_path = env_file
    if source_path.exists():
        lines = source_path.read_text(encoding="utf-8").splitlines()
    elif ENV_EXAMPLE_PATH.exists():
        lines = ENV_EXAMPLE_PATH.read_text(encoding="utf-8").splitlines()
    else:
        lines = []

    pending = dict(updates)
    new_lines: list[str] = []

    for line in lines:
        replaced = False
        for key, value in list(pending.items()):
            if line.startswith(f"{key}="):
                new_lines.append(f"{key}={value}")
                pending.pop(key)
                replaced = True
                break
        if not replaced:
            new_lines.append(line)

    if pending:
        if new_lines and new_lines[-1].strip():
            new_lines.append("")
        for key, value in pending.items():
            new_lines.append(f"{key}={value}")

    env_file.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
