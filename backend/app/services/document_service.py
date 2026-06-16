"""Knowledge-base document lifecycle: add (ingest) and remove (delete vectors).

Keeps the SQLite ``documents`` table, the stored files, and the Qdrant vectors
in sync so the sidebar always reflects the real knowledge base.
"""

from __future__ import annotations

import contextlib
import os
import uuid
from pathlib import Path

from fastapi.concurrency import run_in_threadpool

from app.core.config import get_settings
from app.core.logging import get_logger
from app.db import repository
from app.models.db_models import Document
from app.models.schemas import Chunk
from app.services import vector_store
from app.services.embeddings import embed_texts
from app.services.pdf_processor import chunk_pages, extract_pages

logger = get_logger(__name__)

_EMBED_BATCH = 128
_DEMO_DOC_ID = "demo-corpus"
_DEMO_FILENAME = "Demo Knowledge Base (sample).md"


class IngestionError(RuntimeError):
    """Raised when a document cannot be ingested."""


async def list_documents() -> list[Document]:
    return await run_in_threadpool(repository.list_documents)


async def add_pdf(data: bytes, filename: str) -> Document:
    """Persist, ingest, and index a new PDF. Returns the document record."""
    settings = get_settings()
    await vector_store.ensure_collection()

    document_id = str(uuid.uuid4())
    stored_path = await run_in_threadpool(_store_file, settings.upload_dir, document_id, data)
    await run_in_threadpool(repository.create_document, document_id, filename, stored_path)

    try:
        pages = await run_in_threadpool(extract_pages, data)
        chunks = chunk_pages(
            pages,
            chunk_tokens=settings.chunk_tokens,
            overlap_tokens=settings.chunk_overlap_tokens,
        )
        if not chunks:
            raise IngestionError("No extractable text found in the PDF.")
        await _embed_and_upsert(document_id, filename, chunks)
        await run_in_threadpool(repository.mark_document_ready, document_id, len(chunks))
    except Exception as exc:
        logger.warning(
            "event=ingest_failed document_id=%s error=%s", document_id, type(exc).__name__
        )
        await run_in_threadpool(repository.mark_document_failed, document_id)
        await vector_store.delete_by_document(document_id)
        if isinstance(exc, IngestionError):
            raise
        raise IngestionError("Failed to ingest the PDF.") from exc

    doc = await run_in_threadpool(repository.get_document, document_id)
    if doc is None:
        raise IngestionError("Document vanished immediately after creation.")
    logger.info("event=document_added id=%s chunks=%s", document_id, doc.chunk_count)
    return doc


async def remove_document(document_id: str) -> bool:
    """Delete a document's vectors, file, and record. Returns False if unknown."""
    doc = await run_in_threadpool(repository.get_document, document_id)
    if doc is None:
        return False
    await vector_store.delete_by_document(document_id)
    await run_in_threadpool(_remove_file, doc.stored_path)
    await run_in_threadpool(repository.delete_document_row, document_id)
    logger.info("event=document_removed id=%s", document_id)
    return True


async def seed_demo_if_empty() -> None:
    """Seed the bundled demo corpus when the knowledge base has no vectors."""
    settings = get_settings()
    if not settings.use_demo_corpus:
        return
    await vector_store.ensure_collection()
    if await vector_store.count_points() > 0:
        return

    text = _read_demo_corpus()
    if not text:
        return

    pages = [text]
    chunks = chunk_pages(
        pages,
        chunk_tokens=settings.chunk_tokens,
        overlap_tokens=settings.chunk_overlap_tokens,
    )
    await _embed_and_upsert(_DEMO_DOC_ID, _DEMO_FILENAME, chunks)
    await run_in_threadpool(_upsert_demo_row, _DEMO_DOC_ID, _DEMO_FILENAME, len(chunks))
    logger.info("event=demo_seeded chunks=%s", len(chunks))


async def _embed_and_upsert(document_id: str, filename: str, chunks: list[Chunk]) -> None:
    for start in range(0, len(chunks), _EMBED_BATCH):
        batch = chunks[start : start + _EMBED_BATCH]
        vectors = await embed_texts([c.text for c in batch])
        await vector_store.upsert_chunks(document_id, filename, batch, vectors)


# --- filesystem / db helpers (sync, run in threadpool) -----------------------


def _store_file(upload_dir: str, document_id: str, data: bytes) -> str:
    os.makedirs(upload_dir, exist_ok=True)
    path = os.path.join(upload_dir, f"{document_id}.pdf")
    with open(path, "wb") as handle:
        handle.write(data)
    return path


def _remove_file(path: str) -> None:
    with contextlib.suppress(FileNotFoundError):
        os.remove(path)


def _read_demo_corpus() -> str:
    path = Path(__file__).resolve().parent.parent / "data" / "demo_corpus.md"
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8").strip()


def _upsert_demo_row(doc_id: str, filename: str, chunk_count: int) -> None:
    existing = repository.get_document(doc_id)
    if existing is not None:
        repository.delete_document_row(doc_id)
    repository.create_document(doc_id, filename, stored_path="<bundled>")
    repository.mark_document_ready(doc_id, chunk_count)
