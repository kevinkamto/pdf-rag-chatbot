import type { Metadata } from "next";

import "./globals.css";

export const metadata: Metadata = {
  title: "RAG Chatbot",
  description: "Ask questions answered from your PDF knowledge base.",
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" suppressHydrationWarning>
      <body className="antialiased">{children}</body>
    </html>
  );
}
