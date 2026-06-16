"""FastAPI application entry point."""

from __future__ import annotations

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, conversations, documents
from app.core.config import get_settings
from app.core.logging import configure_logging, get_logger
from app.db.database import init_db
from app.models.schemas import HealthResponse
from app.services import document_service

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    configure_logging()
    init_db()
    try:
        await document_service.seed_demo_if_empty()
    except Exception as exc:
        logger.warning("event=demo_seed_skipped error=%s", type(exc).__name__)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title="RAG Chatbot API", version="0.1.0", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.allowed_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health", response_model=HealthResponse, tags=["health"])
    async def health() -> HealthResponse:
        return HealthResponse()

    app.include_router(chat.router, prefix="/api")
    app.include_router(conversations.router, prefix="/api")
    app.include_router(documents.router, prefix="/api")
    return app


app = create_app()
