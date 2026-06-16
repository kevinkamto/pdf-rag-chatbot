"use client";

import { useChat } from "./useChat";
import { ChatInput } from "./ChatInput";
import { MessageList } from "./MessageList";

export function ChatPane({ title = "Assistant" }: { title?: string }) {
  const { messages, isStreaming, send } = useChat();

  return (
    <div className="flex h-full flex-col bg-background">
      <header className="flex items-center gap-2 border-b px-5 py-3.5">
        <span className="h-2.5 w-2.5 rounded-full bg-emerald-500" />
        <h1 className="text-sm font-semibold">{title}</h1>
      </header>

      <div className="flex-1 overflow-y-auto px-5 py-6">
        <div className="mx-auto h-full max-w-2xl">
          <MessageList messages={messages} isStreaming={isStreaming} />
        </div>
      </div>

      <div className="border-t px-5 py-4">
        <div className="mx-auto max-w-2xl">
          <ChatInput disabled={isStreaming} onSend={send} />
          <p className="mt-2 text-center text-xs text-muted-foreground">
            Answers come only from the knowledge base.
          </p>
        </div>
      </div>
    </div>
  );
}
