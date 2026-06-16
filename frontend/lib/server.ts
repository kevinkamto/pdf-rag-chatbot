import "server-only";

/**
 * Server-only backend configuration. The management secret never reaches the
 * browser: route handlers attach it when proxying to the FastAPI backend.
 */
export const BACKEND_URL = (process.env.BACKEND_URL ?? "http://localhost:8000").replace(/\/$/, "");
export const MANAGEMENT_SECRET = process.env.MANAGEMENT_SECRET ?? "change-me";

export function managementHeaders(): HeadersInit {
  return { "X-Management-Secret": MANAGEMENT_SECRET };
}
