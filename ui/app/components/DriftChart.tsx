"use client";

import React from "react";
import { AlertTriangle, CheckCircle, Flame, ArrowUpRight } from "lucide-react";

interface DriftReport {
  maxPsi: number;
  status: string;
  driftDetected: boolean;
  features: Array<{
    feature: string;
    psi: number;
    status: string;
    baseMean: number;
    currMean: number;
  }>;
  decayReport?: {
    currentWape: number;
    baselineWape: number;
    relativeDecay: number;
    normalizedBias: number;
    alert: boolean;
  };
}

interface DriftChartProps {
  report: DriftReport | null;
  onRetrainRequest: () => void;
}

export const DriftChart: React.FC<DriftChartProps> = ({ report, onRetrainRequest }) => {
  const defaultReport: DriftReport = {
    maxPsi: 0.042,
    status: "STABLE",
    driftDetected: false,
    features: [
      { feature: "sell_price", psi: 0.038, status: "STABLE", baseMean: 6.52, currMean: 6.55 },
      { feature: "rolling_mean_7", psi: 0.042, status: "STABLE", baseMean: 46.86, currMean: 46.90 },
      { feature: "rolling_mean_28", psi: 0.035, status: "STABLE", baseMean: 46.85, currMean: 46.88 },
      { feature: "lag_1", psi: 0.041, status: "STABLE", baseMean: 46.86, currMean: 46.84 },
      { feature: "lag_7", psi: 0.039, status: "STABLE", baseMean: 46.88, currMean: 46.85 },
    ],
    decayReport: {
      currentWape: 0.1325,
      baselineWape: 0.1325,
      relativeDecay: 0.0,
      normalizedBias: -0.012,
      alert: false,
    }
  };

  const activeReport = report || defaultReport;
  const isCritical = activeReport.maxPsi >= 0.20;

  return (
    <div className={`glass-panel ${isCritical ? "glass-card-glow-rose" : ""}`} style={{ padding: "20px" }}>
      
      {/* Header */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <h2 style={{ fontSize: "16px", fontWeight: "700" }}>Statistical Distribution Drift (PSI & KS)</h2>
            <span style={{
              fontSize: "11px",
              padding: "2px 8px",
              borderRadius: "10px",
              fontWeight: "600",
              background: isCritical ? "rgba(244, 63, 94, 0.2)" : "rgba(16, 185, 129, 0.2)",
              color: isCritical ? "#fda4af" : "#6ee7b7",
              border: isCritical ? "1px solid rgba(244, 63, 94, 0.4)" : "1px solid rgba(16, 185, 129, 0.4)",
            }}>
              {isCritical ? "CRITICAL DRIFT DETECTED" : "DISTRIBUTIONS STABLE"}
            </span>
          </div>
          <p style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "2px" }}>
            Population Stability Index comparing production traffic against reference training distributions.
          </p>
        </div>

        {isCritical && (
          <button
            onClick={onRetrainRequest}
            className="agent-btn agent-btn-primary"
            style={{ fontSize: "12px", padding: "6px 12px" }}
          >
            <Flame size={14} />
            <span>Retrain Shadow Model</span>
          </button>
        )}
      </div>

      {/* PSI Gauge & Key Telemetry Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "12px", marginBottom: "20px" }}>
        
        {/* Card 1: Max PSI */}
        <div style={{ background: "rgba(0,0,0,0.3)", padding: "14px", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>Max Feature PSI</div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginTop: "4px" }}>
            <span style={{ fontSize: "24px", fontWeight: "800", color: isCritical ? "var(--accent-rose)" : "var(--accent-emerald)" }}>
              {activeReport.maxPsi.toFixed(3)}
            </span>
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Threshold: 0.20</span>
          </div>
          <div style={{ fontSize: "11px", color: isCritical ? "#fda4af" : "var(--accent-emerald)", marginTop: "4px" }}>
            {isCritical ? "⚠ Critical Distribution Shift" : "✓ Population Stable (< 0.10)"}
          </div>
        </div>

        {/* Card 2: Rolling WAPE Decay */}
        <div style={{ background: "rgba(0,0,0,0.3)", padding: "14px", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>Rolling 14d WAPE</div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginTop: "4px" }}>
            <span style={{ fontSize: "24px", fontWeight: "800", color: isCritical ? "var(--accent-amber)" : "var(--text-primary)" }}>
              {((activeReport.decayReport?.currentWape || 0.1325) * 100).toFixed(1)}%
            </span>
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Base: 13.25%</span>
          </div>
          <div style={{ fontSize: "11px", color: isCritical ? "var(--accent-rose)" : "var(--accent-emerald)", marginTop: "4px" }}>
            {isCritical ? `+${((activeReport.decayReport?.relativeDecay || 0.38) * 100).toFixed(1)}% Degradation` : "Performance Nominal"}
          </div>
        </div>

        {/* Card 3: Forecast Tracking Bias */}
        <div style={{ background: "rgba(0,0,0,0.3)", padding: "14px", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", textTransform: "uppercase" }}>Forecast Bias</div>
          <div style={{ display: "flex", alignItems: "baseline", gap: "8px", marginTop: "4px" }}>
            <span style={{ fontSize: "24px", fontWeight: "800", color: isCritical ? "var(--accent-rose)" : "var(--text-primary)" }}>
              {((activeReport.decayReport?.normalizedBias || -0.012) * 100).toFixed(1)}%
            </span>
          </div>
          <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>
            {isCritical ? "Systematic Over-prediction" : "Near-Zero Bias (-1.2%)"}
          </div>
        </div>

      </div>

      {/* Feature-Level Drift Progress Bars */}
      <div style={{ display: "flex", flexDirection: "column", gap: "10px" }}>
        <div style={{ fontSize: "13px", fontWeight: "600", color: "var(--text-secondary)", marginBottom: "4px" }}>
          Feature Covariate Breakdown (PSI & Value Shifts):
        </div>

        {(activeReport.features || defaultReport.features).map((feat) => {
          const isFeatCritical = feat.psi >= 0.20;
          const barWidth = Math.min(100, (feat.psi / 0.5) * 100);

          return (
            <div
              key={feat.feature}
              style={{
                background: "rgba(0,0,0,0.25)",
                padding: "10px 14px",
                borderRadius: "8px",
                border: "1px solid var(--border-subtle)"
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <code style={{ fontSize: "12px", color: "var(--accent-cyan)", background: "rgba(6,182,212,0.1)", padding: "1px 6px", borderRadius: "4px" }}>
                    {feat.feature}
                  </code>
                  <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                    Mean: {feat.baseMean} → <strong style={{ color: "var(--text-primary)" }}>{feat.currMean}</strong>
                  </span>
                </div>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <span style={{
                    fontSize: "12px",
                    fontWeight: "700",
                    color: isFeatCritical ? "var(--accent-rose)" : "var(--accent-emerald)"
                  }}>
                    PSI: {feat.psi.toFixed(3)}
                  </span>
                  <span style={{
                    fontSize: "10px",
                    padding: "2px 6px",
                    borderRadius: "4px",
                    fontWeight: "600",
                    background: isFeatCritical ? "rgba(244, 63, 94, 0.2)" : "rgba(16, 185, 129, 0.2)",
                    color: isFeatCritical ? "#fda4af" : "#6ee7b7"
                  }}>
                    {feat.status}
                  </span>
                </div>
              </div>

              {/* Progress bar with 0.10 and 0.20 markers */}
              <div style={{ position: "relative", height: "6px", width: "100%", background: "rgba(255,255,255,0.06)", borderRadius: "3px", overflow: "hidden" }}>
                <div
                  style={{
                    height: "100%",
                    width: `${barWidth}%`,
                    background: isFeatCritical
                      ? "linear-gradient(90deg, #f59e0b, #f43f5e)"
                      : "linear-gradient(90deg, #10b981, #06b6d4)",
                    borderRadius: "3px",
                    transition: "width 0.5s ease"
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

    </div>
  );
};
