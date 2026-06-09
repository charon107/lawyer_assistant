import { NextRequest, NextResponse } from "next/server";
import { backendFetch, BackendApiError } from "@/lib/server-api";
import type { RegisterResponse } from "@/types";

function extractDetail(data: unknown): string {
  if (!data) return "Registration failed";
  const d = data as Record<string, unknown>;
  // Custom app error: {"error": {"message": "..."}}
  const appErr = d.error as { message?: string } | undefined;
  if (appErr?.message) return appErr.message;
  // Pydantic validation error: {"detail": [{"msg": "...", ...}]}
  if (Array.isArray(d.detail)) {
    return d.detail.map((e: { msg?: string }) => e.msg || "").filter(Boolean).join("; ");
  }
  // Simple detail string
  if (typeof d.detail === "string") return d.detail;
  return "Registration failed";
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json();

    const data = await backendFetch<RegisterResponse>("/api/v1/auth/register", {
      method: "POST",
      body: JSON.stringify(body),
    });

    return NextResponse.json(data, { status: 201 });
  } catch (error) {
    if (error instanceof BackendApiError) {
      const detail = extractDetail(error.data);
      return NextResponse.json({ detail }, { status: error.status });
    }
    return NextResponse.json(
      { detail: "Internal server error" },
      { status: 500 }
    );
  }
}
