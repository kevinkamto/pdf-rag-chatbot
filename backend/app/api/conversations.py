"""Conversation history endpoint (manual QA, shared-secret protected)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.concurrency import run_in_threadpool

from app.api.deps import require_management_secret
from app.db import repository
from app.models.schemas import ConversationOut

router = APIRouter(tags=["conversations"], dependencies=[Depends(require_management_secret)])


@router.get("/conversations/{session_id}", response_model=ConversationOut)
async def get_conversation(session_id: str) -> ConversationOut:
    conversation = await run_in_threadpool(repository.get_conversation, session_id)
    if conversation is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Conversation not found.")
    return ConversationOut.model_validate(conversation)
