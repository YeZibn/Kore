"""Server lifecycle API endpoints."""

from __future__ import annotations

import os
import signal
import time

from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel

server_router = APIRouter()


class ShutdownResponse(BaseModel):
    success: bool
    message: str


def _shutdown_process() -> None:
    """Terminate the current server process after the response is sent."""
    time.sleep(0.2)
    os.kill(os.getpid(), signal.SIGTERM)


@server_router.post("/shutdown", response_model=ShutdownResponse)
async def shutdown_server(background_tasks: BackgroundTasks) -> ShutdownResponse:
    """Request graceful shutdown of the current backend process."""
    background_tasks.add_task(_shutdown_process)
    return ShutdownResponse(success=True, message="Server shutdown requested.")
