import { ChatPane } from "@/components/chat/ChatPane";
import { Sidebar } from "@/components/sidebar/Sidebar";

export default function Home() {
  return (
    <main className="flex h-screen w-full overflow-hidden">
      <Sidebar />
      <div className="min-w-0 flex-1">
        <ChatPane title="Knowledge Base Assistant" />
      </div>
    </main>
  );
}
