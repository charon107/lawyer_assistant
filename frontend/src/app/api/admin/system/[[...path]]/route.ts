import { NextRequest, NextResponse } from "next/server";
import { backendFetch, BackendApiError } from "@/lib/server-api";
import { requireAdmin } from "@/lib/admin-auth";

type Params = { params: Promise<{ path?: string[] }> };

function buildBackendUrl(path: string[], searchParams: URLSearchParams): string {
  const segments = path.length ? `/${path.join("/")}` : "";
  const qs = searchParams.toString();
  return `/api/v1/admin/system${segments}${qs ? `?${qs}` : ""}`;
}

export async function GET(request: NextRequest, ctx: Params) {
  try {
    const adminCheck = await requireAdmin(request);
    if ("error" in adminCheck) return adminCheck.error;
    const { accessToken } = adminCheck;

    const { path } = await ctx.params;
    const url = buildBackendUrl(path ?? [], request.nextUrl.searchParams);

    const data = await backendFetch(url, {
      headers: { Authorization: `Bearer ${accessToken}` },
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
    const adminCheck = await requireAdmin(request);
    if ("error" in adminCheck) return adminCheck.error;
    const { accessToken } = adminCheck;

    const { path } = await ctx.params;
    const url = buildBackendUrl(path ?? [], new URLSearchParams());

    const data = await backendFetch(url, {
      method: "POST",
      headers: { Authorization: `Bearer ${accessToken}` },
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
