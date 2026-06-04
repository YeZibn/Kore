"""Configuration API endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

config_router = APIRouter()


class ProviderConfig(BaseModel):
    api_key: str = ""
    base_url: str = ""


class ProviderConfigResponse(BaseModel):
    providers: dict[str, ProviderConfig]


class UpdateProviderRequest(BaseModel):
    provider: str
    api_key: str = ""
    base_url: str = ""


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
        "deepseek": ("deepseek_api_key", "deepseek_base_url"),
        "openai": ("openai_api_key", "openai_base_url"),
        "qwen": ("qwen_api_key", "qwen_base_url"),
    }

    for name, (key_attr, url_attr) in provider_map.items():
        api_key = getattr(config.llm, key_attr, "")
        base_url = getattr(config.llm, url_attr, "")
        providers[name] = ProviderConfig(
            api_key=_mask_key(api_key),
            base_url=base_url,
        )

    return ProviderConfigResponse(providers=providers)


@config_router.put("/models", response_model=UpdateResponse)
async def update_model_config(request: Request, body: UpdateProviderRequest) -> UpdateResponse:
    """Update model configuration (API key and/or base URL) at runtime."""
    config = request.app.state.config

    provider_map = {
        "deepseek": ("deepseek_api_key", "deepseek_base_url"),
        "openai": ("openai_api_key", "openai_base_url"),
        "qwen": ("qwen_api_key", "qwen_base_url"),
    }

    if body.provider not in provider_map:
        return UpdateResponse(success=False)

    key_attr, url_attr = provider_map[body.provider]

    if body.api_key:
        setattr(config.llm, key_attr, body.api_key)
        logger.info("Updated API key for provider: %s", body.provider)

    if body.base_url:
        setattr(config.llm, url_attr, body.base_url)
        logger.info("Updated base URL for provider: %s", body.provider)

    # Recreate LLM factory with updated config
    from kore.llm.factory import LLMFactory
    request.app.state.agent_core.llm_factory = LLMFactory(config.llm)

    return UpdateResponse(success=True)
