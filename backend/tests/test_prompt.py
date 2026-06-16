from __future__ import annotations

from app.models.schemas import RetrievedChunk
from app.services.rag_pipeline import build_messages, generic_messages


def test_no_context_refers_to_fallback() -> None:
    messages = build_messages("What is the price?", [])
    joined = " ".join(str(m["content"]) for m in messages)
    assert "do not have" in joined.lower()


def test_context_is_included_with_source() -> None:
    chunk = RetrievedChunk(
        text="The Personal plan costs 8 dollars per month.",
        document_id="doc1",
        filename="pricing.pdf",
        page=2,
        chunk_index=0,
        score=0.9,
    )
    messages = build_messages("How much is Personal?", [chunk])
    joined = " ".join(str(m["content"]) for m in messages)
    assert "8 dollars" in joined
    assert "pricing.pdf" in joined


def test_system_prompt_forbids_em_dash() -> None:
    messages = build_messages("hi", [])
    assert any("em-dash" in str(m["content"]) for m in messages)


def test_generic_mode_answers_freely_without_fallback() -> None:
    messages = generic_messages("What is the capital of France?")
    joined = " ".join(str(m["content"]) for m in messages).lower()
    # Generic mode does not refuse or point at a fallback contact.
    assert "do not have" not in joined
    assert "context" not in joined
    # The em-dash rule still applies everywhere.
    assert any("em-dash" in str(m["content"]) for m in messages)
    # The user question is included.
    assert any(m["role"] == "user" for m in messages)
