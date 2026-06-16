"""OpenAI embedding helpers."""

from __future__ import annotations

from app.core.config import get_settings
from app.core.openai_client import get_openai_client


async def embed_texts(texts: list[str]) -> list[list[float]]:
    """Embed a batch of texts with the configured embedding model."""
    if not texts:
        return []
    client = get_openai_client()
    settings = get_settings()
    response = await client.embeddings.create(model=settings.openai_embedding_model, input=texts)
    return [item.embedding for item in response.data]


async def embed_query(text: str) -> list[float]:
    vectors = await embed_texts([text])
    return vectors[0]
