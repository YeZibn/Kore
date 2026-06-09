"""Chat API endpoints."""

from __future__ import annotations

import asyncio
import json
import logging

from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
from sse_starlette.sse import EventSourceResponse

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
        return ChatResponse(reply=reply, model=agent.model_state.current_model)
    except Exception as e:
        logger.error("Chat error: %s", e)
        raise HTTPException(status_code=500, detail=str(e))


@chat_router.post("/stream")
async def chat_stream(request: Request, body: ChatRequest) -> EventSourceResponse:
    """Send a message to the agent and stream public trace events."""
    agent = request.app.state.agent_core
    if agent is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")

    async def event_generator():
        queue: asyncio.Queue[dict] = asyncio.Queue()
        emitted_run_failed = False

        async def emit(event: dict) -> None:
            nonlocal emitted_run_failed
            if event.get("type") == "run_failed":
                emitted_run_failed = True
            await queue.put(event)

        task = asyncio.create_task(agent.run_with_events(body.message, body.session_id, emit))
        try:
            while True:
                if task.done() and queue.empty():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=0.1)
                except asyncio.TimeoutError:
                    continue
                yield {
                    "event": event.get("type", "message"),
                    "data": json.dumps(event, ensure_ascii=False),
                }
            await task
        except Exception as e:
            logger.error("Chat stream error: %s", e)
            if not emitted_run_failed:
                yield {
                    "event": "run_failed",
                    "data": json.dumps({"type": "run_failed", "error": str(e)}, ensure_ascii=False),
                }

    return EventSourceResponse(event_generator())
