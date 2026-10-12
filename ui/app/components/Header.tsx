"use client";

import React, { useRef } from "react";
import { Activity, ShieldCheck, AlertTriangle, BookOpen, Settings, RotateCcw, Zap, FileSpreadsheet, UploadCloud, Sparkles } from "lucide-react";

interface HeaderProps {
  activeModel: { version: string; wape: number; bias: number; status: string };
  isDriftActive: boolean;
  onOpenGuide: () => void;
  onOpenConfig: () => void;
  onRollback: () => void;
  isLiveActive?: boolean;
  onToggleLive?: () => void;
  uploadedFileName?: string | null;
  onViewRawCsv?: () => void;
  onUploadCsv?: (file: File) => void;
  onOpenAnalyse?: () => void;
}

export const Header: React.FC<HeaderProps> = ({
  activeModel,
  isDriftActive,
  onOpenGuide,
  onOpenConfig,
  onRollback,
  isLiveActive = false,
  onToggleLive,
  uploadedFileName,
  onViewRawCsv,
  onUploadCsv,
  onOpenAnalyse,
}) => {
  const fileInputRef = useRef<HTMLInputElement>(null);
  return (
    <header className="glass-panel" style={{ padding: "8px 16px", marginBottom: "10px", width: "100%", boxSizing: "border-box", flexShrink: 0 }}>
      <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", flexWrap: "wrap", gap: "10px" }}>
        
        {/* Title & Brand */}
        <div style={{ display: "flex", alignItems: "center", gap: "10px", minWidth: 0 }}>
          <div style={{
            width: "36px",
            height: "36px",
            borderRadius: "8px",
            background: "linear-gradient(135deg, #06b6d4, #3b82f6)",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            boxShadow: "0 0 16px rgba(6, 182, 212, 0.3)",
            flexShrink: 0
          }}>
            <Activity size={18} color="#fff" />
          </div>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <h1 style={{ fontSize: "16px", fontWeight: "700", letterSpacing: "-0.02em", margin: 0, whiteSpace: "nowrap" }}>
                Forecast-to-Insight <span style={{ color: "var(--accent-cyan)" }}>Agentic ML</span>
              </h1>
              <span style={{
                fontSize: "10px",
                padding: "1px 6px",
                borderRadius: "10px",
                fontWeight: "600",
                background: "rgba(6, 182, 212, 0.15)",
                color: "var(--accent-cyan)",
                border: "1px solid rgba(6, 182, 212, 0.3)",
                whiteSpace: "nowrap"
              }}>
                v1.0 HA
              </span>
            </div>
            <p style={{ fontSize: "11px", color: "var(--text-secondary)", margin: "1px 0 0 0", whiteSpace: "nowrap" }}>
              Autonomous MLOps • Multi-Series Demand • Real-Time Drift Mitigation
            </p>
          </div>
        </div>

        {/* Status Indicators & Control Actions */}
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flexWrap: "wrap" }}>
          
          {/* Agent Status Badge */}
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            padding: "5px 10px",
            borderRadius: "16px",
            background: isDriftActive ? "rgba(244, 63, 94, 0.12)" : "rgba(16, 185, 129, 0.12)",
            border: isDriftActive ? "1px solid rgba(244, 63, 94, 0.3)" : "1px solid rgba(16, 185, 129, 0.3)",
            fontSize: "11px",
            fontWeight: "600",
            color: isDriftActive ? "var(--accent-rose)" : "var(--accent-emerald)",
            whiteSpace: "nowrap"
          }}>
            <div
              className="pulsing-dot"
              style={{ width: "6px", height: "6px", background: isDriftActive ? "var(--accent-rose)" : "var(--accent-emerald)" }}
            />
            <span>{isDriftActive ? "DRIFT ALERT" : "SENTINEL ACTIVE"}</span>
          </div>

          {/* Champion Model Badge */}
          <div style={{
            display: "flex",
            alignItems: "center",
            gap: "6px",
            padding: "5px 10px",
            borderRadius: "6px",
            background: "rgba(255, 255, 255, 0.04)",
            border: "1px solid var(--border-subtle)",
            fontSize: "11px",
            whiteSpace: "nowrap"
          }}>
            <ShieldCheck size={14} color="var(--accent-cyan)" />
            <div>
              <span style={{ color: "var(--text-muted)" }}>Champion: </span>
              <strong style={{ color: "var(--text-primary)" }}>{activeModel.version}</strong>
              <span style={{ color: "var(--text-muted)", marginLeft: "6px" }}>WAPE: </span>
              <strong style={{ color: "var(--accent-emerald)" }}>{(activeModel.wape * 100).toFixed(2)}%</strong>
            </div>
          </div>

          {/* Live CSV / Production Data Mode Switcher */}
          {onToggleLive && (
            <button
              onClick={onToggleLive}
              className="agent-btn"
              style={{
                fontSize: "11px",
                padding: "5px 10px",
                background: isLiveActive
                  ? "linear-gradient(135deg, rgba(6, 182, 212, 0.25), rgba(16, 185, 129, 0.2))"
                  : "rgba(255, 255, 255, 0.04)",
                border: isLiveActive
                  ? "1px solid var(--accent-cyan)"
                  : "1px solid var(--border-subtle)",
                color: isLiveActive ? "var(--accent-cyan)" : "var(--text-muted)",
                fontWeight: "700",
                boxShadow: isLiveActive ? "0 0 12px rgba(6, 182, 212, 0.25)" : "none",
                whiteSpace: "nowrap"
              }}
              title="Click to toggle between Live Uploaded CSV Data and Production Default Baseline"
            >
              <span
                style={{
                  width: "6px",
                  height: "6px",
                  borderRadius: "50%",
                  background: isLiveActive ? "var(--accent-emerald)" : "#64748b",
                  boxShadow: isLiveActive ? "0 0 6px var(--accent-emerald)" : "none",
                }}
              />
              <span>{isLiveActive ? `⚡ LIVE: ${uploadedFileName || "Custom CSV"}` : "📊 Default Data"}</span>
            </button>
          )}

          {/* Raw CSV Data Inspector Button (if CSV is available) */}
          {uploadedFileName && onViewRawCsv && (
            <button
              onClick={onViewRawCsv}
              className="agent-btn"
              style={{ fontSize: "11px", padding: "5px 10px" }}
              title="Inspect raw CSV rows and schema table"
            >
              <FileSpreadsheet size={13} color="var(--accent-cyan)" />
              <span>Raw CSV</span>
            </button>
          )}

          {/* Deep Agentic Analyse Button */}
          {uploadedFileName && onOpenAnalyse && (
            <button
              onClick={onOpenAnalyse}
              className="agent-btn agent-btn-primary"
              style={{
                fontSize: "11px",
                padding: "5px 10px",
                background: "linear-gradient(135deg, #6366f1, #06b6d4)",
                boxShadow: "0 0 12px rgba(99, 102, 241, 0.4)",
                fontWeight: "700",
              }}
              title="Run Deep Agentic Loop Analysis, Tradeoff Consent & Champion/Challenger ML"
            >
              <Sparkles size={13} color="#fff" />
              <span>⚡ Analyse</span>
            </button>
          )}

          {/* Upload New CSV Button */}
          {onUploadCsv && (
            <>
              <input
                type="file"
                ref={fileInputRef}
                accept=".csv"
                style={{ display: "none" }}
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) {
                    onUploadCsv(file);
                    e.target.value = "";
                  }
                }}
              />
              <button
                onClick={() => fileInputRef.current?.click()}
                className="agent-btn"
                style={{ fontSize: "11px", padding: "5px 10px" }}
                title="Upload custom demand CSV dataset"
              >
                <UploadCloud size={13} color="var(--accent-emerald)" />
                <span>Upload CSV</span>
              </button>
            </>
          )}

          {/* Quick Action Buttons */}
          <button
            onClick={onRollback}
            className="agent-btn agent-btn-danger"
            style={{ fontSize: "11px", padding: "5px 10px" }}
            title="Perform Instant Rollback"
          >
            <RotateCcw size={13} />
            <span>Rollback</span>
          </button>

          <button
            onClick={onOpenGuide}
            className="agent-btn"
            style={{ fontSize: "11px", padding: "5px 10px" }}
            title="Open 12-Week Playbook & User Guide"
          >
            <BookOpen size={13} />
            <span>Guide</span>
          </button>

          <button
            onClick={onOpenConfig}
            className="agent-btn"
            style={{ fontSize: "11px", padding: "5px 10px" }}
            title="Agent System Configuration"
          >
            <Settings size={13} />
            <span>Config</span>
          </button>

        </div>

      </div>
    </header>
  );
};
