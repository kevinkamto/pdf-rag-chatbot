# CLAUDE.md

Guidance for Claude Code when working in this repository. Read SPEC.md alongside this file before writing any code; SPEC.md is the source of truth for requirements and CLAUDE.md is the source of truth for how to work.

## Project Overview

A small, embeddable AI chatbot that answers questions from a single PDF knowledge base using OpenAI for generation and embeddings, Qdrant for vector search, and a lightweight SQLite log for conversation history. This is a fixed-scope MVP built against a client job description with a small budget, not an enterprise system. Favor the simplest correct solution over abstraction for hypothetical future needs.

## Tech Stack

- Frontend: Next.js (App Router), TypeScript, Tailwind CSS
- Backend: FastAPI (Python 3.11+)
- Vector database: Qdrant, run via Docker locally; Qdrant Cloud free tier is an option for production
- LLM provider: OpenAI API, gpt-4o-mini for chat completions, text-embedding-3-small for embeddings (both configurable via env vars)
- Conversation storage: SQLite via SQLAlchemy
- Containerization: Docker and Docker Compose for backend plus Qdrant
- Documentation lookups: Context7 MCP is installed locally. When implementing anything touching an external library (Next.js routing, FastAPI, the Qdrant client, the OpenAI SDK, SQLAlchemy), look up current usage via Context7 first instead of relying on memorized API shapes, since library APIs shift between versions.

## Repository Structure

```
project-root/
  frontend/
    app/
      page.tsx
      widget/
    components/
    lib/
    public/
      embed.js
  backend/
    app/
      main.py
      api/
        chat.py
        conversations.py
      core/
        config.py
        openai_client.py
        qdrant_client.py
      services/
        pdf_processor.py
        rag_pipeline.py
        chat_service.py
      models/
        schemas.py
        db_models.py
      db/
        database.py
    scripts/
      ingest_pdf.py
    requirements.txt
    Dockerfile
  docker-compose.yml
  .env.example
  CLAUDE.md
  SPEC.md
  README.md
```

## Development Commands

Backend:
- `uvicorn app.main:app --reload` to run the API locally
- `python scripts/ingest_pdf.py path/to/file.pdf` to build the Qdrant collection from the source PDF
- `pytest` for tests, once they exist

Frontend:
- `npm run dev` for local development
- `npm run build` before deploying

Infrastructure:
- `docker compose up -d` to start Qdrant (and the backend, once containerized)

## Coding Standards

- Python: type hints throughout, Pydantic models for every request and response body, keep route handlers thin and push logic into services so it stays testable.
- TypeScript: strict mode, functional components, no `any`.
- Do not add features outside SPEC.md without flagging them first. Multi-PDF support, authentication, multi-tenant logic, and an admin dashboard are explicitly out of scope for v1; see SPEC.md section on scope.
- Keep commits small and scoped to one logical change.

## AI Output Rules (important, do not skip)

- The chatbot must never produce an em-dash character in any generated reply. Enforce this two ways: state it directly in the system prompt sent to OpenAI, and add a defensive post-processing step on the backend that replaces any em-dash with a comma or period before the reply is returned to the frontend, in case the model ignores the instruction.
- This rule also applies to any user-facing text Claude Code writes by hand: UI copy, error messages, README content, commit messages. Use commas, periods, or parentheses instead of em-dashes everywhere in this project.
- The chatbot must answer only from the retrieved PDF context. If the retrieved chunks do not contain the answer, the reply should say so plainly and point to the configured fallback contact rather than guessing or using outside knowledge.

## Environment Variables

See `.env.example` for the full list. Never commit a populated `.env` file or the source PDF to git.

## Security Notes

- Restrict FastAPI CORS to the actual domain(s) the widget will be embedded on, plus localhost during development.
- The PDF ingestion script is an operator-run tool, not a public upload endpoint. Do not expose a public file upload route in v1.
- Do not log the OpenAI API key or any secret values.

## Workflow Notes

- Build the backend and verify the RAG pipeline with direct API calls (curl or a REST client) before wiring up the frontend widget.
- Once the real PDF is available, write a short list of 5 to 8 questions drawn from its actual content and manually verify the chatbot answers them correctly and refuses gracefully outside that scope, before calling the feature done.
- If a choice in SPEC.md (database, model names, deployment target) does not fit the actual hosting situation, raise it before building rather than silently changing it.