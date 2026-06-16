"use client";

import { useCallback, useRef, useState } from "react";

import { streamChat } from "@/lib/chatStream";
import type { ChatMessage } from "@/lib/types";

const SESSION_KEY = "rag-chatbot-session-id";

function newId(): string {
  return Math.random().toString(36).slice(2) + Date.now().toString(36);
}

function loadSessionId(): string | null {
  if (typeof window === "undefined") return null;
  return window.localStorage.getItem(SESSION_KEY);
}

export interface UseChat {
  messages: ChatMessage[];
  isStreaming: boolean;
  send: (text: string) => Promise<void>;
}

export function useChat(): UseChat {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isStreaming, setIsStreaming] = useState(false);
  const sessionIdRef = useRef<string | null>(loadSessionId());

  const updateAssistant = useCallback((id: string, updater: (prev: string) => string) => {
    setMessages((prev) =>
      prev.map((m) => (m.id === id ? { ...m, content: updater(m.content) } : m)),
    );
  }, []);

  const send = useCallback(
    async (text: string) => {
      const trimmed = text.trim();
      if (!trimmed || isStreaming) return;

      const userMessage: ChatMessage = { id: newId(), role: "user", content: trimmed };
      const assistantId = newId();
      setMessages((prev) => [
        ...prev,
        userMessage,
        { id: assistantId, role: "assistant", content: "" },
      ]);
      setIsStreaming(true);

      let errored = false;
      await streamChat(trimmed, sessionIdRef.current, {
        onSession: (id) => {
          sessionIdRef.current = id;
          if (typeof window !== "undefined") window.localStorage.setItem(SESSION_KEY, id);
        },
        onToken: (token) => updateAssistant(assistantId, (prev) => prev + token),
        onError: (message) => {
          errored = true;
          updateAssistant(assistantId, () => message);
        },
      });

      if (!errored) {
        updateAssistant(assistantId, (prev) =>
          prev.length > 0 ? prev : "I did not receive a response. Please try again.",
        );
      }
      setIsStreaming(false);
    },
    [isStreaming, updateAssistant],
  );

  return { messages, isStreaming, send };
}
