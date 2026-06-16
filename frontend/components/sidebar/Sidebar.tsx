"use client";

import { FileText, Loader2, MessageSquare, Plus, Trash2 } from "lucide-react";
import { useCallback, useEffect, useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { deleteDocument, fetchDocuments, uploadDocument } from "@/lib/documents";
import type { KnowledgeDocument } from "@/lib/types";
import { cn } from "@/lib/utils";

export function Sidebar() {
  const [documents, setDocuments] = useState<KnowledgeDocument[]>([]);
  const [loading, setLoading] = useState(true);
  const [uploading, setUploading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const refresh = useCallback(async () => {
    try {
      setDocuments(await fetchDocuments());
      setError(null);
    } catch {
      setError("Could not load documents.");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void refresh();
  }, [refresh]);

  async function onFileSelected(event: React.ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file) return;

    setUploading(true);
    setError(null);
    try {
      await uploadDocument(file);
      await refresh();
    } catch (err) {
      setError(err instanceof Error ? err.message : "Upload failed.");
    } finally {
      setUploading(false);
    }
  }

  async function onDelete(id: string) {
    setDeletingId(id);
    setError(null);
    try {
      await deleteDocument(id);
      setDocuments((prev) => prev.filter((d) => d.id !== id));
    } catch (err) {
      setError(err instanceof Error ? err.message : "Delete failed.");
    } finally {
      setDeletingId(null);
    }
  }

  return (
    <aside className="flex h-full w-72 shrink-0 flex-col border-r bg-card">
      <div className="flex items-center gap-2 px-4 py-4">
        <MessageSquare className="h-5 w-5 text-primary" />
        <span className="text-sm font-semibold">RAG Chatbot</span>
      </div>

      <div className="px-4">
        <input
          ref={fileInputRef}
          type="file"
          accept="application/pdf,.pdf"
          className="hidden"
          onChange={onFileSelected}
        />
        <Button
          className="w-full"
          variant="default"
          disabled={uploading}
          onClick={() => fileInputRef.current?.click()}
        >
          {uploading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Plus className="h-4 w-4" />}
          {uploading ? "Uploading..." : "Add PDF"}
        </Button>
      </div>

      <div className="mt-4 px-4 text-xs font-medium uppercase tracking-wide text-muted-foreground">
        Knowledge base
      </div>

      <div className="mt-2 flex-1 overflow-y-auto px-2">
        {loading ? (
          <div className="flex items-center justify-center py-8 text-muted-foreground">
            <Loader2 className="h-5 w-5 animate-spin" />
          </div>
        ) : documents.length === 0 ? (
          <p className="px-2 py-6 text-center text-sm text-muted-foreground">
            No documents yet. Add a PDF to ground answers in it.
          </p>
        ) : (
          <ul className="flex flex-col gap-1">
            {documents.map((doc) => (
              <li
                key={doc.id}
                className="group flex items-center gap-2 rounded-lg px-2 py-2 hover:bg-accent"
              >
                <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                <div className="min-w-0 flex-1">
                  <p className="truncate text-sm" title={doc.filename}>
                    {doc.filename}
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {doc.status === "ready" ? `${doc.chunk_count} chunks` : doc.status}
                  </p>
                </div>
                <button
                  type="button"
                  aria-label={`Remove ${doc.filename}`}
                  onClick={() => onDelete(doc.id)}
                  disabled={deletingId === doc.id}
                  className={cn(
                    "rounded p-1 text-muted-foreground opacity-0 transition hover:text-destructive group-hover:opacity-100",
                    deletingId === doc.id && "opacity-100",
                  )}
                >
                  {deletingId === doc.id ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Trash2 className="h-4 w-4" />
                  )}
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {error && (
        <p className="border-t px-4 py-2 text-xs text-destructive" role="alert">
          {error}
        </p>
      )}
    </aside>
  );
}
