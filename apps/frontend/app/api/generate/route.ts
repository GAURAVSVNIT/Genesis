
import { NextResponse } from "next/server";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    
    // Forward to Python backend
    const response = await fetch("http://127.0.0.1:8000/v1/blog/generate", {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
        const errorText = await response.text();
        console.error("Backend error:", response.status, errorText);
        return NextResponse.json({ error: `Backend error: ${response.status}`, details: errorText }, { status: response.status });
    }

    const data = await response.json();
    return NextResponse.json(data);
  } catch (error) {
    console.error("API Route Error:", error);
    return NextResponse.json({ error: "Internal Server Error" }, { status: 500 });
  }
}
