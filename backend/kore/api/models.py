"""Model management API endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

from kore.config import update_env_file
from kore.runtime.models import SUPPORTED_PROVIDERS

models_router = APIRouter()


class SwitchRequest(BaseModel):
    model: str


class SwitchResponse(BaseModel):
    success: bool
    current_model: str


class ModelInfo(BaseModel):
    name: str
    provider: str


class ModelListResponse(BaseModel):
    current_model: str
    models: list[ModelInfo]


class ProviderInfo(BaseModel):
    name: str
    base_url: str
    configured: bool


class ProviderListResponse(BaseModel):
    providers: list[ProviderInfo]


@models_router.get("/list", response_model=ModelListResponse)
async def list_models(request: Request) -> ModelListResponse:
    """List all available models."""
    model_state = request.app.state.model_state
    models = model_state.list_models()
    return ModelListResponse(
        current_model=model_state.current_model,
        models=[ModelInfo(**m) for m in models],
    )


@models_router.post("/switch", response_model=SwitchResponse)
async def switch_model(request: Request, body: SwitchRequest) -> SwitchResponse:
    """Switch the current model."""
    model_state = request.app.state.model_state
    config = request.app.state.config
    try:
        model_state.switch(body.model)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    config.agent.chat_model = model_state.current_model
    update_env_file({"KORE_AGENT__CHAT_MODEL": model_state.current_model})
    return SwitchResponse(success=True, current_model=model_state.current_model)


@models_router.get("/providers", response_model=ProviderListResponse)
async def list_providers(request: Request) -> ProviderListResponse:
    """List supported providers and their configuration status."""
    config = request.app.state.config
    providers = []
    for p in SUPPORTED_PROVIDERS:
        # Check if provider has an API key configured
        name_lower = p["name"].lower()
        api_key = getattr(config.llm, f"{name_lower}_api_key", "")
        if not api_key:
            # Try alternate key names
            key_map = {"deepseek": "deepseek_api_key", "openai": "openai_api_key", "qwen": "qwen_api_key"}
            api_key = getattr(config.llm, key_map.get(name_lower, ""), "")

        providers.append(ProviderInfo(
            name=p["name"],
            base_url=p["default_base_url"],
            configured=bool(api_key),
        ))
    return ProviderListResponse(providers=providers)
