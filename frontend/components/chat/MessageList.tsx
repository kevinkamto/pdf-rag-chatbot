"use client";

import { useEffect, useRef } from "react";

import type { ChatMessage } from "@/lib/types";

import { MessageBubble } from "./MessageBubble";

interface MessageListProps {
  messages: ChatMessage[];
  isStreaming: boolean;
}

export function MessageList({ messages, isStreaming }: MessageListProps) {
  const endRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    endRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  if (messages.length === 0) {
    return (
      <div className="flex h-full flex-col items-center justify-center gap-2 text-center text-muted-foreground">
        <p className="text-lg font-medium text-foreground">Ask me anything</p>
        <p className="max-w-sm text-sm">
          I answer from the documents in the knowledge base. Add a PDF in the sidebar, or try the
          bundled sample.
        </p>
      </div>
    );
  }

  const lastIndex = messages.length - 1;
  return (
    <div className="flex flex-col gap-5">
      {messages.map((message, index) => (
        <MessageBubble
          key={message.id}
          message={message}
          streaming={isStreaming && index === lastIndex && message.role === "assistant"}
        />
      ))}
      <div ref={endRef} />
    </div>
  );
}
