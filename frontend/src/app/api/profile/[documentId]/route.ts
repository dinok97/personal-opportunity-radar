import { NextResponse } from "next/server";

const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

type RouteContext = {
  params: Promise<{ documentId: string }>;
};

export async function GET(_request: Request, { params }: RouteContext) {
  const { documentId } = await params;

  try {
    const backendResponse = await fetch(
      `${backendUrl}/api/profile/${encodeURIComponent(documentId)}`,
      { cache: "no-store" },
    );
    const responseBody = await backendResponse.json();

    return NextResponse.json(responseBody, { status: backendResponse.status });
  } catch {
    return NextResponse.json(
      { detail: "Profile service is unavailable." },
      { status: 503 },
    );
  }
}
