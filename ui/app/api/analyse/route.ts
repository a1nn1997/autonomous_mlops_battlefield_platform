import { NextResponse } from "next/server";

export interface DataPoint {
  date: string;
  actual: number;
  forecast?: number;
  lightgbm?: number;
  ets?: number;
  naive?: number;
  s_naive?: number;
  isDrift?: boolean;
}

export interface TradeoffProfile {
  id: "latency" | "accuracy" | "balanced" | "custom";
  name: string;
  badge: string;
  targetWape: string;
  targetLatencyMs: number;
  maxRps: number;
  memoryMb: number;
  architecture: string;
  pros: string;
  cons: string;
  recommendedFor: string;
}

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const res = await fetch(`${BACKEND_URL}/api/analyse`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error: any) {
    console.error("[Analyse API Proxy Error]", error);
    return NextResponse.json(
      {
        error: error.message || "Failed to reach deep analyse backend service on " + BACKEND_URL,
      },
      { status: 502 }
    );
  }
}
