from __future__ import annotations

from app.services.pdf_processor import chunk_pages


def test_chunks_respect_pages_and_index() -> None:
    pages = ["First page paragraph.\n\nSecond paragraph here.", "Page two content."]
    chunks = chunk_pages(pages, chunk_tokens=50, overlap_tokens=10)
    assert chunks
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))
    assert {c.page for c in chunks} <= {1, 2}


def test_empty_pages_produce_no_chunks() -> None:
    assert chunk_pages(["", "  "], chunk_tokens=50, overlap_tokens=10) == []


def test_long_paragraph_is_split() -> None:
    long_paragraph = " ".join(f"word{i}" for i in range(2000))
    chunks = chunk_pages([long_paragraph], chunk_tokens=100, overlap_tokens=20)
    assert len(chunks) > 1
    assert all(c.page == 1 for c in chunks)
