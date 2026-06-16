# RAG Chatbot Backend

FastAPI backend for the RAG chatbot: OpenAI for chat and embeddings, Qdrant for
vector search, SQLite for conversation and document records.

## Quick start

```bash
uv sync
cp ../.env.example .env   # then fill in values
uv run uvicorn app.main:app --reload
```

Seed the demo corpus (optional, also seeded automatically on first start):

```bash
uv run python scripts/ingest_pdf.py
```

Ingest a PDF from the CLI:

```bash
uv run python scripts/ingest_pdf.py path/to/file.pdf
```

## Checks

```bash
uv run ruff check .
uv run ruff format --check .
uv run mypy app
uv run pytest
```

## Endpoints

- `GET  /api/health`
- `POST /api/chat` (Server-Sent Events stream)
- `GET  /api/conversations/{session_id}` (header `X-Management-Secret`)
- `GET/POST/DELETE /api/documents` (header `X-Management-Secret`)
