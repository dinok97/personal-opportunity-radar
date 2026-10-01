import { NextResponse } from "next/server";

const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

export async function GET() {
  try {
    const response = await fetch(`${backendUrl}/api/user`, { cache: "no-store" });
    const body = await response.json();

    return NextResponse.json(body, {
      status: response.status,
      headers: { "Cache-Control": "no-store" },
    });
  } catch {
    return NextResponse.json(
      { detail: "The profile service is unavailable." },
      { status: 503, headers: { "Cache-Control": "no-store" } }
    );
  }
}