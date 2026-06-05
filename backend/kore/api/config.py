"""Configuration API endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel

from kore.config import update_env_file

logger = logging.getLogger(__name__)

config_router = APIRouter()


class ProviderConfig(BaseModel):
    api_key: str = ""
    base_url: str = ""
    thinking_enabled: bool | None = None


class ProviderConfigResponse(BaseModel):
    providers: dict[str, ProviderConfig]


class UpdateProviderRequest(BaseModel):
    provider: str
    api_key: str = ""
    base_url: str = ""
    thinking_enabled: bool | None = None


class UpdateResponse(BaseModel):
    success: bool


def _mask_key(key: str) -> str:
    """Mask API key for display, showing only first 3 and last 4 chars."""
    if len(key) <= 8:
        return "***" if key else ""
    return f"{key[:3]}{'*' * (len(key) - 7)}{key[-4:]}"


@config_router.get("/models", response_model=ProviderConfigResponse)
async def get_model_config(request: Request) -> ProviderConfigResponse:
    """Get current model configuration (API keys are masked)."""
    config = request.app.state.config
    providers = {}

    provider_map = {
        "deepseek": ("deepseek_api_key", "deepseek_base_url", "deepseek_thinking_enabled"),
        "openai": ("openai_api_key", "openai_base_url", None),
        "qwen": ("qwen_api_key", "qwen_base_url", None),
    }

    for name, (key_attr, url_attr, thinking_attr) in provider_map.items():
        api_key = getattr(config.llm, key_attr, "")
        base_url = getattr(config.llm, url_attr, "")
        thinking_enabled = getattr(config.llm, thinking_attr, None) if thinking_attr else None
        providers[name] = ProviderConfig(
            api_key=_mask_key(api_key),
            base_url=base_url,
            thinking_enabled=thinking_enabled,
        )

    return ProviderConfigResponse(providers=providers)


@config_router.put("/models", response_model=UpdateResponse)
async def update_model_config(request: Request, body: UpdateProviderRequest) -> UpdateResponse:
    """Update model configuration in memory and persist it to backend/.env."""
    config = request.app.state.config

    provider_map = {
        "deepseek": ("deepseek_api_key", "deepseek_base_url", "deepseek_thinking_enabled"),
        "openai": ("openai_api_key", "openai_base_url", None),
        "qwen": ("qwen_api_key", "qwen_base_url", None),
    }

    if body.provider not in provider_map:
        return UpdateResponse(success=False)

    key_attr, url_attr, thinking_attr = provider_map[body.provider]
    env_key = f"KORE_LLM__{body.provider.upper()}_API_KEY"
    env_base_url = f"KORE_LLM__{body.provider.upper()}_BASE_URL"
    env_updates: dict[str, str] = {}

    if body.api_key:
        setattr(config.llm, key_attr, body.api_key)
        env_updates[env_key] = body.api_key
        logger.info("Updated API key for provider: %s", body.provider)

    if body.base_url:
        setattr(config.llm, url_attr, body.base_url)
        env_updates[env_base_url] = body.base_url
        logger.info("Updated base URL for provider: %s", body.provider)

    if thinking_attr and body.thinking_enabled is not None:
        setattr(config.llm, thinking_attr, body.thinking_enabled)
        env_updates[f"KORE_LLM__{body.provider.upper()}_THINKING_ENABLED"] = (
            "true" if body.thinking_enabled else "false"
        )
        logger.info("Updated thinking mode for provider: %s", body.provider)

    if env_updates:
        update_env_file(env_updates)

    # Recreate LLM factory with updated config
    from kore.llm.factory import LLMFactory
    request.app.state.agent_core.llm_factory = LLMFactory(config.llm)

    return UpdateResponse(success=True)
