"""Synchronous data-access helpers.

Each function manages its own session via :func:`session_scope`. Async callers
must invoke these through ``fastapi.concurrency.run_in_threadpool``.
"""

from __future__ import annotations

from sqlalchemy import delete, select

from app.db.database import session_scope
from app.models.db_models import Conversation, Document, Message


# --- Conversations & messages ------------------------------------------------


def get_or_create_conversation(session_id: str) -> int:
    with session_scope() as db:
        conv = db.scalar(select(Conversation).where(Conversation.session_id == session_id))
        if conv is None:
            conv = Conversation(session_id=session_id)
            db.add(conv)
            db.flush()
        return conv.id


def add_message(session_id: str, role: str, content: str) -> None:
    with session_scope() as db:
        conv = db.scalar(select(Conversation).where(Conversation.session_id == session_id))
        if conv is None:
            conv = Conversation(session_id=session_id)
            db.add(conv)
            db.flush()
        db.add(Message(conversation_id=conv.id, role=role, content=content))


def get_conversation(session_id: str) -> Conversation | None:
    with session_scope() as db:
        conv = db.scalar(select(Conversation).where(Conversation.session_id == session_id))
        if conv is None:
            return None
        # Touch the relationship so it is loaded before the session closes.
        _ = list(conv.messages)
        db.expunge(conv)
        return conv


# --- Documents ---------------------------------------------------------------


def create_document(doc_id: str, filename: str, stored_path: str) -> None:
    with session_scope() as db:
        db.add(
            Document(
                id=doc_id,
                filename=filename,
                stored_path=stored_path,
                status="processing",
                chunk_count=0,
            )
        )


def mark_document_ready(doc_id: str, chunk_count: int) -> None:
    with session_scope() as db:
        doc = db.get(Document, doc_id)
        if doc is not None:
            doc.status = "ready"
            doc.chunk_count = chunk_count


def mark_document_failed(doc_id: str) -> None:
    with session_scope() as db:
        doc = db.get(Document, doc_id)
        if doc is not None:
            doc.status = "failed"


def list_documents() -> list[Document]:
    with session_scope() as db:
        docs = list(db.scalars(select(Document).order_by(Document.created_at.desc())))
        for doc in docs:
            db.expunge(doc)
        return docs


def get_document(doc_id: str) -> Document | None:
    with session_scope() as db:
        doc = db.get(Document, doc_id)
        if doc is not None:
            db.expunge(doc)
        return doc


def delete_document_row(doc_id: str) -> None:
    with session_scope() as db:
        db.execute(delete(Document).where(Document.id == doc_id))
