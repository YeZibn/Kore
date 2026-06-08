"""Kore API router."""

from __future__ import annotations

from fastapi import APIRouter

from kore.api.chat import chat_router
from kore.api.config import config_router
from kore.api.models import models_router
from kore.api.server import server_router

api_router = APIRouter()


@api_router.get("/status")
async def get_status() -> dict:
    """Get system status."""
    return {
        "status": "running",
        "version": "0.1.0",
    }


api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
api_router.include_router(models_router, prefix="/models", tags=["models"])
api_router.include_router(config_router, prefix="/config", tags=["config"])
api_router.include_router(server_router, prefix="/server", tags=["server"])
