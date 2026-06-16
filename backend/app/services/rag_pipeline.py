"""Retrieval-augmented generation: retrieve context and stream a grounded answer."""

from __future__ import annotations

from collections.abc import AsyncIterator

from openai.types.chat import ChatCompletionMessageParam

from app.core.config import get_settings
from app.core.openai_client import get_openai_client
from app.core.text import strip_em_dashes
from app.models.schemas import RetrievedChunk
from app.services.embeddings import embed_query
from app.services.vector_store import search

_SYSTEM_PROMPT = (
    "You are a helpful support assistant for the product or service described in the "
    "provided context. Follow these rules strictly:\n"
    "1. Answer only using the provided context. Do not use outside knowledge.\n"
    "2. If the answer is not contained in the context, say plainly that you do not have "
    "that information and refer the visitor to {fallback_contact}. Do not guess.\n"
    "3. Never use an em-dash character in your response. Use commas, periods, or "
    "parentheses instead.\n"
    "4. Be concise and accurate."
)

_NO_CONTEXT_NOTE = (
    "No relevant context was found for this question. Tell the visitor you do not have "
    "that information and refer them to {fallback_contact}."
)


async def retrieve(query: str) -> list[RetrievedChunk]:
    settings = get_settings()
    vector = await embed_query(query)
    return await search(vector, settings.top_k)


def build_messages(query: str, chunks: list[RetrievedChunk]) -> list[ChatCompletionMessageParam]:
    settings = get_settings()
    system = _SYSTEM_PROMPT.format(fallback_contact=settings.fallback_contact)

    if chunks:
        context = "\n\n".join(f"[Source: {c.filename}, page {c.page}]\n{c.text}" for c in chunks)
        context_message = f"Context:\n{context}"
    else:
        context_message = _NO_CONTEXT_NOTE.format(fallback_contact=settings.fallback_contact)

    return [
        {"role": "system", "content": system},
        {"role": "system", "content": context_message},
        {"role": "user", "content": query},
    ]


async def stream_answer(messages: list[ChatCompletionMessageParam]) -> AsyncIterator[str]:
    """Stream sanitized answer tokens from the chat model."""
    client = get_openai_client()
    settings = get_settings()
    stream = await client.chat.completions.create(
        model=settings.openai_chat_model,
        messages=messages,
        stream=True,
        temperature=0.2,
    )
    async for event in stream:
        if not event.choices:
            continue
        delta = event.choices[0].delta.content
        if delta:
            yield strip_em_dashes(delta)
