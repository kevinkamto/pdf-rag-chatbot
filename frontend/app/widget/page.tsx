import { ChatPane } from "@/components/chat/ChatPane";

/**
 * Chat-only view embedded by public/embed.js as an iframe. No sidebar or
 * document management, so it is safe to expose on a public client website.
 */
export default function WidgetPage() {
  return (
    <main className="h-screen w-full">
      <ChatPane title="Chat with us" />
    </main>
  );
}
