"""PDF text extraction and token-aware chunking."""

from __future__ import annotations

import re
from functools import lru_cache
from io import BytesIO

import tiktoken
from pypdf import PdfReader

from app.models.schemas import Chunk


@lru_cache
def _encoder() -> tiktoken.Encoding:
    return tiktoken.get_encoding("cl100k_base")


def extract_pages(data: bytes) -> list[str]:
    """Extract text from each page of a PDF.

    Returns one string per page. Pages with no extractable text become empty
    strings so page numbering stays aligned with the source document.
    """
    reader = PdfReader(BytesIO(data))
    pages: list[str] = []
    for page in reader.pages:
        text = page.extract_text() or ""
        pages.append(_normalize(text))
    return pages


def _normalize(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    # Collapse runs of spaces/tabs but keep paragraph breaks.
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _split_paragraphs(text: str) -> list[str]:
    parts = re.split(r"\n\s*\n", text)
    return [p.strip() for p in parts if p.strip()]


def chunk_pages(
    pages: list[str],
    *,
    chunk_tokens: int,
    overlap_tokens: int,
) -> list[Chunk]:
    """Split page text into overlapping, token-bounded chunks.

    Chunks respect paragraph boundaries where possible: paragraphs are packed
    together until the token budget is reached. A paragraph larger than the
    budget is split on token windows. Overlap is carried between chunks within
    the same page to preserve context across boundaries.
    """
    enc = _encoder()
    chunks: list[Chunk] = []
    index = 0

    for page_number, page_text in enumerate(pages, start=1):
        if not page_text:
            continue
        for piece in _pack_paragraphs(
            _split_paragraphs(page_text), enc, chunk_tokens, overlap_tokens
        ):
            chunks.append(Chunk(text=piece, page=page_number, chunk_index=index))
            index += 1

    return chunks


def _pack_paragraphs(
    paragraphs: list[str],
    enc: tiktoken.Encoding,
    chunk_tokens: int,
    overlap_tokens: int,
) -> list[str]:
    pieces: list[str] = []
    current: list[str] = []
    current_tokens = 0

    def flush() -> None:
        nonlocal current, current_tokens
        if current:
            pieces.append("\n\n".join(current).strip())
            current = []
            current_tokens = 0

    for paragraph in paragraphs:
        para_tokens = len(enc.encode(paragraph))

        if para_tokens > chunk_tokens:
            flush()
            pieces.extend(_split_long(paragraph, enc, chunk_tokens, overlap_tokens))
            continue

        if current_tokens + para_tokens > chunk_tokens:
            flush()
        current.append(paragraph)
        current_tokens += para_tokens

    flush()
    return pieces


def _split_long(
    paragraph: str,
    enc: tiktoken.Encoding,
    chunk_tokens: int,
    overlap_tokens: int,
) -> list[str]:
    tokens = enc.encode(paragraph)
    step = max(1, chunk_tokens - overlap_tokens)
    windows: list[str] = []
    for start in range(0, len(tokens), step):
        window = tokens[start : start + chunk_tokens]
        if not window:
            break
        windows.append(enc.decode(window).strip())
        if start + chunk_tokens >= len(tokens):
            break
    return windows
