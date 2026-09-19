import { NextRequest, NextResponse } from "next/server";
import { createMockResponse } from "@/lib/mock-data";

const backendUrl = process.env.BACKEND_URL || "http://localhost:8000";

export async function POST(request: NextRequest) {
  try {
    const contentType = request.headers.get("content-type") || "";
    let backendRequest: RequestInit;

    if (contentType.includes("multipart/form-data")) {
      const formData = await request.formData();
      const forwardedForm = new FormData();
      const prompt = formData.get("prompt");
      const messages = formData.get("messages");
      const uploadedFile = formData.get("file");

      if (typeof prompt === "string") forwardedForm.append("prompt", prompt);
      if (typeof messages === "string") forwardedForm.append("messages", messages);
      if (uploadedFile instanceof File) forwardedForm.append("file", uploadedFile, uploadedFile.name);

      backendRequest = { method: "POST", body: forwardedForm };
    } else {
      backendRequest = {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: await request.text(),
      };
    }

    const backendResponse = await fetch(`${backendUrl}/api/chat`, backendRequest);
    const responseBody = await backendResponse.json();

    return NextResponse.json(responseBody, { status: backendResponse.status });
  } catch {
    const body = await request.clone().json().catch(() => ({ prompt: "all" }));
    const fallback = createMockResponse(typeof body?.prompt === "string" ? body.prompt : "all");

    return NextResponse.json(
      {
        ...fallback,
        source: "demo",
        warning: "Backend unavailable; showing demo data.",
      },
      { status: 200 }
    );
  }
}
