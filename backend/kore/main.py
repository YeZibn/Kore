"""Kore FastAPI application entry point."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncGenerator

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from kore.config import load_config

logger = logging.getLogger("kore")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan: startup and shutdown."""
    config = load_config()
    config.ensure_dirs()

    from kore.runtime.agent_core import AgentCore
    app.state.agent_core = AgentCore(config)

    logger.info("Kore starting on %s:%s", config.server.host, config.server.port)
    yield
    logger.info("Kore shutdown complete")


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    config = load_config()

    app = FastAPI(
        title="Kore",
        description="Personal AI Assistant & Agent Runtime",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.server.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    from kore.api.router import api_router
    app.include_router(api_router, prefix="/api")

    @app.get("/health")
    async def health() -> dict:
        return {"status": "ok", "version": "0.1.0"}

    return app


app = create_app()


def main() -> None:
    """Run the Kore server."""
    config = load_config()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(name)s %(levelname)s %(message)s",
    )
    uvicorn.run(
        "kore.main:app",
        host=config.server.host,
        port=config.server.port,
        reload=True,
    )


if __name__ == "__main__":
    main()
