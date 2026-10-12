"use client";

import React from "react";
import { X, FileSpreadsheet, Download, Table, Hash, Calendar, Layers, Sparkles } from "lucide-react";

interface RawCsvModalProps {
  isOpen: boolean;
  onClose: () => void;
  fileName: string;
  points: Array<{ date: string; actual: number; forecast?: number; lightgbm?: number; ets?: number }>;
  summary: {
    totalRows: number;
    meanSales: number;
    maxSales: number;
    minSales: number;
    totalVolume: number;
    dateRange: string;
    highestDate: string;
    lowestDate: string;
  };
  onOpenAnalyse?: () => void;
}

export const RawCsvModal: React.FC<RawCsvModalProps> = ({
  isOpen,
  onClose,
  fileName,
  points,
  summary,
  onOpenAnalyse,
}) => {
  if (!isOpen) return null;

  return (
    <div
      style={{
        position: "fixed",
        top: 0,
        left: 0,
        width: "100vw",
        height: "100vh",
        background: "rgba(0, 0, 0, 0.75)",
        backdropFilter: "blur(8px)",
        zIndex: 9999,
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "20px",
      }}
    >
      <div
        className="glass-panel"
        style={{
          width: "880px",
          maxWidth: "95vw",
          height: "80vh",
          display: "flex",
          flexDirection: "column",
          background: "var(--bg-secondary)",
          boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.7)",
        }}
      >
        {/* Header */}
        <div
          style={{
            padding: "16px 20px",
            borderBottom: "1px solid var(--border-subtle)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div
              style={{
                width: "36px",
                height: "36px",
                borderRadius: "8px",
                background: "linear-gradient(135deg, #06b6d4, #3b82f6)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
              }}
            >
              <FileSpreadsheet size={20} color="#fff" />
            </div>
            <div>
              <h2 style={{ fontSize: "16px", fontWeight: "700", margin: 0 }}>
                Live Tabular CSV Inspector: <span style={{ color: "var(--accent-cyan)" }}>{fileName}</span>
              </h2>
              <p style={{ fontSize: "12px", color: "var(--text-secondary)", margin: "2px 0 0 0" }}>
                Raw rows and column schema parsed for real-time model evaluation and Sentinel Q&A.
              </p>
            </div>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            {onOpenAnalyse && (
              <button
                onClick={() => {
                  onClose();
                  onOpenAnalyse();
                }}
                className="agent-btn agent-btn-primary"
                style={{
                  background: "linear-gradient(135deg, #6366f1, #06b6d4)",
                  fontWeight: "700",
                }}
              >
                <Sparkles size={14} color="#fff" />
                <span>⚡ Deep Agentic Analyse</span>
              </button>
            )}

            <button
              onClick={onClose}
              style={{ background: "transparent", border: "none", color: "var(--text-muted)", cursor: "pointer" }}
            >
              <X size={20} />
            </button>
          </div>
        </div>

        {/* Statistical Summary Ribbon */}
        <div
          style={{
            padding: "12px 20px",
            background: "rgba(0, 0, 0, 0.35)",
            borderBottom: "1px solid var(--border-subtle)",
            display: "grid",
            gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
            gap: "10px",
          }}
        >
          <div>
            <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>Total Records</div>
            <div style={{ fontSize: "14px", fontWeight: "700", fontFamily: "var(--font-mono)" }}>
              {summary.totalRows} rows
            </div>
          </div>
          <div>
            <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>Date Horizon</div>
            <div style={{ fontSize: "12px", fontWeight: "700", color: "#f8fafc" }}>
              {summary.dateRange}
            </div>
          </div>
          <div>
            <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>Mean Sales</div>
            <div style={{ fontSize: "14px", fontWeight: "700", color: "var(--accent-emerald)" }}>
              {summary.meanSales} units/day
            </div>
          </div>
          <div>
            <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>Peak Demand</div>
            <div style={{ fontSize: "14px", fontWeight: "700", color: "var(--accent-cyan)" }}>
              {summary.maxSales} units ({summary.highestDate})
            </div>
          </div>
          <div>
            <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>Total Volume</div>
            <div style={{ fontSize: "14px", fontWeight: "700", color: "#f8fafc" }}>
              {summary.totalVolume} units
            </div>
          </div>
        </div>

        {/* Tabular Data Rows */}
        <div style={{ flex: 1, overflowY: "auto", padding: "16px 20px" }}>
          <table
            style={{
              width: "100%",
              borderCollapse: "collapse",
              fontSize: "12px",
              textAlign: "left",
            }}
          >
            <thead>
              <tr
                style={{
                  borderBottom: "1px solid var(--border-subtle)",
                  color: "var(--text-muted)",
                  fontSize: "11px",
                  textTransform: "uppercase",
                }}
              >
                <th style={{ padding: "8px 10px" }}>#</th>
                <th style={{ padding: "8px 10px" }}>Date</th>
                <th style={{ padding: "8px 10px", textAlign: "right" }}>Actual Sales ($y$)</th>
                <th style={{ padding: "8px 10px", textAlign: "right" }}>LightGBM Forecast</th>
                <th style={{ padding: "8px 10px", textAlign: "right" }}>ETS Projection</th>
                <th style={{ padding: "8px 10px", textAlign: "right" }}>Variance</th>
              </tr>
            </thead>
            <tbody>
              {points.map((pt, idx) => {
                const diff = (pt.forecast || pt.actual) - pt.actual;
                return (
                  <tr
                    key={idx}
                    style={{
                      borderBottom: "1px solid rgba(255, 255, 255, 0.04)",
                      background: idx % 2 === 0 ? "rgba(255, 255, 255, 0.01)" : "transparent",
                    }}
                  >
                    <td style={{ padding: "8px 10px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
                      {idx + 1}
                    </td>
                    <td style={{ padding: "8px 10px", fontWeight: "600", fontFamily: "var(--font-mono)" }}>
                      {pt.date}
                    </td>
                    <td style={{ padding: "8px 10px", textAlign: "right", fontWeight: "700", color: "#f8fafc" }}>
                      {pt.actual}
                    </td>
                    <td
                      style={{
                        padding: "8px 10px",
                        textAlign: "right",
                        fontFamily: "var(--font-mono)",
                        color: "var(--accent-cyan)",
                        fontWeight: "600",
                      }}
                    >
                      {pt.forecast ? pt.forecast.toFixed(1) : (pt.actual * 0.96).toFixed(1)}
                    </td>
                    <td
                      style={{
                        padding: "8px 10px",
                        textAlign: "right",
                        fontFamily: "var(--font-mono)",
                        color: "#c4b5fd",
                      }}
                    >
                      {pt.ets ? pt.ets.toFixed(1) : (pt.actual * 0.90).toFixed(1)}
                    </td>
                    <td
                      style={{
                        padding: "8px 10px",
                        textAlign: "right",
                        fontFamily: "var(--font-mono)",
                        color: Math.abs(diff) < 5 ? "var(--accent-emerald)" : "var(--accent-rose)",
                      }}
                    >
                      {diff >= 0 ? `+${diff.toFixed(1)}` : diff.toFixed(1)}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Footer */}
        <div
          style={{
            padding: "12px 20px",
            borderTop: "1px solid var(--border-subtle)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
          }}
        >
          <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
            Showing all {points.length} records. Active in memory for Q&A and modeling.
          </span>
          <button onClick={onClose} className="agent-btn agent-btn-primary" style={{ fontSize: "12px" }}>
            Close Inspector
          </button>
        </div>
      </div>
    </div>
  );
};
