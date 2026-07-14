import { NextRequest, NextResponse } from "next/server";

// Server-side proxy for backend WRITE endpoints. The backend requires an
// X-API-Key on mutations; attaching it here keeps the token out of the
// client bundle. Operators choose the deployment mode:
//   - API_WRITE_TOKEN set   → UI write features (create world, interventions)
//     work for visitors, while direct API access still requires the token.
//   - API_WRITE_TOKEN unset → proxied writes get 403 from the backend and
//     the UI degrades to observation-only.
const BACKEND_URL =
  process.env.BACKEND_INTERNAL_URL ||
  process.env.NEXT_PUBLIC_API_URL ||
  "http://localhost:3301";

const UUID = "[0-9a-fA-F-]{36}";
// Only the known UI write paths may be proxied with the token attached.
const ALLOWED_POSTS: RegExp[] = [
  new RegExp(`^worlds$`),
  new RegExp(`^worlds/${UUID}/(start|stop|seed-bomb|events)$`),
  new RegExp(`^worlds/${UUID}/agents/${UUID}/whisper$`),
];

async function forward(
  req: NextRequest,
  params: Promise<{ path: string[] }>,
): Promise<NextResponse> {
  const { path } = await params;
  const joined = path.join("/");

  if (!ALLOWED_POSTS.some((re) => re.test(joined))) {
    return NextResponse.json({ detail: "Path not proxied" }, { status: 404 });
  }

  const headers: Record<string, string> = { "Content-Type": "application/json" };
  if (process.env.API_WRITE_TOKEN) {
    headers["X-API-Key"] = process.env.API_WRITE_TOKEN;
  }

  const body = await req.text();
  const resp = await fetch(`${BACKEND_URL}/api/${joined}${req.nextUrl.search}`, {
    method: "POST",
    headers,
    body: body || undefined,
    cache: "no-store",
  });

  const text = await resp.text();
  return new NextResponse(text, {
    status: resp.status,
    headers: {
      "Content-Type": resp.headers.get("Content-Type") ?? "application/json",
    },
  });
}

export async function POST(
  req: NextRequest,
  ctx: { params: Promise<{ path: string[] }> },
) {
  return forward(req, ctx.params);
}
