import { NextResponse } from "next/server";

export interface ModelBattleResult {
  id: string;
  name: string;
  shortName: string;
  category: "Classical ML" | "Time Series" | "Baseline";
  wape: number;
  bias: number;
  mae: number;
  rmse: number;
  latencyP50: number;
  latencyP95: number;
  throughputRps: number;
  memoryMb: number;
  rank: number;
  isChampion: boolean;
  deltaVsNaive: number;
  color: string;
  hyperparameters?: Record<string, any>;
}

export interface BattleTimeSeriesPoint {
  date: string;
  actual: number;
  lightgbm?: number;
  ets?: number;
  s_naive?: number;
  naive?: number;
  moving_avg?: number;
}

export interface ModelConfigs {
  lightgbm?: {
    objective?: "l1" | "l2" | "huber";
    learningRate?: number;
    numLeaves?: number;
    useLags?: boolean;
  };
  ets?: {
    seasonalPeriod?: number;
    trendType?: "additive" | "multiplicative" | "none";
    seasonalType?: "additive" | "multiplicative";
    damped?: boolean;
  };
  s_naive?: { cycleLag?: number };
  moving_avg?: { windowSize?: number };
  primaryMetric?: "wape" | "mae" | "rmse" | "bias";
}

export interface BulkDatasetItem {
  id: string;
  name: string;
  csvContent?: string;
  datasetType?: string;
}

const BACKEND_URL = process.env.BACKEND_URL || "http://127.0.0.1:8000";

export async function POST(req: Request) {
  try {
    const body = await req.json();
    const res = await fetch(`${BACKEND_URL}/api/battle`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });

    const data = await res.json();
    return NextResponse.json(data, { status: res.status });
  } catch (error: any) {
    console.error("[Battle API Proxy Error]", error);
    return NextResponse.json(
      {
        error: error.message || "Failed to reach model battle backend service on " + BACKEND_URL,
      },
      { status: 502 }
    );
  }
}
