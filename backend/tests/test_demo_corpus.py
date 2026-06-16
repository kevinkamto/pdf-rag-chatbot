from __future__ import annotations

from app.services.document_service import _read_demo_corpus


def test_bundled_demo_corpus_is_present_and_non_empty() -> None:
    # Empty-KB mode falls back to this corpus; a missing file would silently
    # ship an empty knowledge base instead of failing the build.
    text = _read_demo_corpus()
    assert text, "bundled demo_corpus.md is missing or empty"
