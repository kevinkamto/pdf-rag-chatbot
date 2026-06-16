"""CLI to ingest a PDF into the knowledge base, or seed the demo corpus.

Usage:
    uv run python scripts/ingest_pdf.py path/to/file.pdf
    uv run python scripts/ingest_pdf.py            # seed the bundled demo corpus
"""

from __future__ import annotations

import asyncio
import sys
from pathlib import Path

from app.core.logging import configure_logging
from app.db.database import init_db
from app.services import document_service


async def _run(pdf_path: str | None) -> int:
    configure_logging()
    init_db()

    if pdf_path is None:
        await document_service.seed_demo_if_empty()
        print("Seeded the demo corpus if the knowledge base was empty.")
        return 0

    path = Path(pdf_path)
    if not path.is_file():
        print(f"Error: file not found: {path}", file=sys.stderr)
        return 1

    data = path.read_bytes()
    doc = await document_service.add_pdf(data, path.name)
    print(f"Ingested '{doc.filename}' as {doc.id} with {doc.chunk_count} chunks.")
    return 0


def main() -> None:
    arg = sys.argv[1] if len(sys.argv) > 1 else None
    raise SystemExit(asyncio.run(_run(arg)))


if __name__ == "__main__":
    main()
