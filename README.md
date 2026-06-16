# RAG Chatbot

An embeddable, ChatGPT-like AI chatbot that answers questions from a managed set
of PDF knowledge sources. It uses OpenAI for chat and embeddings, Qdrant for
vector search, and SQLite for conversation and document records. Replies stream
token by token. The app runs with or without your own PDFs: when the knowledge
base is empty it answers from a bundled demo corpus so retrieval works out of the
box.

- **Backend**: FastAPI (Python 3.11+, managed with `uv`)
- **Frontend**: Next.js App Router + TypeScript + Tailwind + shadcn-style UI
  (managed with `pnpm`)
- **Vector DB**: Qdrant, an external server reached by `QDRANT_URL`

See [SPEC.md](SPEC.md) for requirements and [CLAUDE.md](CLAUDE.md) for working
conventions.

## Contents

- [Architecture](#architecture)
- [Prerequisites](#prerequisites)
- [1. Backend](#1-backend)
- [2. Frontend](#2-frontend)
- [3. Embedding into a website](#3-embedding-into-a-website)
- [Deploying with Docker (backend)](#deploying-with-docker-backend)
- [Environment variables](#environment-variables)
- [Checks](#checks)

## Architecture

```
Browser ──> Next.js app (chat pane + PDF sidebar)
              │  same-origin route handlers add the management secret
              ▼
           FastAPI backend ──> OpenAI (chat + embeddings)
              │                └─> Qdrant (vector search)
              └─> SQLite (conversations, documents)
```

Adding a PDF in the sidebar ingests its content; removing a PDF deletes that
document's vectors, so the knowledge base stays in sync with the sidebar.

## Prerequisites

- A running Qdrant server (local Docker, WSL, or Qdrant Cloud) and its URL
- An OpenAI API key
- `uv`, `pnpm`, and (optionally) Docker

## 1. Backend

```bash
cd backend
cp .env.example .env        # set OPENAI_API_KEY, QDRANT_URL, MANAGEMENT_SECRET
uv sync
uv run uvicorn app.main:app --reload
```

The knowledge base is seeded with the demo corpus on first start. To ingest a
real PDF from the CLI:

```bash
uv run python scripts/ingest_pdf.py path/to/file.pdf
```

## 2. Frontend

```bash
cd frontend
cp .env.example .env.local  # set BACKEND_URL and the same MANAGEMENT_SECRET
pnpm install
pnpm dev
```

Open http://localhost:3000 for the app. Add and remove PDFs from the sidebar.

## 3. Embedding into a website

Deploy the frontend, then paste this into any site:

```html
<script src="https://YOUR_HOST/embed.js" data-base-url="https://YOUR_HOST" defer></script>
```

It injects a floating chat bubble that opens the chat-only `/widget` view. The
host site does not need to run Next.js.

## Deploying with Docker (backend)

```bash
docker compose up -d --build
```

Qdrant is not part of the compose file. Point `QDRANT_URL` in `backend/.env` at
your running Qdrant (use `http://host.docker.internal:6333` if it runs on the
Docker host). The SQLite database and uploaded PDFs persist in a named volume.

## Environment variables

Backend and frontend have separate env files:

- Backend: [backend/.env.example](backend/.env.example)
- Frontend: [frontend/.env.example](frontend/.env.example)

`MANAGEMENT_SECRET` must be identical in both so the frontend can call the
backend's protected document endpoints.

### Tunable backend settings

These have sensible defaults; override them in `backend/.env` as needed:

| Variable | Default | Purpose |
| --- | --- | --- |
| `TOP_K` | `4` | Chunks retrieved per query (1..20). |
| `USE_DEMO_CORPUS` | `true` | Seed the bundled demo corpus when the knowledge base is empty. |
| `FALLBACK_CONTACT` | support email | Contact offered when the answer is not in context. |
| `MAX_UPLOAD_MB` | `20` | Largest accepted PDF upload. |
| `CHUNK_TOKENS` | `800` | Token budget per chunk. |
| `CHUNK_OVERLAP_TOKENS` | `100` | Overlap carried between chunks (must be `< CHUNK_TOKENS`). |

## Checks

```bash
# backend
cd backend && uv run ruff check . && uv run mypy app && uv run pytest

# frontend
cd frontend && pnpm lint && pnpm build
```
