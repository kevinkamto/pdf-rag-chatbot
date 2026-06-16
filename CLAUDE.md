# CLAUDE.md

Guidance for Claude Code when working in this repository. Read SPEC.md alongside this file before writing any code; SPEC.md is the source of truth for requirements and CLAUDE.md is the source of truth for how to work.

## Project Overview

A small, embeddable AI chatbot that answers questions from a single PDF knowledge base using OpenAI for generation and embeddings, Qdrant for vector search, and a lightweight SQLite log for conversation history. Replies stream token by token. The MVP runs out of the box with or without a client PDF: when no PDF has been ingested it falls back to a small bundled demo corpus so the full RAG path is always exercised and visibly working. This is a fixed-scope MVP built against a client job description with a small budget, not an enterprise system. Favor the simplest correct solution over abstraction for hypothetical future needs.

## Tech Stack

- Frontend: Next.js (App Router), TypeScript, Tailwind CSS, shadcn/ui for components
- Backend: FastAPI (Python 3.11+)
- Vector database: Qdrant. A Qdrant server is already installed and running; the backend connects to it purely through env vars (`QDRANT_URL`, `QDRANT_API_KEY`). Do not provision a Qdrant container in this project.
- LLM provider: OpenAI API, gpt-4o-mini for chat completions, text-embedding-3-small for embeddings (both configurable via env vars). Responses are streamed.
- Conversation storage: SQLite via SQLAlchemy
- Config and validation: Pydantic v2 everywhere. All request/response bodies, internal service boundaries, and structured payloads are Pydantic models. App settings load from `.env` via `pydantic-settings` (`BaseSettings`), never `os.getenv` scattered through the code.
- Backend tooling: `uv` for environment and dependency management, `ruff` for lint + format, `mypy` for type checking.
- Frontend tooling: `pnpm` for dependency management, `prettier` for formatting, ESLint for linting.
- Containerization: Docker and Docker Compose for the backend only (Qdrant is external, see above).

## Skills

Project-scoped Claude Code skills are installed and active. Use them; do not re-derive their guidance from memory. They are loaded automatically by name when a task matches their description, or invoke explicitly via the Skill tool.

Backend (Python):
- `python-project-structure` for module layout and public API design.
- `python-code-style` for style, naming, docstrings, and linter config.
- `python-type-safety` for type hints, generics, protocols, mypy/pyright setup.
- `python-design-patterns` for layering responsibilities and avoiding over-abstraction. Note: this project favors the simplest correct solution, so apply KISS and skip patterns that add abstraction for hypothetical future needs.

Frontend (Next.js / React / styling):
- `next-best-practices` for App Router conventions, RSC boundaries, data and metadata patterns, route handlers.
- `vercel-react-best-practices` for React/Next performance patterns.
- `vercel-composition-patterns` for component composition and reusable APIs.
- `tailwindcss` for utility-first styling and theme variables.
- `shadcn` for adding and composing shadcn/ui components.
- `frontend-design` for distinctive, non-templated visual design of the widget.

Meta:
- `find-skills` to discover and install further skills when a need comes up.

Skill layout and Context7 both apply: when a task touches an external library API, also look it up via Context7 MCP (see below) for current syntax. Skills give project conventions; Context7 gives current library APIs.

### How skills are stored

Skills live as real files in `.claude/skills/<name>/SKILL.md`, which is the directory Claude Code reads. They are committed to the repo, so a fresh clone has them immediately with no extra install step. To add more, you can use the skills.sh CLI (`npx skills add <github-repo-url> --skill <name>`); it vendors into `.agents/skills/` and links per agent, so afterward copy the new skill folder into `.claude/skills/` and remove the `.agents/` bookkeeping to keep this single-directory layout.

## Documentation lookups

Context7 MCP is installed locally. When implementing anything touching an external library (Next.js routing, FastAPI, the Qdrant client, the OpenAI SDK, SQLAlchemy, Pydantic, pydantic-settings), look up current usage via Context7 first instead of relying on memorized API shapes, since library APIs shift between versions.

## Repository Structure

```
project-root/
  frontend/
    app/
      page.tsx
      widget/
    components/
      ui/                 # shadcn/ui components
    lib/
    public/
      embed.js
    package.json
    pnpm-lock.yaml
    .prettierrc
  backend/
    app/
      main.py
      api/
        chat.py           # streaming /api/chat (SSE)
        conversations.py
      core/
        config.py         # pydantic-settings BaseSettings, loads .env
        openai_client.py
        qdrant_client.py
      services/
        pdf_processor.py
        rag_pipeline.py
        chat_service.py
      models/
        schemas.py        # Pydantic request/response + internal models
        db_models.py
      db/
        database.py
      data/
        demo_corpus.md    # bundled sample knowledge base for no-PDF mode
    scripts/
      ingest_pdf.py
    pyproject.toml        # deps + ruff + mypy config (uv-managed)
    uv.lock
    Dockerfile
  docker-compose.yml      # backend only; Qdrant is external
  .env.example
  .gitignore
  .claude/skills/         # project skills, real files, committed
  CLAUDE.md
  SPEC.md
  README.md
```

## Development Commands

Backend (uv):
- `uv sync` to install dependencies into the project venv
- `uv run uvicorn app.main:app --reload` to run the API locally
- `uv run python scripts/ingest_pdf.py path/to/file.pdf` to build the Qdrant collection from a source PDF (omit the path to seed the bundled demo corpus)
- `uv run ruff check .` and `uv run ruff format .` for lint and format
- `uv run mypy app` for type checking
- `uv run pytest` for tests, once they exist

Frontend (pnpm):
- `pnpm install` to install dependencies
- `pnpm dev` for local development
- `pnpm build` before deploying
- `pnpm prettier --write .` for formatting; `pnpm lint` for ESLint

Infrastructure:
- `docker compose up -d` to start the backend. Qdrant is already running externally and reached via `QDRANT_URL`.

## Coding Standards

- Python: type hints throughout, validated by `mypy`. Pydantic v2 models for every request and response body and for every structured value crossing a service boundary, not just config. Keep route handlers thin and push logic into services so it stays testable. Format and lint with `ruff`.
- Configuration: a single `Settings(BaseSettings)` object loaded from `.env` via `pydantic-settings`; inject it rather than reading environment variables ad hoc.
- TypeScript: strict mode, functional components, no `any`. Format with `prettier`.
- Follow the installed skills for conventions in their domains.
- Do not add features outside SPEC.md without flagging them first. Multi-PDF support, authentication, multi-tenant logic, and an admin dashboard are explicitly out of scope for v1; see SPEC.md section on scope.
- Keep commits small and scoped to one logical change.

## Production Quality Bar

All source code in this repo is production grade, even though the scope is a small MVP. Production quality here means correct and robust, not gold plated:

- No placeholders, stubs, empty `TODO` bodies, commented-out code, or fake/mock data on real code paths. If something cannot be finished, raise it rather than leaving a stub behind.
- Validate every external input (API bodies, env, PDF content, OpenAI and Qdrant responses) with Pydantic and handle the failure paths explicitly.
- Handle errors deliberately: recover where you can, surface clear messages, and never swallow exceptions silently. External calls (OpenAI, Qdrant) have timeouts, retries where sensible, and graceful degradation.
- Structured logging for operationally useful events; never log secrets.
- Code is typed (mypy clean), linted and formatted (ruff and prettier clean), and covered by tests for the RAG pipeline and the API surface.
- No secrets, keys, or hardcoded environment specifics in source; everything environment dependent comes through `Settings`.
- "Simplest correct solution" still applies: production quality is robustness and clarity, not added abstraction or premature generalization. Reach for the `python-design-patterns` skill's KISS guidance before introducing a new layer.

## AI Output Rules (important, do not skip)

- The chatbot must never produce an em-dash character in any generated reply. Enforce this two ways: state it directly in the system prompt sent to OpenAI, and add a defensive post-processing step on the backend that replaces any em-dash with a comma or period before the reply is returned to the frontend, in case the model ignores the instruction. Because replies stream, apply this safeguard to each streamed chunk as it is emitted, not only to the final assembled text.
- This rule also applies to any user-facing text Claude Code writes by hand: UI copy, error messages, README content, commit messages. Use commas, periods, or parentheses instead of em-dashes everywhere in this project.
- The chatbot must answer only from the retrieved context (the client PDF, or the demo corpus when no PDF is ingested). If the retrieved chunks do not contain the answer, the reply should say so plainly and point to the configured fallback contact rather than guessing or using outside knowledge.

## Environment Variables

See `.env.example` for the full list, loaded through `pydantic-settings`. Never commit a populated `.env` file or the source PDF to git (both are gitignored).

## Security Notes

- Restrict FastAPI CORS to the actual domain(s) the widget will be embedded on, plus localhost during development.
- The PDF ingestion script is an operator-run tool, not a public upload endpoint. Do not expose a public file upload route in v1.
- Do not log the OpenAI API key, the Qdrant API key, or any secret values.

## Workflow Notes

- Build the backend and verify the RAG pipeline (including streaming) with direct API calls (curl or a REST client) before wiring up the frontend widget. With no PDF ingested, the demo corpus makes this possible immediately.
- Once the real PDF is available, write a short list of 5 to 8 questions drawn from its actual content and manually verify the chatbot answers them correctly and refuses gracefully outside that scope, before calling the feature done.
- If a choice in SPEC.md (model names, deployment target) does not fit the actual hosting situation, raise it before building rather than silently changing it.
