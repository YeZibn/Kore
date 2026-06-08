"""Core runtime models for Kore agent execution."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import StrEnum
from typing import Any


class RunMode(StrEnum):
    """Execution mode for a run."""

    DIRECT = "direct"
    PLAN = "plan"


class RunStatus(StrEnum):
    """Status of a run."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class RunContext:
    """Context for a single agent run."""

    run_id: str
    mode: RunMode = RunMode.DIRECT
    user_message: str = ""
    status: RunStatus = RunStatus.RUNNING
    total_tokens: int = 0
    total_tool_calls: int = 0
    started_at: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)


# Supported providers (static configuration)
SUPPORTED_PROVIDERS = [
    {
        "name": "DeepSeek",
        "keywords": ["deepseek"],
        "default_base_url": "https://api.deepseek.com/v1",
        "models": ["deepseek-v4-flash", "deepseek-v4-pro"],
        "active": True,
    },
    {
        "name": "OpenAI",
        "keywords": ["gpt", "o1", "o3", "o4"],
        "default_base_url": "https://api.openai.com/v1",
        "models": ["gpt-4o", "gpt-4o-mini", "o3-mini"],
        "active": False,
    },
    {
        "name": "Qwen",
        "keywords": ["qwen"],
        "default_base_url": "https://dashscope.aliyuncs.com/compatible-mode/v1",
        "models": ["qwen-plus", "qwen-turbo", "qwen-max"],
        "active": False,
    },
]


@dataclass
class ModelState:
    """Global model state — runtime-switchable model configuration."""

    current_model: str = "deepseek-v4-flash"

    def switch(self, model: str) -> None:
        """Switch the current model."""
        if not self.is_available_model(model):
            raise ValueError(f"Model '{model}' is not available.")
        self.current_model = model

    def is_available_model(self, model: str) -> bool:
        """Return whether a model is currently available for switching."""
        return model in {item["name"] for item in self.list_models()}

    def get_provider_for_model(self, model: str) -> str:
        """Get the provider name for a given model."""
        model_lower = model.lower()
        for provider in SUPPORTED_PROVIDERS:
            for kw in provider["keywords"]:
                if kw in model_lower:
                    return provider["name"]
        return "Unknown"

    def list_models(self) -> list[dict[str, str]]:
        """List all available models across providers."""
        models = []
        for provider in SUPPORTED_PROVIDERS:
            if not provider.get("active", False):
                continue
            for model_name in provider["models"]:
                models.append({"name": model_name, "provider": provider["name"]})
        return models
