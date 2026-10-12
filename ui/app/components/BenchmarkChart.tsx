"use client";

import React from "react";
import { Sparkles, DollarSign, Clock, CheckCircle2 } from "lucide-react";

export const BenchmarkChart: React.FC = () => {
  const benchmarkRows = [
    {
      provider: "Gemini (Vertex AI Agent)",
      accuracy: 71.9,
      citationRate: 34.4,
      latencyP50: 42.0,
      latencyP95: 68.2,
      costPer1k: "$0.140",
      highlight: true
    },
    {
      provider: "OpenAI (GPT-4o-mini)",
      accuracy: 94.0,
      citationRate: 32.7,
      latencyP50: 317.4,
      latencyP95: 385.1,
      costPer1k: "$0.240",
      highlight: false
    },
    {
      provider: "Deterministic Fallback",
      accuracy: 100.0,
      citationRate: 100.0,
      latencyP50: 0.4,
      latencyP95: 0.8,
      costPer1k: "$0.000",
      highlight: false
    }
  ];

  const categories = [
    { name: "Price Elasticity Shocks", cases: 8, desc: "+45% inflation, discount flash sales" },
    { name: "Promotional Surges", cases: 8, desc: "Loyalty BOGO promos, national SuperBowl ads" },
    { name: "Concept & Supply Disruptions", cases: 8, desc: "Supplier outages, SKU cannibalization" },
    { name: "Regional Store Events", cases: 8, desc: "Blizzard closures, stadium game day spikes" },
  ];

  return (
    <div className="glass-panel" style={{ padding: "20px" }}>
      
      {/* Title */}
      <div style={{ marginBottom: "16px" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Sparkles size={18} color="var(--accent-violet)" />
          <h2 style={{ fontSize: "16px", fontWeight: "700" }}>GenAI Explainer: 32-Case Golden Benchmark</h2>
        </div>
        <p style={{ fontSize: "12px", color: "var(--text-secondary)", marginTop: "2px" }}>
          Ground-truth evaluation comparing Gemini vs. OpenAI across 32 real-world retail demand disruptions.
        </p>
      </div>

      {/* Comparison Cards */}
      <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(240px, 1fr))", gap: "14px", marginBottom: "20px" }}>
        
        {benchmarkRows.map((b) => (
          <div
            key={b.provider}
            style={{
              background: b.highlight ? "rgba(139, 92, 246, 0.08)" : "rgba(0, 0, 0, 0.3)",
              border: b.highlight ? "1px solid rgba(139, 92, 246, 0.4)" : "1px solid var(--border-subtle)",
              borderRadius: "10px",
              padding: "16px"
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "8px" }}>
              <strong style={{ fontSize: "14px", color: b.highlight ? "var(--accent-violet)" : "var(--text-primary)" }}>
                {b.provider}
              </strong>
              {b.highlight && (
                <span style={{ fontSize: "10px", background: "rgba(139, 92, 246, 0.2)", color: "#c4b5fd", padding: "1px 6px", borderRadius: "4px", fontWeight: "700" }}>
                  RECOMMENDED
                </span>
              )}
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: "10px", marginTop: "12px" }}>
              <div>
                <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>ACCURACY</div>
                <div style={{ fontSize: "16px", fontWeight: "800", color: "var(--accent-emerald)" }}>{b.accuracy}%</div>
              </div>
              <div>
                <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>CITATION RATE</div>
                <div style={{ fontSize: "16px", fontWeight: "800", color: "var(--accent-cyan)" }}>{b.citationRate}%</div>
              </div>
              <div>
                <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>p50 LATENCY</div>
                <div style={{ fontSize: "16px", fontWeight: "800", color: "#f8fafc" }}>{b.latencyP50} ms</div>
              </div>
              <div>
                <div style={{ fontSize: "10px", color: "var(--text-muted)" }}>COST / 1K REPORTS</div>
                <div style={{ fontSize: "16px", fontWeight: "800", color: "var(--accent-amber)" }}>{b.costPer1k}</div>
              </div>
            </div>
          </div>
        ))}

      </div>

      {/* 32 Golden Case Categorization */}
      <div>
        <div style={{ fontSize: "13px", fontWeight: "600", marginBottom: "8px", color: "var(--text-secondary)" }}>
          Evaluated Incident Categories (Total: 32 Curated Golden Cases):
        </div>
        <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(200px, 1fr))", gap: "10px" }}>
          {categories.map((c) => (
            <div key={c.name} style={{ background: "rgba(0,0,0,0.2)", padding: "10px 12px", borderRadius: "8px", border: "1px solid var(--border-subtle)" }}>
              <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
                <span style={{ fontSize: "12px", fontWeight: "600" }}>{c.name}</span>
                <span style={{ fontSize: "11px", color: "var(--accent-cyan)", fontWeight: "700" }}>{c.cases} cases</span>
              </div>
              <p style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>{c.desc}</p>
            </div>
          ))}
        </div>
      </div>

    </div>
  );
};
