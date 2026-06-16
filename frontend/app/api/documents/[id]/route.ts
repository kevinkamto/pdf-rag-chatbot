import { NextResponse } from "next/server";

import { BACKEND_URL, managementHeaders } from "@/lib/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/** Remove a document and its vectors. */
export async function DELETE(
  _request: Request,
  context: { params: Promise<{ id: string }> },
): Promise<Response> {
  const { id } = await context.params;
  try {
    const upstream = await fetch(`${BACKEND_URL}/api/documents/${encodeURIComponent(id)}`, {
      method: "DELETE",
      headers: managementHeaders(),
    });
    if (upstream.status === 204) {
      return new NextResponse(null, { status: 204 });
    }
    const data = await upstream.json().catch(() => ({ detail: "Delete failed." }));
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json({ detail: "Backend unavailable" }, { status: 502 });
  }
}
