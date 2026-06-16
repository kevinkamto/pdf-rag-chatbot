import { BACKEND_URL } from "@/lib/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/** Proxy the chat request to the backend and stream the SSE response back. */
export async function POST(request: Request): Promise<Response> {
  const body = await request.text();

  let upstream: Response;
  try {
    upstream = await fetch(`${BACKEND_URL}/api/chat`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body,
    });
  } catch {
    return new Response("Backend unavailable", { status: 502 });
  }

  if (!upstream.ok || !upstream.body) {
    return new Response("Backend error", { status: upstream.status || 502 });
  }

  return new Response(upstream.body, {
    status: 200,
    headers: {
      "Content-Type": "text/event-stream; charset=utf-8",
      "Cache-Control": "no-cache, no-transform",
      "X-Accel-Buffering": "no",
    },
  });
}
