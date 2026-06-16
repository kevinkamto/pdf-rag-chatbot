# SPEC.md

## 1. Goal

Build a small, embeddable AI chatbot for a client website that answers visitor questions using a single PDF as its knowledge source (a basic RAG setup), logs conversations, and can be deployed cheaply on the client's hosting. This is a fixed-scope MVP, not an enterprise system: the priority is a working, maintainable v1 over completeness.

## 2. Scope

In scope for v1:
- OpenAI API integration for chat completion and embeddings
- One PDF knowledge base, ingested once via a script
- RAG pipeline: chunk the PDF, embed the chunks, store them in Qdrant, retrieve the most relevant chunks per question, and ground the answer in them
- A chat widget that can be embedded into the client's existing website, separate from the Next.js app itself
- Conversation storage in SQLite for basic logging
- Deployment instructions covering Docker Compose for the backend and Qdrant, plus a frontend hosting target

Out of scope for v1 (explicitly, to keep this a small project):
- Multiple PDFs or a dynamic knowledge base management UI
- User authentication or multi-tenant support
- An admin analytics dashboard; raw conversation rows are enough for now
- Token-by-token streaming responses
- Any language beyond what the source PDF is written in

## 3. Architecture

1. The operator runs the ingestion script once with the client's PDF. The script extracts text, splits it into chunks, embeds each chunk, and stores them in a Qdrant collection.
2. A visitor opens the chat widget on the client's website. The widget is embedded through a small script tag that points at the deployed Next.js app, so the client's site does not need to be Next.js itself.
3. The widget sends the visitor's message and a session id to the backend's `/api/chat` endpoint.
4. The backend embeds the question, searches Qdrant for the closest chunks, builds a prompt that includes only that retrieved context, calls OpenAI for a completion, strips any em-dash characters defensively, stores the exchange in SQLite, and returns the reply.
5. The widget renders the reply in the chat window.

## 4. RAG Pipeline

Ingestion (run once per PDF, or re-run if the client sends an updated PDF):
- Extract text from the PDF page by page.
- Split into chunks of roughly 800 tokens with about 100 tokens of overlap, respecting paragraph boundaries where possible.
- Embed each chunk with the configured OpenAI embedding model.
- Upsert into a Qdrant collection, storing the chunk text, source page number, and chunk index as payload alongside the vector.
- The collection is recreated fresh on each ingestion run, since v1 only supports a single source PDF.

Query time:
- Embed the incoming question with the same embedding model used at ingestion time.
- Run a similarity search against Qdrant, returning the top K chunks (K configurable, default 4).
- Construct a prompt along these lines:
  - System message: act as a support assistant for the client's product or service, answer only using the provided context, state plainly when the answer is not in the context and point to the configured fallback contact, and never use an em-dash in the response.
  - Context message: the retrieved chunks joined together.
  - User message: the visitor's question.
- Call the OpenAI chat completion endpoint.
- Replace any em-dash characters in the returned text with a comma or period as a safeguard, even though the system prompt already forbids them.
- Persist the user message and the assistant reply against the session id in SQLite.
- Return the reply to the widget.

## 5. API Endpoints

- `GET /api/health` returns a simple status payload, used for deployment checks.
- `POST /api/chat` accepts a session id (created server-side if omitted) and a message, returns the session id and the reply.
- `GET /api/conversations/{session_id}` returns the stored messages for a session, intended for manual QA rather than public use; protect it with a simple shared-secret header check rather than leaving it fully open.

PDF ingestion is a CLI script (`scripts/ingest_pdf.py`), not a public endpoint. A public upload route is unnecessary scope for a single, client-supplied PDF and avoids an extra attack surface on a small budget project.

## 6. Data Models

SQLite:
- `conversations`: id, session_id (unique), created_at
- `messages`: id, conversation_id (foreign key), role (user or assistant), content, created_at

Qdrant:
- Single collection (name configurable, default `pdf_knowledge_base`), vector size matching the embedding model's output (1536 for text-embedding-3-small), cosine distance
- Payload per point: chunk text, source page number, chunk index

## 7. Frontend

- A Next.js app hosting the chat widget UI: a floating bubble that expands into a chat window, plus a small demo page for testing during development.
- `public/embed.js`: a short script the client pastes into their existing website, on any platform, that injects the widget (as an iframe or a mounted floating element) pointing at the deployed widget URL. This satisfies the website-embedding requirement without requiring the client's site to run Next.js.
- The session id is stored in the browser's localStorage so a returning visitor keeps their conversation thread within the same browser.
- Styling stays on Tailwind defaults until branding colors and a logo are provided, then those get applied directly rather than building a theming system.

## 8. Environment Variables

- `OPENAI_API_KEY`
- `OPENAI_CHAT_MODEL` (default: gpt-4o-mini)
- `OPENAI_EMBEDDING_MODEL` (default: text-embedding-3-small)
- `QDRANT_URL`
- `QDRANT_API_KEY` (only needed for Qdrant Cloud, blank for local Docker)
- `QDRANT_COLLECTION_NAME` (default: pdf_knowledge_base)
- `DATABASE_URL` (SQLite file path)
- `ALLOWED_ORIGINS` (comma-separated list for CORS)
- `FALLBACK_CONTACT` (text shown when the bot does not know an answer)
- `TOP_K` (default: 4)

## 9. Deployment Plan

- Backend and Qdrant: a `docker-compose.yml` with two services, the FastAPI backend and Qdrant, deployed to either a small VPS or a platform such as Render or Railway. The SQLite file is persisted through a mounted volume.
- Frontend: deployed separately, for example on Vercel, or alongside the backend on the same host behind a reverse proxy if that fits the client's existing hosting better.
- `README.md` documents the exact steps: environment setup, `docker compose up`, running the ingestion script once against the client's PDF, and pointing the client's website at the deployed `embed.js`.

## 10. Deliverables Mapping

1. Working chatbot integrated into the website: satisfied by the embed script plus the widget UI (section 7).
2. PDF-based Q&A functionality: satisfied by the RAG pipeline (section 4).
3. Basic conversation storage: satisfied by the SQLite schema (section 6).
4. Deployment instructions or setup help: satisfied by the Docker Compose setup and README (section 9).

## 11. Open Questions for the Client

- The PDF itself, confirmed to be text-based rather than a scanned image.
- An OpenAI API key for development and, eventually, production.
- The hosting target: a VPS, a platform like Render or Railway, or something already in use by the client.
- The platform the client's website runs on, so the embed snippet is tested against it.
- Branding basics: logo, accent color, and the welcome message text.
- A fallback contact (email or phone) to show when the bot does not know an answer.
- A short list of sample questions the PDF should be able to answer, for manual QA after launch.

## 12. Constraints

- This is a fixed-scope, low-budget MVP. Resist adding functionality beyond this document without raising it first.
- Em-dash characters must never appear in chatbot-generated text. This is enforced through both the system prompt and a post-processing safeguard, as described in section 4.