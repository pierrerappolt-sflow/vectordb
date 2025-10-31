import { NextRequest, NextResponse } from "next/server";

export async function GET(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const params = await context.params;
  const path = params.path?.join("/") || "";
  const searchParams = request.nextUrl.searchParams.toString();
  const url = `http://rabbitmq:15672/${path}${searchParams ? `?${searchParams}` : ""}`;

  // Auto-authenticate with guest/guest
  const auth = Buffer.from("guest:guest").toString("base64");

  try {
    const response = await fetch(url, {
      headers: {
        ...Object.fromEntries(request.headers),
        host: "rabbitmq:15672",
        authorization: `Basic ${auth}`,
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
    console.error("RabbitMQ proxy error:", error);
    return NextResponse.json({ error: "Proxy error" }, { status: 502 });
  }
}

export async function POST(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> }
) {
  const params = await context.params;
  const path = params.path?.join("/") || "";
  const url = `http://rabbitmq:15672/${path}`;

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

    return new NextResponse(response.body, {
      status: response.status,
      headers,
    });
  } catch (error) {
    console.error("RabbitMQ proxy error:", error);
    return NextResponse.json({ error: "Proxy error" }, { status: 502 });
  }
}
