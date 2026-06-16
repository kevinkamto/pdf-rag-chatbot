"""Qdrant vector-store operations for the shared knowledge-base collection."""

from __future__ import annotations

import uuid

from qdrant_client import models as qm
from qdrant_client.http.exceptions import ResponseHandlingException

from app.core.config import get_settings
from app.core.logging import get_logger
from app.core.qdrant_client import get_qdrant_client
from app.core.retry import async_retry
from app.models.schemas import Chunk, RetrievedChunk

logger = get_logger(__name__)

# Qdrant occasionally drops the first connection (transient); retry those.
_TRANSIENT: tuple[type[BaseException], ...] = (ResponseHandlingException,)


@async_retry(attempts=3, exceptions=_TRANSIENT)
async def ensure_collection() -> None:
    """Create the collection if it does not already exist."""
    client = get_qdrant_client()
    settings = get_settings()
    if await client.collection_exists(settings.qdrant_collection_name):
        return
    await client.create_collection(
        collection_name=settings.qdrant_collection_name,
        vectors_config=qm.VectorParams(
            size=settings.embedding_dim,
            distance=qm.Distance.COSINE,
        ),
    )
    # Index the document_id payload so filtered deletes are efficient.
    await client.create_payload_index(
        collection_name=settings.qdrant_collection_name,
        field_name="document_id",
        field_schema=qm.PayloadSchemaType.KEYWORD,
    )
    logger.info("event=collection_created name=%s", settings.qdrant_collection_name)


@async_retry(attempts=3, exceptions=_TRANSIENT)
async def count_points() -> int:
    client = get_qdrant_client()
    settings = get_settings()
    result = await client.count(collection_name=settings.qdrant_collection_name, exact=True)
    return result.count


@async_retry(attempts=3, exceptions=_TRANSIENT)
async def upsert_chunks(
    document_id: str,
    filename: str,
    chunks: list[Chunk],
    vectors: list[list[float]],
) -> None:
    """Upsert embedded chunks for a single document."""
    if not chunks:
        return
    client = get_qdrant_client()
    settings = get_settings()
    points = [
        qm.PointStruct(
            id=str(uuid.uuid4()),
            vector=vector,
            payload={
                "document_id": document_id,
                "filename": filename,
                "page": chunk.page,
                "chunk_index": chunk.chunk_index,
                "text": chunk.text,
            },
        )
        for chunk, vector in zip(chunks, vectors, strict=True)
    ]
    await client.upsert(collection_name=settings.qdrant_collection_name, points=points, wait=True)


@async_retry(attempts=3, exceptions=_TRANSIENT)
async def delete_by_document(document_id: str) -> None:
    """Delete every point belonging to a document."""
    client = get_qdrant_client()
    settings = get_settings()
    await client.delete(
        collection_name=settings.qdrant_collection_name,
        points_selector=qm.FilterSelector(
            filter=qm.Filter(
                must=[qm.FieldCondition(key="document_id", match=qm.MatchValue(value=document_id))]
            )
        ),
        wait=True,
    )


@async_retry(attempts=3, exceptions=_TRANSIENT)
async def search(vector: list[float], top_k: int) -> list[RetrievedChunk]:
    """Return the top-k chunks across all documents for a query vector."""
    client = get_qdrant_client()
    settings = get_settings()
    hits = await client.query_points(
        collection_name=settings.qdrant_collection_name,
        query=vector,
        limit=top_k,
        with_payload=True,
    )
    chunks: list[RetrievedChunk] = []
    for hit in hits.points:
        payload = hit.payload or {}
        chunks.append(
            RetrievedChunk(
                text=str(payload.get("text", "")),
                document_id=str(payload.get("document_id", "")),
                filename=str(payload.get("filename", "")),
                page=int(payload.get("page", 0)),
                chunk_index=int(payload.get("chunk_index", 0)),
                score=float(hit.score),
            )
        )
    return chunks
