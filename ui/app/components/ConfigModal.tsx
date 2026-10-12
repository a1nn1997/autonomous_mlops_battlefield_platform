"use client";

import React, { useState } from "react";
import { X, Settings, Sliders, Shield, Zap, Check } from "lucide-react";

export interface AgentConfig {
  psiWarning: number;
  psiCritical: number;
  wapeDecayThreshold: number;
  retrainWindowDays: number;
  servingTimeout: number;
  llmProvider: string;
}

interface ConfigModalProps {
  isOpen: boolean;
  onClose: () => void;
  config: AgentConfig;
  onSaveConfig: (newConfig: AgentConfig) => void;
}

export const ConfigModal: React.FC<ConfigModalProps> = ({
  isOpen,
  onClose,
  config,
  onSaveConfig
}) => {
  const [form, setForm] = useState<AgentConfig>(config);
  const [saved, setSaved] = useState(false);

  if (!isOpen) return null;

  const handleSave = () => {
    onSaveConfig(form);
    setSaved(true);
    setTimeout(() => {
      setSaved(false);
      onClose();
    }, 600);
  };

  return (
    <div style={{
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
      padding: "20px"
    }}>
      <div className="glass-panel" style={{
        width: "560px",
        maxWidth: "95vw",
        background: "var(--bg-secondary)",
        boxShadow: "0 25px 50px -12px rgba(0, 0, 0, 0.7)",
        padding: "24px",
        display: "flex",
        flexDirection: "column",
        gap: "20px"
      }}>
        
        {/* Header */}
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
            <div style={{
              width: "32px",
              height: "32px",
              borderRadius: "8px",
              background: "linear-gradient(135deg, #06b6d4, #10b981)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center"
            }}>
              <Sliders size={18} color="#fff" />
            </div>
            <div>
              <h2 style={{ fontSize: "16px", fontWeight: "700" }}>Agent & MLOps Configuration</h2>
              <p style={{ fontSize: "12px", color: "var(--text-secondary)" }}>Tune statistical drift sensitivity, timeouts, and LLM providers</p>
            </div>
          </div>

          <button onClick={onClose} style={{ background: "transparent", color: "var(--text-muted)", cursor: "pointer" }}>
            <X size={20} />
          </button>
        </div>

        {/* Inputs */}
        <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
          
          {/* PSI Critical Threshold */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "6px" }}>
              <span style={{ fontWeight: "600" }}>PSI Critical Alert Threshold</span>
              <span style={{ color: "var(--accent-rose)", fontWeight: "700" }}>{form.psiCritical.toFixed(2)}</span>
            </div>
            <input
              type="range"
              min="0.10"
              max="0.40"
              step="0.01"
              value={form.psiCritical}
              onChange={(e) => setForm({ ...form, psiCritical: parseFloat(e.target.value) })}
              style={{ width: "100%", accentColor: "var(--accent-rose)", cursor: "pointer" }}
            />
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Threshold where automated shadow retraining is triggered</span>
          </div>

          {/* WAPE Decay Threshold */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "6px" }}>
              <span style={{ fontWeight: "600" }}>WAPE Decay Trigger (%)</span>
              <span style={{ color: "var(--accent-amber)", fontWeight: "700" }}>{(form.wapeDecayThreshold * 100).toFixed(0)}%</span>
            </div>
            <input
              type="range"
              min="0.05"
              max="0.30"
              step="0.01"
              value={form.wapeDecayThreshold}
              onChange={(e) => setForm({ ...form, wapeDecayThreshold: parseFloat(e.target.value) })}
              style={{ width: "100%", accentColor: "var(--accent-amber)", cursor: "pointer" }}
            />
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Relative error degradation triggering model incident alert</span>
          </div>

          {/* Serving Timeout */}
          <div>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: "12px", marginBottom: "6px" }}>
              <span style={{ fontWeight: "600" }}>Serving Circuit Breaker Timeout (seconds)</span>
              <span style={{ color: "var(--accent-cyan)", fontWeight: "700" }}>{form.servingTimeout.toFixed(1)} s</span>
            </div>
            <input
              type="range"
              min="0.5"
              max="5.0"
              step="0.1"
              value={form.servingTimeout}
              onChange={(e) => setForm({ ...form, servingTimeout: parseFloat(e.target.value) })}
              style={{ width: "100%", accentColor: "var(--accent-cyan)", cursor: "pointer" }}
            />
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>Max latency before returning HTTP 504 Gateway Timeout</span>
          </div>

          {/* LLM Provider Selection */}
          <div>
            <label style={{ fontSize: "12px", fontWeight: "600", display: "block", marginBottom: "6px" }}>
              GenAI Incident Explainer Provider
            </label>
            <select
              value={form.llmProvider}
              onChange={(e) => setForm({ ...form, llmProvider: e.target.value })}
              style={{
                width: "100%",
                background: "rgba(0,0,0,0.4)",
                border: "1px solid var(--border-subtle)",
                borderRadius: "8px",
                padding: "10px",
                color: "var(--text-primary)",
                fontSize: "13px",
                outline: "none"
              }}
            >
              <option value="gemini-flash">Google Gemini (Gemini 3.8 Flash-Lite - Default Optimized)</option>
              <option value="openai-luna">OpenAI (GPT-6 Luna - Ultra-Fast Agentic Inference)</option>
              <option value="claude-haiku">Anthropic Claude (Claude Haiku 5.5 - High-Speed Multi-Turn)</option>
              <option value="fallback">Deterministic Rule-Based Fallback (Zero Latency & 100% SLA)</option>
            </select>
          </div>

        </div>

        {/* Footer */}
        <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", borderTop: "1px solid var(--border-subtle)", paddingTop: "16px" }}>
          <button onClick={onClose} className="agent-btn" style={{ padding: "8px 16px" }}>
            Cancel
          </button>
          <button onClick={handleSave} className="agent-btn agent-btn-primary" style={{ padding: "8px 20px" }}>
            {saved ? <Check size={14} /> : null}
            <span>{saved ? "Saved!" : "Save Changes"}</span>
          </button>
        </div>

      </div>
    </div>
  );
};
