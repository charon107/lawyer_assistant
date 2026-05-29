import { NextRequest, NextResponse } from "next/server";
import { backendFetch, BackendApiError } from "@/lib/server-api";

function getAuthHeaders(accessToken: string): Record<string, string> {
  return { Authorization: `Bearer ${accessToken}` };
}

function extractPath(pathSegments: string[]): string {
  return pathSegments.join("/");
}

function buildBackendUrl(path: string, searchParams: URLSearchParams): string {
  const qs = searchParams.toString();
  const base = path ? `/api/v1/commercial/${path}` : "/api/v1/commercial";
  return `${base}${qs ? `?${qs}` : ""}`;
}

type Params = { params: Promise<{ path?: string[] }> };

async function resolvePath(params: Params["params"]): Promise<string> {
  const { path } = await params;
  return extractPath(path ?? []);
}

export async function GET(request: NextRequest, ctx: Params) {
  try {
    const accessToken = request.cookies.get("access_token")?.value;
    if (!accessToken) {
      return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const pathStr = await resolvePath(ctx.params);
    const url = buildBackendUrl(pathStr, request.nextUrl.searchParams);

    const data = await backendFetch(url, {
      headers: getAuthHeaders(accessToken),
    });

    return NextResponse.json(data);
  } catch (error) {
    if (error instanceof BackendApiError) {
      return NextResponse.json(
        { detail: error.message || "Request failed" },
        { status: error.status }
      );
    }
    return NextResponse.json({ detail: "Internal server error" }, { status: 500 });
  }
}

export async function POST(request: NextRequest, ctx: Params) {
  try {
    const accessToken = request.cookies.get("access_token")?.value;
    if (!accessToken) {
      return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const pathStr = await resolvePath(ctx.params);
    const url = buildBackendUrl(pathStr, request.nextUrl.searchParams);
    const body = await request.text();

    const data = await backendFetch(url, {
      method: "POST",
      headers: {
        ...getAuthHeaders(accessToken),
        "Content-Type": "application/json",
      },
      body,
    });

    return NextResponse.json(data);
  } catch (error) {
    if (error instanceof BackendApiError) {
      return NextResponse.json(
        { detail: error.message || "Request failed" },
        { status: error.status }
      );
    }
    return NextResponse.json({ detail: "Internal server error" }, { status: 500 });
  }
}

export async function PUT(request: NextRequest, ctx: Params) {
  try {
    const accessToken = request.cookies.get("access_token")?.value;
    if (!accessToken) {
      return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const pathStr = await resolvePath(ctx.params);
    const url = buildBackendUrl(pathStr, request.nextUrl.searchParams);
    const body = await request.text();

    const data = await backendFetch(url, {
      method: "PUT",
      headers: {
        ...getAuthHeaders(accessToken),
        "Content-Type": "application/json",
      },
      body,
    });

    return NextResponse.json(data);
  } catch (error) {
    if (error instanceof BackendApiError) {
      return NextResponse.json(
        { detail: error.message || "Request failed" },
        { status: error.status }
      );
    }
    return NextResponse.json({ detail: "Internal server error" }, { status: 500 });
  }
}
