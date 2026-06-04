"""Kore API router."""

from __future__ import annotations

from fastapi import APIRouter

from kore.api.chat import chat_router

api_router = APIRouter()


@api_router.get("/status")
async def get_status() -> dict:
    """Get system status."""
    return {
        "status": "running",
        "version": "0.1.0",
    }


api_router.include_router(chat_router, prefix="/chat", tags=["chat"])
