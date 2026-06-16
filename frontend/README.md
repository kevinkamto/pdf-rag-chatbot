# RAG Chatbot Frontend

ChatGPT-like Next.js app: a chat pane plus a sidebar to add and remove the PDFs
that make up the knowledge base. A chat-only view (`/widget`) is exposed for
embedding into other websites through `public/embed.js`.

## Quick start

```bash
pnpm install
cp .env.example .env.local   # set BACKEND_URL and MANAGEMENT_SECRET
pnpm dev
```

Open http://localhost:3000 for the app, or http://localhost:3000/widget for the
embeddable chat view.

## Checks

```bash
pnpm lint
pnpm format:check
pnpm build
```

## Architecture notes

- All backend calls go through same-origin Next.js route handlers in
  `app/api/*`, which attach the management secret server-side. The browser never
  sees the secret and there are no cross-origin requests.
- `app/api/chat` proxies the Server-Sent-Events stream from the backend.
- Embedding: add this to any site:
  `<script src="https://YOUR_HOST/embed.js" data-base-url="https://YOUR_HOST" defer></script>`
