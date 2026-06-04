"""Chat API endpoints."""

from __future__ import annotations

import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel

logger = logging.getLogger(__name__)

chat_router = APIRouter()


class ChatRequest(BaseModel):
    """Request body for chat endpoint."""

    message: str
    session_id: str = ""


class ChatResponse(BaseModel):
    """Response body for chat endpoint."""

    reply: str
    model: str = ""


@chat_router.post("/send", response_model=ChatResponse)
async def chat_send(request: Request, body: ChatRequest) -> ChatResponse:
    """Send a message to the agent and get a response."""
    agent = request.app.state.agent_core
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    try:
        reply = await agent.run(body.message, body.session_id)
        return ChatResponse(reply=reply, model=agent.config.agent.chat_model)
    except Exception as e:
        logger.error("Chat error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))
