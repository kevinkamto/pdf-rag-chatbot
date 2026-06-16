"""Chat orchestration: retrieve, stream as SSE, and persist the exchange."""

from __future__ import annotations

import json
import uuid
from collections.abc import AsyncIterator

from fastapi.concurrency import run_in_threadpool

from app.core.logging import get_logger
from app.db import repository
from app.services import rag_pipeline

logger = get_logger(__name__)


def _sse(event: str, data: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


async def stream_chat(message: str, session_id: str | None) -> AsyncIterator[str]:
    """Yield SSE events for a chat turn.

    Event types: ``session`` (the resolved session id), ``token`` (a sanitized
    text delta), ``done`` (completion), and ``error`` (a user-safe failure).
    """
    session_id = session_id or uuid.uuid4().hex
    yield _sse("session", {"session_id": session_id})

    await run_in_threadpool(repository.add_message, session_id, "user", message)

    parts: list[str] = []
    try:
        chunks = await rag_pipeline.retrieve(message)
        messages = rag_pipeline.build_messages(message, chunks)
        async for token in rag_pipeline.stream_answer(messages):
            parts.append(token)
            yield _sse("token", {"text": token})
    except Exception as exc:
        logger.error("event=chat_failed session=%s error=%s", session_id, type(exc).__name__)
        if not parts:
            yield _sse(
                "error",
                {"message": "Sorry, something went wrong while answering. Please try again."},
            )
            return

    answer = "".join(parts).strip()
    if answer:
        await run_in_threadpool(repository.add_message, session_id, "assistant", answer)
    yield _sse("done", {"session_id": session_id})
