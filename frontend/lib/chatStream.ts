/**
 * Client-side Server-Sent-Events reader for the chat endpoint.
 *
 * Posts a message to the same-origin `/api/chat` proxy and invokes callbacks as
 * `session`, `token`, `done`, and `error` events arrive.
 */

export interface ChatStreamCallbacks {
  onSession?: (sessionId: string) => void;
  onToken?: (text: string) => void;
  onError?: (message: string) => void;
  onDone?: () => void;
}

interface SSEvent {
  event: string;
  data: string;
}

export async function streamChat(
  message: string,
  sessionId: string | null,
  callbacks: ChatStreamCallbacks,
  signal?: AbortSignal,
): Promise<void> {
  const response = await fetch("/api/chat", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId }),
    signal,
  });

  if (!response.ok || !response.body) {
    callbacks.onError?.("The assistant is unavailable right now. Please try again.");
    return;
  }

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      let separator = buffer.indexOf("\n\n");
      while (separator !== -1) {
        const rawEvent = buffer.slice(0, separator);
        buffer = buffer.slice(separator + 2);
        dispatch(parseEvent(rawEvent), callbacks);
        separator = buffer.indexOf("\n\n");
      }
    }
  } catch (error) {
    if ((error as Error).name !== "AbortError") {
      callbacks.onError?.("The connection was interrupted. Please try again.");
    }
  }
}

function parseEvent(raw: string): SSEvent {
  let event = "message";
  const dataLines: string[] = [];
  for (const line of raw.split("\n")) {
    if (line.startsWith("event:")) {
      event = line.slice(6).trim();
    } else if (line.startsWith("data:")) {
      dataLines.push(line.slice(5).trim());
    }
  }
  return { event, data: dataLines.join("\n") };
}

function dispatch(sse: SSEvent, callbacks: ChatStreamCallbacks): void {
  if (!sse.data) return;
  let payload: Record<string, unknown>;
  try {
    payload = JSON.parse(sse.data) as Record<string, unknown>;
  } catch {
    return;
  }

  switch (sse.event) {
    case "session":
      if (typeof payload.session_id === "string") callbacks.onSession?.(payload.session_id);
      break;
    case "token":
      if (typeof payload.text === "string") callbacks.onToken?.(payload.text);
      break;
    case "error":
      if (typeof payload.message === "string") callbacks.onError?.(payload.message);
      break;
    case "done":
      callbacks.onDone?.();
      break;
  }
}
