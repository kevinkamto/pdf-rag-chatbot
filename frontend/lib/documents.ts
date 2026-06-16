import type { KnowledgeDocument } from "@/lib/types";

interface DocumentListResponse {
  documents: KnowledgeDocument[];
}

export async function fetchDocuments(): Promise<KnowledgeDocument[]> {
  const res = await fetch("/api/documents", { cache: "no-store" });
  if (!res.ok) throw new Error("Failed to load documents.");
  const data = (await res.json()) as DocumentListResponse;
  return data.documents;
}

export async function uploadDocument(file: File): Promise<KnowledgeDocument> {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch("/api/documents", { method: "POST", body: form });
  const data = (await res.json().catch(() => ({}))) as Partial<KnowledgeDocument> & {
    detail?: string;
  };
  if (!res.ok) {
    throw new Error(data.detail ?? "Upload failed.");
  }
  return data as KnowledgeDocument;
}

export async function deleteDocument(id: string): Promise<void> {
  const res = await fetch(`/api/documents/${encodeURIComponent(id)}`, { method: "DELETE" });
  if (!res.ok && res.status !== 204) {
    const data = (await res.json().catch(() => ({}))) as { detail?: string };
    throw new Error(data.detail ?? "Delete failed.");
  }
}
