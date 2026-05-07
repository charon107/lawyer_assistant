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
  return `/api/v1/lpa-cases/${path}${qs ? `?${qs}` : ""}`;
}

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const accessToken = request.cookies.get("access_token")?.value;
    if (!accessToken) {
      return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const { path } = await params;
    const pathStr = extractPath(path);
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
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}

export async function POST(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const accessToken = request.cookies.get("access_token")?.value;
    if (!accessToken) {
      return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const { path } = await params;
    const pathStr = extractPath(path);
    const url = buildBackendUrl(pathStr, request.nextUrl.searchParams);

    const contentType = request.headers.get("content-type") || "";
    let body: FormData | string;
    const headers: Record<string, string> = getAuthHeaders(accessToken);

    if (contentType.includes("multipart/form-data")) {
      body = await request.formData();
      // Don't set Content-Type — let fetch set it with the boundary
    } else {
      body = await request.text();
      headers["Content-Type"] = "application/json";
    }

    const data = await backendFetch(url, {
      method: "POST",
      headers,
      body,
    });

    return NextResponse.json(data, { status: 201 });
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

export async function PATCH(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const accessToken = request.cookies.get("access_token")?.value;
    if (!accessToken) {
      return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const { path } = await params;
    const pathStr = extractPath(path);
    const url = buildBackendUrl(pathStr, request.nextUrl.searchParams);
    const body = await request.text();

    const data = await backendFetch(url, {
      method: "PATCH",
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

export async function DELETE(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  try {
    const accessToken = request.cookies.get("access_token")?.value;
    if (!accessToken) {
      return NextResponse.json({ detail: "Not authenticated" }, { status: 401 });
    }

    const { path } = await params;
    const pathStr = extractPath(path);
    const url = buildBackendUrl(pathStr, request.nextUrl.searchParams);

    await backendFetch(url, {
      method: "DELETE",
      headers: getAuthHeaders(accessToken),
    });

    return new NextResponse(null, { status: 204 });
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
