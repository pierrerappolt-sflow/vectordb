import { NextRequest, NextResponse } from "next/server";
import { getSampleDocuments } from "@/lib/sample-data";

export async function GET(request: NextRequest) {
  try {
    const searchParams = request.nextUrl.searchParams;
    const count = parseInt(searchParams.get("count") || "100", 10);

    // Validate count
    if (count < 1 || count > 1000) {
      return NextResponse.json(
        { error: "Count must be between 1 and 1000" },
        { status: 400 }
      );
    }

    const documents = await getSampleDocuments(count);

    return NextResponse.json({
      documents,
      total: documents.length,
    });
  } catch (error) {
    console.error("Error fetching sample documents:", error);
    return NextResponse.json(
      { error: "Failed to fetch sample documents" },
      { status: 500 }
    );
  }
}
