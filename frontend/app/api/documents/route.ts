import { NextResponse } from "next/server";

import { BACKEND_URL, managementHeaders } from "@/lib/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

/** List ingested documents. */
export async function GET(): Promise<Response> {
  try {
    const upstream = await fetch(`${BACKEND_URL}/api/documents`, {
      headers: managementHeaders(),
      cache: "no-store",
    });
    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json({ detail: "Backend unavailable" }, { status: 502 });
  }
}

/** Upload (and ingest) a new PDF. */
export async function POST(request: Request): Promise<Response> {
  const form = await request.formData();
  const file = form.get("file");
  if (!(file instanceof File)) {
    return NextResponse.json({ detail: "No file provided." }, { status: 400 });
  }

  const forwarded = new FormData();
  forwarded.append("file", file, file.name);

  try {
    const upstream = await fetch(`${BACKEND_URL}/api/documents`, {
      method: "POST",
      headers: managementHeaders(),
      body: forwarded,
    });
    const data = await upstream.json();
    return NextResponse.json(data, { status: upstream.status });
  } catch {
    return NextResponse.json({ detail: "Backend unavailable" }, { status: 502 });
  }
}
