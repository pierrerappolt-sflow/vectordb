import { NextRequest, NextResponse } from "next/server";

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const params = await context.params;
  const path = params.path?.join("/") || "";
  const searchParams = request.nextUrl.searchParams.toString();
  const url = `http://temporal-ui:8080/${path}${searchParams ? `?${searchParams}` : ""}`;

  try {
    const response = await fetch(url, {
      headers: {
        ...Object.fromEntries(request.headers),
        host: "temporal-ui:8080",
      },
    });

    const headers = new Headers(response.headers);
    // Remove headers that block iframe embedding
    headers.delete("x-frame-options");
    headers.delete("content-security-policy");
    headers.delete("content-encoding");

    return new NextResponse(response.body, {
      status: response.status,
      headers,
    });
  } catch (error) {
    console.error("Temporal proxy error:", error);
    return NextResponse.json({ error: "Proxy error" }, { status: 502 });
  }
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const params = await context.params;
  const path = params.path?.join("/") || "";
  const url = `http://temporal-ui:8080/${path}`;

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        ...Object.fromEntries(request.headers),
        host: "temporal-ui:8080",
      },
      body: request.body,
      // @ts-ignore
      duplex: "half",
    });

    const headers = new Headers(response.headers);
    headers.delete("x-frame-options");
    headers.delete("content-security-policy");

    return new NextResponse(response.body, {
      status: response.status,
      headers,
    });
  } catch (error) {
    console.error("Temporal proxy error:", error);
    return NextResponse.json({ error: "Proxy error" }, { status: 502 });
  }
}
