// Backend write calls go through the Next.js server proxy so the
// X-API-Key write token stays server-side (see app/api/backend/[...path]).
export function backendWrite(path: string, body?: unknown): Promise<Response> {
  return fetch(`/api/backend/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
}
