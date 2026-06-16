"""Pydantic v2 models for API bodies and internal data crossing service boundaries."""

from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"


class ChatRequest(BaseModel):
    message: str = Field(min_length=1, max_length=4000)
    # Bounded to the conversations.session_id column width (String(64)).
    session_id: str | None = Field(default=None, min_length=1, max_length=64)


class MessageOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    role: Literal["user", "assistant"]
    content: str
    created_at: datetime


class ConversationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    session_id: str
    created_at: datetime
    messages: list[MessageOut]


class DocumentOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    status: Literal["processing", "ready", "failed"]
    chunk_count: int
    created_at: datetime


class DocumentList(BaseModel):
    documents: list[DocumentOut]


class RetrievedChunk(BaseModel):
    """A single chunk returned from vector search."""

    text: str
    document_id: str
    filename: str
    page: int
    chunk_index: int
    score: float


class Chunk(BaseModel):
    """A chunk produced during ingestion, before embedding."""

    text: str
    page: int
    chunk_index: int
