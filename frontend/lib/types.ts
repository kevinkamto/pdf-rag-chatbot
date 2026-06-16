export type Role = "user" | "assistant";

export interface ChatMessage {
  id: string;
  role: Role;
  content: string;
}

export type DocumentStatus = "processing" | "ready" | "failed";

export interface KnowledgeDocument {
  id: string;
  filename: string;
  status: DocumentStatus;
  chunk_count: number;
  created_at: string;
}
