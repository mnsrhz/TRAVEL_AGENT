import { NextRequest, NextResponse } from "next/server";

const BACKEND_API_BASE_URL =
  process.env.BACKEND_API_BASE_URL?.replace(/\/$/, "") ||
  process.env.NEXT_PUBLIC_API_BASE_URL?.replace(/\/$/, "");

type RouteContext = {
  params: Promise<{ path?: string[] }> | { path?: string[] };
};

export async function GET(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export async function POST(request: NextRequest, context: RouteContext) {
  return proxy(request, context);
}

export async function OPTIONS() {
  return new NextResponse(null, { status: 204 });
}

async function proxy(request: NextRequest, context: RouteContext) {
  if (!BACKEND_API_BASE_URL) {
    return NextResponse.json(
      { detail: "BACKEND_API_BASE_URL is not configured in Vercel." },
      { status: 500 }
    );
  }

  const params = await Promise.resolve(context.params);
  const path = (params.path || []).join("/");
  const target = new URL(`/api/${path}${request.nextUrl.search}`, BACKEND_API_BASE_URL);
  const body = request.method === "GET" || request.method === "HEAD" ? undefined : await request.arrayBuffer();

  const response = await fetch(target, {
    method: request.method,
    headers: forwardedHeaders(request),
    body,
    cache: "no-store"
  });

  return new NextResponse(response.body, {
    status: response.status,
    headers: responseHeaders(response)
  });
}

function forwardedHeaders(request: NextRequest) {
  const headers = new Headers();
  const contentType = request.headers.get("content-type");
  const accept = request.headers.get("accept");
  if (contentType) headers.set("content-type", contentType);
  if (accept) headers.set("accept", accept);
  return headers;
}

function responseHeaders(response: Response) {
  const headers = new Headers();
  for (const key of ["content-type", "content-disposition"]) {
    const value = response.headers.get(key);
    if (value) headers.set(key, value);
  }
  return headers;
}
