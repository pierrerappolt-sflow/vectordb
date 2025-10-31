import { NextRequest, NextResponse } from "next/server";

export const dynamic = 'force-dynamic';

export async function GET(request: NextRequest) {
  const searchParams = request.nextUrl.searchParams.toString();
  const url = `http://rabbitmq:15672/${searchParams ? `?${searchParams}` : ""}`;

  // Auto-authenticate with guest/guest
  const auth = Buffer.from("guest:guest").toString("base64");

  try {
    const response = await fetch(url, {
      headers: {
        accept: request.headers.get("accept") || "*/*",
        "accept-language": request.headers.get("accept-language") || "en-US,en;q=0.9",
        "user-agent": request.headers.get("user-agent") || "Mozilla/5.0",
        authorization: `Basic ${auth}`,
      },
      cache: "no-store",
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
    console.error("RabbitMQ proxy error:", error);
    return NextResponse.json({ error: "Proxy error" }, { status: 502 });
  }
}

export async function POST(request: NextRequest) {
  const url = "http://rabbitmq:15672/";

  // Auto-authenticate with guest/guest
  const auth = Buffer.from("guest:guest").toString("base64");

  try {
    const response = await fetch(url, {
      method: "POST",
      headers: {
        ...Object.fromEntries(request.headers),
        host: "rabbitmq:15672",
        authorization: `Basic ${auth}`,
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
    console.error("RabbitMQ proxy error:", error);
    return NextResponse.json({ error: "Proxy error" }, { status: 502 });
  }
}
