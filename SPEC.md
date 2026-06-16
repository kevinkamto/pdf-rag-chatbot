# SPEC.md

## 1. Goal

Build an AI chatbot that answers questions from a set of PDF knowledge sources (a RAG setup), streams its replies, and lets the operator manage the knowledge base through a ChatGPT-like web app. The app presents a familiar chat interface with a sidebar listing the ingested PDFs and controls to add and remove them; adding a PDF ingests its content and removing a PDF deletes that document's vectors, so the knowledge base stays in sync with the sidebar. The same backend also powers a small chat-only widget that can be embedded into a client's existing website.

This remains a focused MVP: the priority is a working, maintainable product over completeness. It must run end to end with or without any ingested PDF. When the knowledge base is empty, the backend seeds and answers from a small bundled demo corpus, so the full RAG pipeline (embed, retrieve, ground, stream) is demonstrably working on a fresh checkout.

## 2. Scope

In scope for v1:
- OpenAI API integration for chat completion (streaming) and embeddings
- Multiple PDF knowledge sources, managed at runtime: add (upload and ingest) and remove (delete that document's vectors), kept in sync with the sidebar
- A bundled demo corpus used when the knowledge base has no ingested PDFs
- RAG pipeline: chunk each PDF, embed the chunks, store them in Qdrant tagged by source document, retrieve the most relevant chunks across all active documents per question, and ground the answer in them
- Token-by-token streaming of the assistant reply
- A ChatGPT-like web app: chat pane plus a sidebar that lists the PDFs and exposes add/remove
- A chat-only embeddable widget (`embed.js`) that injects the chat view (no sidebar, no management) into a client's existing website
- Conversation storage in SQLite for basic logging
- Deployment instructions covering Docker Compose for the backend, an externally running Qdrant reached by env vars, and a frontend hosting target

Out of scope for v1 (explicitly, to keep this focused):
- User authentication and multi-tenant support. The PDF-management actions are protected by a simple shared-secret header, not a full auth system.
- An admin analytics dashboard; raw conversation rows are enough for now
- OCR of scanned/image PDFs; sources are assumed to be text-based
- Any language beyond what the source PDFs are written in

Note: multiple PDFs, a knowledge-base management UI, and an upload/delete endpoint were out of scope in the earlier draft and are now deliberately in scope per the updated product direction.

## 3. Architecture

1. The operator opens the web app and manages the knowledge base from the sidebar. Adding a PDF uploads it to the backend, which extracts text, chunks it, embeds the chunks, and upserts them into Qdrant tagged with the document id. Removing a PDF deletes every Qdrant point tagged with that document id and drops its record. If no PDF is present, the backend seeds the same collection from the bundled demo corpus.
2. A visitor (in the app, or through the embedded widget on a client site) sends a message and a session id to the backend's `/api/chat` endpoint.
3. The backend embeds the question, searches Qdrant across all active documents for the closest chunks, builds a prompt that includes only that retrieved context, calls OpenAI with streaming enabled, strips any em-dash characters defensively from each chunk, streams the reply, and stores the completed exchange in SQLite.
4. The chat UI renders the reply token by token as it arrives.

## 4. RAG Pipeline

Ingestion is per document and additive (the collection is not recreated on each add):
- Extract text from the PDF page by page (or read the bundled demo corpus when the knowledge base is empty).
- Split into chunks of roughly 800 tokens with about 100 tokens of overlap, respecting paragraph boundaries where possible.
- Embed each chunk with the configured OpenAI embedding model.
- Upsert into the shared Qdrant collection, storing chunk text, document id, source filename, source page number, and chunk index as payload alongside the vector.

Adding a PDF: run the ingestion above for the new document only, leaving existing documents untouched.

Removing a PDF: delete all Qdrant points whose payload `document_id` matches, then remove the document's SQLite record and stored file. Retrieval afterward no longer surfaces that content.

Query time:
- Embed the incoming question with the same embedding model used at ingestion time.
- Run a similarity search against Qdrant across all active documents, returning the top K chunks (K configurable, default 4).
- Construct a prompt along these lines:
  - System message: act as a support assistant, answer only using the provided context, state plainly when the answer is not in the context and point to the configured fallback contact, and never use an em-dash in the response.
  - Context message: the retrieved chunks joined together, each attributable to its source filename.
  - User message: the visitor's question.
- Call the OpenAI chat completion endpoint with streaming enabled.
- As chunks stream back, replace any em-dash characters with a comma or period as a safeguard, and forward each cleaned chunk to the client.
- Once the stream completes, persist the user message and the full assistant reply against the session id in SQLite.

## 5. API Endpoints

All request and response bodies are Pydantic models.

- `GET /api/health` returns a simple status payload, used for deployment checks.
- `POST /api/chat` accepts a session id (created server-side if omitted) and a message, and streams the reply back as Server-Sent Events (SSE). The session id is sent in an initial event (or response header) so the client can persist it. The stream ends with a terminal event.
- `GET /api/conversations/{session_id}` returns the stored messages for a session, intended for manual QA. Protected by a shared-secret header check.
- `GET /api/documents` lists the ingested PDFs (id, filename, status, chunk count, created_at) for the sidebar.
- `POST /api/documents` accepts a PDF upload (multipart), ingests it, and returns the new document record. This adds context.
- `DELETE /api/documents/{document_id}` deletes the document's vectors, record, and stored file. This removes context.

The document-management endpoints mutate the knowledge base, so they are protected by the same shared-secret header as the conversations endpoint, validate the upload's content type and size, and are not anonymous public routes. A CLI script (`scripts/ingest_pdf.py`) remains available for bulk or initial seeding, but the app's add/remove flow is the primary path.

## 6. Data Models

All backend data structures (API bodies, service inputs/outputs, retrieved-chunk records) are Pydantic v2 models.

SQLite (via SQLAlchemy):
- `documents`: id, filename, stored_path, status, chunk_count, created_at
- `conversations`: id, session_id (unique), created_at
- `messages`: id, conversation_id (foreign key), role (user or assistant), content, created_at

Qdrant (external server, reached via env vars):
- Single collection (name configurable, default `pdf_knowledge_base`), persisted across adds and removes, vector size matching the embedding model's output (1536 for text-embedding-3-small), cosine distance
- Payload per point: chunk text, document_id, source filename, source page number (or demo-corpus section), chunk index. The `document_id` enables filtered deletion when a PDF is removed and source attribution in answers.

## 7. Frontend

- A Next.js (App Router) app presenting a ChatGPT-like interface: a left sidebar and a main chat pane. Components use shadcn/ui and Tailwind; visual design follows the `frontend-design` skill so the app does not read as a templated default.
- Sidebar: lists the ingested PDFs with an add control (file picker that uploads to `POST /api/documents`) and a remove control per item (`DELETE /api/documents/{id}`). The list reflects the live knowledge base and updates after add/remove. The shared secret for these calls is configured for the operator UI, not exposed to anonymous visitors.
- Chat pane: streaming conversation that consumes the SSE `/api/chat` response and renders tokens as they arrive, with a visible streaming/typing state.
- `public/embed.js`: a short script the client pastes into their existing website that injects the chat pane only (no sidebar, no management) as an iframe or mounted floating element pointing at the deployed widget URL. This satisfies the website-embedding requirement without requiring the client's site to run Next.js.
- The session id is stored in the browser's localStorage so a returning visitor keeps their conversation thread within the same browser.
- Styling stays on Tailwind plus shadcn defaults until branding colors and a logo are provided, then those get applied directly rather than building a theming system.

## 8. Environment Variables

Backend and frontend keep separate env files (`backend/.env.example` and
`frontend/.env.example`); there is no shared root env. The frontend env holds
`BACKEND_URL` and `MANAGEMENT_SECRET` (server-only, used by the Next route
handlers). The backend variables below are loaded through `pydantic-settings`
(`Settings(BaseSettings)`). `MANAGEMENT_SECRET` must match across both apps.

- `OPENAI_API_KEY`
- `OPENAI_CHAT_MODEL` (default: gpt-4o-mini)
- `OPENAI_EMBEDDING_MODEL` (default: text-embedding-3-small)
- `QDRANT_URL` (points at the already-running Qdrant server)
- `QDRANT_API_KEY` (set if the Qdrant server requires auth, blank otherwise)
- `QDRANT_COLLECTION_NAME` (default: pdf_knowledge_base)
- `DATABASE_URL` (SQLite file path)
- `UPLOAD_DIR` (where uploaded PDFs are stored, on a mounted volume)
- `MAX_UPLOAD_MB` (default: 20; reject larger uploads)
- `MANAGEMENT_SECRET` (shared secret required by the document-management and conversations endpoints)
- `ALLOWED_ORIGINS` (comma-separated list for CORS)
- `FALLBACK_CONTACT` (text shown when the bot does not know an answer)
- `TOP_K` (default: 4)
- `USE_DEMO_CORPUS` (default: true; when the knowledge base has no ingested PDFs, seed and answer from the bundled demo corpus)

## 9. Deployment Plan

- Backend: a `docker-compose.yml` with the FastAPI backend service. It connects to the existing Qdrant server through `QDRANT_URL`, so Qdrant is not part of this compose file. The SQLite file and `UPLOAD_DIR` are persisted through mounted volumes.
- Backend dependencies and the venv are managed with `uv` (`uv sync`, `uv run ...`); the Dockerfile uses `uv` to install from `pyproject.toml` / `uv.lock`.
- Frontend: managed with `pnpm`, deployed separately, for example on Vercel, or alongside the backend on the same host behind a reverse proxy if that fits the client's existing hosting better.
- `README.md` documents the exact steps: environment setup, `docker compose up`, adding PDFs through the app (or the CLI seed script), and pointing the client's website at the deployed `embed.js`.

## 10. Deliverables Mapping

1. Working chatbot, in-app and embeddable: satisfied by the ChatGPT-like app plus the `embed.js` chat view (section 7).
2. PDF-based Q&A with managed sources: satisfied by the additive RAG pipeline and the add/remove flow (sections 4 and 5), demonstrable with or without PDFs via the demo corpus.
3. Basic conversation storage: satisfied by the SQLite schema (section 6).
4. Deployment instructions or setup help: satisfied by the Docker Compose setup and README (section 9).

## 11. Open Questions for the Client

- The PDFs are confirmed text-based rather than scanned images (no OCR in v1).
- An OpenAI API key for development and, eventually, production.
- Confirmation of the Qdrant server endpoint and whether it requires an API key.
- The hosting target for the backend, and storage for uploaded PDFs.
- The platform the client's website runs on, so the embed snippet is tested against it.
- Branding basics: logo, accent color, and the welcome message text.
- A fallback contact (email or phone) to show when the bot does not know an answer.
- A short list of sample questions the PDFs should answer, for manual QA after launch.

## 12. Constraints

- This is a focused MVP. Resist adding functionality beyond this document without raising it first.
- Streaming responses are mandatory.
- The app must work both with and without ingested PDFs (demo corpus fallback).
- The PDF sidebar and the knowledge base stay in sync: adding a PDF ingests its context, removing a PDF deletes that document's vectors.
- Multiple PDFs are supported; ingestion is additive and per document, not a full collection rebuild.
- Qdrant runs as an external, already-installed server, configured only through env vars.
- Document-management endpoints are protected by a shared secret and validate upload type and size.
- Em-dash characters must never appear in chatbot-generated text. This is enforced through both the system prompt and a per-chunk post-processing safeguard, as described in section 4.
