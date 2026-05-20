import { NextRequest, NextResponse } from "next/server";
import { backendFetch, BackendApiError } from "@/lib/server-api";

function getAuthHeaders(accessToken: string): Record<string, string> {
  return { Authorization: `Bearer ${accessToken}` };
}

function buildBackendUrl(pathSegments: string[], searchParams: URLSearchParams): string {
  const path = pathSegments.join("/");
  const qs = searchParams.toString();
  const base = path ? `/api/v1/review/${path}` : "/api/v1/review";
  return `${base}${qs ? `?${qs}` : ""}`;
}

type Params = { params: Promise<{ path?: string[] }> };

async function resolvePath(params: Params["params"]): Promise<string[]> {
  const { path } = await params;
  return path ?? [];
}

export async function GET(request: NextRequest, ctx: Params) {
  try {
    const accessToken = request.cookies.get("access_token")?.value;
    if (!accessToken) {
      return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const pathSegments = await resolvePath(ctx.params);
    const url = buildBackendUrl(pathSegments, request.nextUrl.searchParams);

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
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function POST(request: NextRequest, ctx: Params) {
  try {
    const accessToken = request.cookies.get("access_token")?.value;
    if (!accessToken) {
      return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const pathSegments = await resolvePath(ctx.params);
    const url = buildBackendUrl(pathSegments, request.nextUrl.searchParams);

    const contentType = request.headers.get("content-type") || "";
    let body: FormData | string;
    const headers: Record<string, string> = getAuthHeaders(accessToken);

    if (contentType.includes("multipart/form-data")) {
      body = await request.formData();
    } else {
      body = await request.text();
      headers["Content-Type"] = "application/json";
    }

    const data = await backendFetch(url, {
      method: "POST",
      headers,
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
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function PUT(request: NextRequest, ctx: Params) {
  try {
    const accessToken = request.cookies.get("access_token")?.value;
    if (!accessToken) {
      return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const pathSegments = await resolvePath(ctx.params);
    const url = buildBackendUrl(pathSegments, request.nextUrl.searchParams);

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
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}
