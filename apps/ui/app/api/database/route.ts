import { NextRequest, NextResponse } from "next/server";

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams.toString();
  const url = `http://adminer:8080/${searchParams ? `?${searchParams}` : ""}`;

  try {
    const response = await fetch(url, {
      headers: {
        accept: request.headers.get("accept") || "*/*",
        "accept-language": request.headers.get("accept-language") || "en-US,en;q=0.9",
        "user-agent": request.headers.get("user-agent") || "Mozilla/5.0",
        ...(request.headers.get("cookie") && { cookie: request.headers.get("cookie")! }),
      },
      cache: "no-store",
    });

    const headers = new Headers(response.headers);
    headers.delete("x-frame-options");
    headers.delete("content-security-policy");
    // Remove content-encoding to avoid decompression issues
    headers.delete("content-encoding");

    return new NextResponse(response.body, {
      status: response.status,
      headers,
    });
  } catch (error) {
    console.error("Database proxy error:", error);
    return NextResponse.json({ error: "Proxy error" }, { status: 502 });
  }
}

export async function POST(request: NextRequest) {
  const url = "http://adminer:8080/";

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        ...Object.fromEntries(request.headers),
        host: "adminer:8080",
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
    console.error("Database proxy error:", error);
    return NextResponse.json({ error: "Proxy error" }, { status: 502 });
  }
}
