"use client";

import React from "react";
import { ShieldCheck, RotateCcw, GitBranch, ArrowDownRight, Award } from "lucide-react";

interface ModelsChartProps {
  activeVersion: string;
  previousVersion: string;
  onRollback: () => void;
  onRetrain: () => void;
}

export const ModelsChart: React.FC<ModelsChartProps> = ({
  activeVersion,
  previousVersion,
  onRollback,
  onRetrain
}) => {
  const modelsData = [
    { name: "Naive (t-1)", wape: 42.03, bias: -0.55, type: "Baseline", color: "#64748b" },
    { name: "Seasonal Naive (t-7)", wape: 40.29, bias: +2.05, type: "Baseline", color: "#f59e0b" },
    { name: "ETS Holt-Winters", wape: 38.50, bias: -1.80, type: "Comparator", color: "#8b5cf6" },
    { name: "LightGBM (Champion)", wape: 13.25, bias: -1.20, type: "Champion", color: "#10b981", active: activeVersion === "v1" },
    { name: "Shadow Retrained", wape: 13.37, bias: -0.40, type: "Candidate", color: "#06b6d4", active: activeVersion !== "v1" },
  ];

  return (
    <div className="glass-panel" style={{ padding: "20px" }}>
      
      {/* Title */}
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "16px", flexWrap: "wrap", gap: "10px" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <h2 style={{ fontSize: "16px", fontWeight: "700" }}>Model Registry & Baseline Comparison</h2>
            <span style={{
              fontSize: "11px",
              padding: "2px 8px",
              borderRadius: "10px",
              background: "rgba(16, 185, 129, 0.15)",
              color: "var(--accent-emerald)",
              fontWeight: "600",
              border: "1px solid rgba(16, 185, 129, 0.3)"
            }}>
              WAPE Beats Baseline by 68.5%
            </span>
          </div>
          <p style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "2px" }}>
            WAPE and normalized bias across persistence baselines, classical ETS, and gradient boosted trees.
          </p>
        </div>

        <div style={{ display: "flex", gap: "8px" }}>
          <button onClick={onRollback} className="agent-btn agent-btn-danger" style={{ fontSize: "12px" }}>
            <RotateCcw size={13} />
            <span>Rollback Champion</span>
          </button>
          <button onClick={onRetrain} className="agent-btn agent-btn-primary" style={{ fontSize: "12px" }}>
            <GitBranch size={13} />
            <span>Trigger Retrain</span>
          </button>
        </div>
      </div>

      {/* Model Performance Comparison Bars */}
      <div style={{ display: "flex", flexDirection: "column", gap: "12px", marginBottom: "24px" }}>
        {modelsData.map((m) => {
          const barWidth = (m.wape / 50) * 100;
          return (
            <div
              key={m.name}
              style={{
                background: m.active ? "rgba(6, 182, 212, 0.08)" : "rgba(0, 0, 0, 0.25)",
                border: m.active ? "1px solid rgba(6, 182, 212, 0.35)" : "1px solid var(--border-subtle)",
                borderRadius: "8px",
                padding: "12px 16px"
              }}
            >
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "6px" }}>
                <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                  <strong style={{ fontSize: "13px", color: m.active ? "var(--accent-cyan)" : "var(--text-primary)" }}>
                    {m.name}
                  </strong>
                  {m.active && (
                    <span style={{
                      fontSize: "10px",
                      padding: "1px 6px",
                      borderRadius: "4px",
                      background: "rgba(6, 182, 212, 0.2)",
                      color: "var(--accent-cyan)",
                      fontWeight: "700"
                    }}>
                      ACTIVE CHAMPION
                    </span>
                  )}
                </div>

                <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
                  <span style={{ fontSize: "12px", color: "var(--text-muted)" }}>
                    Bias: <strong style={{ color: "var(--text-primary)" }}>{m.bias > 0 ? `+${m.bias}` : m.bias}%</strong>
                  </span>
                  <span style={{ fontSize: "14px", fontWeight: "800", color: m.color }}>
                    {m.wape.toFixed(2)}% WAPE
                  </span>
                </div>
              </div>

              {/* Progress bar */}
              <div style={{ height: "6px", width: "100%", background: "rgba(255,255,255,0.06)", borderRadius: "3px", overflow: "hidden" }}>
                <div
                  style={{
                    height: "100%",
                    width: `${barWidth}%`,
                    background: m.color,
                    borderRadius: "3px",
                    transition: "width 0.4s ease"
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>

      {/* Registry Lineage Topology */}
      <div style={{ background: "rgba(0,0,0,0.3)", padding: "16px", borderRadius: "10px", border: "1px solid var(--border-subtle)" }}>
        <div style={{ fontSize: "13px", fontWeight: "600", marginBottom: "12px", display: "flex", alignItems: "center", gap: "6px" }}>
          <GitBranch size={16} color="var(--accent-cyan)" />
          <span>Model Registry Manifest & Lineage:</span>
        </div>

        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "12px" }}>
          
          <div style={{
            padding: "12px",
            borderRadius: "8px",
            background: "rgba(16, 185, 129, 0.08)",
            border: "1px solid rgba(16, 185, 129, 0.3)"
          }}>
            <div style={{ fontSize: "11px", color: "var(--accent-emerald)", fontWeight: "600" }}>ACTIVE CHAMPION</div>
            <div style={{ fontSize: "16px", fontWeight: "800", marginTop: "2px" }}>{activeVersion}</div>
            <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>
              Path: <code style={{ color: "var(--text-secondary)" }}>/models/registry/champion</code>
            </div>
            <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "4px" }}>
              Test WAPE: <strong>{activeVersion === "v1" ? "13.25%" : "13.37%"}</strong>
            </div>
          </div>

          <div style={{
            padding: "12px",
            borderRadius: "8px",
            background: "rgba(255, 255, 255, 0.03)",
            border: "1px solid var(--border-subtle)"
          }}>
            <div style={{ fontSize: "11px", color: "var(--text-muted)", fontWeight: "600" }}>PREVIOUS VERSION (ROLLBACK TARGET)</div>
            <div style={{ fontSize: "16px", fontWeight: "800", marginTop: "2px" }}>{previousVersion}</div>
            <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "4px" }}>
              Status: <span style={{ color: "var(--accent-amber)" }}>Archived / Hot-Reload Ready</span>
            </div>
            <div style={{ fontSize: "11px", color: "var(--text-secondary)", marginTop: "4px" }}>
              Rollback Latency: <strong>&lt; 15 ms</strong>
            </div>
          </div>

        </div>
      </div>

    </div>
  );
};
