import { NextRequest, NextResponse } from "next/server";

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams.toString();
  const url = `http://temporal-ui:8080/${searchParams ? `?${searchParams}` : ""}`;

  try {
    const response = await fetch(url, {
      headers: {
        accept: request.headers.get("accept") || "*/*",
        "accept-language": request.headers.get("accept-language") || "en-US,en;q=0.9",
        "user-agent": request.headers.get("user-agent") || "Mozilla/5.0",
      },
      cache: "no-store",
    });

    const headers = new Headers(response.headers);
    headers.delete("x-frame-options");
    headers.delete("content-security-policy");
    headers.delete("content-encoding");

    // For HTML responses, rewrite paths to include /api/temporal prefix
    const contentType = response.headers.get("content-type") || "";
    if (contentType.includes("text/html")) {
      const html = await response.text();
      const rewrittenHtml = html
        .replace(/href="\/_app\//g, 'href="/api/temporal/_app/')
        .replace(/src="\/_app\//g, 'src="/api/temporal/_app/')
        .replace(/from\("\/_app\//g, 'from("/api/temporal/_app/')
        .replace(/import\("\/_app\//g, 'import("/api/temporal/_app/');

      return new NextResponse(rewrittenHtml, {
        status: response.status,
        headers,
      });
    }

    return new NextResponse(response.body, {
      status: response.status,
      headers,
    });
  } catch (error) {
    console.error("Temporal proxy error:", error);
    return NextResponse.json({ error: "Proxy error" }, { status: 502 });
  }
}

export async function POST(request: NextRequest) {
  const url = "http://temporal-ui:8080/";

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
