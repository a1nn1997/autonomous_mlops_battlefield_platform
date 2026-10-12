"use client";

import React, { useState, useEffect, useRef } from "react";
import {
  Swords,
  Upload,
  FileSpreadsheet,
  CheckCircle2,
  TrendingDown,
  Trophy,
  Activity,
  Zap,
  Gauge,
  Layers,
  Sparkles,
  RefreshCw,
  AlertTriangle,
  Download,
  Info,
  Sliders,
  Settings,
  Trash2,
  FolderPlus,
  Play,
  Check,
  ChevronDown,
  ChevronUp,
  Cpu,
  BarChart3,
  Flame
} from "lucide-react";
import {
  ModelBattleResult,
  BattleTimeSeriesPoint,
  ModelConfigs,
  BulkDatasetItem,
} from "../api/battle/route";

interface ModelBattleArenaProps {
  onPromoteModel?: (modelId: string, modelName: string, wape: number) => void;
  onAskAgent?: (prompt: string) => void;
  onDatasetLoaded?: (dataset: {
    fileName: string;
    points: any[];
    summary: any;
    championModel: string;
    championWape: number;
  }) => void;
}

interface StagedDataset {
  id: string;
  name: string;
  sizeKb?: number;
  csvContent?: string;
  isPreloaded?: boolean;
}

export const ModelBattleArena: React.FC<ModelBattleArenaProps> = ({
  onPromoteModel,
  onAskAgent,
  onDatasetLoaded,
}) => {
  // Staged datasets for bulk upload
  const [stagedDatasets, setStagedDatasets] = useState<StagedDataset[]>([
    { id: "m5_sample", name: "M5 Retail Demand (Multi-Category Hierarchy)", isPreloaded: true },
    { id: "grocery_promo", name: "Fast-Moving Grocery (+45% Promo Surge)", isPreloaded: true },
  ]);
  const [activeDatasetId, setActiveDatasetId] = useState<string>("m5_sample");

  // Selected models
  const [selectedModels, setSelectedModels] = useState<string[]>([
    "lightgbm",
    "ets",
    "s_naive",
    "naive",
    "moving_avg",
  ]);

  // Model Hyperparameters configuration
  const [showConfigDrawer, setShowConfigDrawer] = useState<boolean>(false);
  const [modelConfigs, setModelConfigs] = useState<ModelConfigs>({
    lightgbm: {
      objective: "l1",
      learningRate: 0.05,
      numLeaves: 31,
      useLags: true,
    },
    ets: {
      seasonalPeriod: 7,
      trendType: "additive",
      seasonalType: "additive",
      damped: false,
    },
    s_naive: {
      cycleLag: 7,
    },
    moving_avg: {
      windowSize: 7,
    },
    primaryMetric: "wape",
  });

  // Battle execution state
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [battleLogs, setBattleLogs] = useState<string[]>([
    "[SYSTEM] Model Battle Arena initialized with Datadog Telemetry Mesh.",
    "[READY] 2 Datasets staged. 5 Combatant architectures ready.",
  ]);
  const [battleData, setBattleData] = useState<{
    datasets: Array<{ id: string; name: string; datasetSummary: any; modelsCount: number; championModel: string; championWape: number }>;
    activeDatasetId: string;
    datasetSummary: any;
    models: ModelBattleResult[];
    champion: ModelBattleResult;
    timeSeries: BattleTimeSeriesPoint[];
    crossDatasetLeaderboard?: any[];
    segmentBreakdown: any[];
    battleTelemetry: any;
  } | null>(null);

  // Active series display toggles
  const [visibleCurves, setVisibleCurves] = useState<Record<string, boolean>>({
    actual: true,
    lightgbm: true,
    ets: true,
    s_naive: true,
    naive: false,
    moving_avg: false,
  });

  const fileInputRef = useRef<HTMLInputElement>(null);

  // Initial load
  useEffect(() => {
    executeBattleTournament();
  }, []);

  const addLog = (msg: string) => {
    const timestamp = new Date().toLocaleTimeString();
    setBattleLogs((prev) => [...prev.slice(-12), `[${timestamp}] ${msg}`]);
  };

  // Launch the actual model battle tournament
  const executeBattleTournament = async (datasetToSelect?: string) => {
    setIsLoading(true);
    addLog(`⚔️ Launching tournament across ${stagedDatasets.length} dataset(s) and ${selectedModels.length} models...`);

    try {
      const payload = {
        datasets: stagedDatasets.map((d) => ({
          id: d.id,
          name: d.name,
          csvContent: d.csvContent,
          datasetType: d.isPreloaded ? d.id : undefined,
        })),
        activeDatasetId: datasetToSelect || activeDatasetId,
        selectedModels,
        modelConfigs,
      };

      const res = await fetch("/api/battle", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });

      if (res.ok) {
        const data = await res.json();
        setBattleData(data);
        if (data.activeDatasetId) {
          setActiveDatasetId(data.activeDatasetId);
        }
        if (onDatasetLoaded && data.datasetSummary) {
          onDatasetLoaded({
            fileName: data.datasetSummary.name || "uploaded_dataset.csv",
            points: data.timeSeries || [],
            summary: {
              totalRows: data.datasetSummary.totalRows || (data.timeSeries?.length || 0),
              meanSales: data.datasetSummary.meanSales || 0,
              maxSales: data.datasetSummary.maxSales || 0,
              minSales: data.datasetSummary.minSales || 0,
              totalVolume: data.datasetSummary.totalVolume || 0,
              dateRange: data.datasetSummary.dateRange || "",
              highestDate: data.datasetSummary.highestDate || "",
              lowestDate: data.datasetSummary.lowestDate || "",
            },
            championModel: data.champion?.name || "LightGBM Regressor (L1 Loss)",
            championWape: data.champion?.wape || 0.05,
          });
        }
        addLog(`✅ Tournament completed! Champion: ${data.champion?.name} (WAPE: ${(data.champion?.wape * 100).toFixed(2)}%)`);
      } else {
        const err = await res.json();
        addLog(`❌ Battle execution failed: ${err.error || "Unknown error"}`);
      }
    } catch (e: any) {
      addLog(`❌ Network error: ${e.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  // Bulk CSV file upload handler
  const handleBulkFileUpload = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    const newStaged: StagedDataset[] = [];
    const readers: Promise<void>[] = [];

    Array.from(files).forEach((file, idx) => {
      const readerPromise = new Promise<void>((resolve) => {
        const reader = new FileReader();
        reader.onload = (event) => {
          const text = event.target?.result as string;
          newStaged.push({
            id: `custom_csv_${Date.now()}_${idx}`,
            name: file.name,
            sizeKb: Math.round(file.size / 1024),
            csvContent: text,
            isPreloaded: false,
          });
          resolve();
        };
        reader.readAsText(file);
      });
      readers.push(readerPromise);
    });

    Promise.all(readers).then(() => {
      setStagedDatasets((prev) => [...prev, ...newStaged]);
      const firstNewId = newStaged[0]?.id;
      if (firstNewId) {
        setActiveDatasetId(firstNewId);
      }
      addLog(`📁 Bulk uploaded ${newStaged.length} dataset(s): ${newStaged.map((f) => f.name).join(", ")}. Click 'Start Battle' to evaluate.`);
    });
  };

  const removeStagedDataset = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    if (stagedDatasets.length <= 1) return;
    const filtered = stagedDatasets.filter((d) => d.id !== id);
    setStagedDatasets(filtered);
    if (activeDatasetId === id) {
      setActiveDatasetId(filtered[0].id);
    }
    addLog(`🗑️ Removed dataset ${id} from tournament queue.`);
  };

  const toggleModel = (modelId: string) => {
    if (selectedModels.includes(modelId)) {
      if (selectedModels.length <= 2) return; // Keep at least 2 models
      setSelectedModels(selectedModels.filter((m) => m !== modelId));
    } else {
      setSelectedModels([...selectedModels, modelId]);
    }
  };

  const toggleCurve = (curveKey: string) => {
    setVisibleCurves((prev) => ({ ...prev, [curveKey]: !prev[curveKey] }));
  };

  const handlePromoteChampion = () => {
    if (battleData?.champion && onPromoteModel) {
      onPromoteModel(
        battleData.champion.id,
        battleData.champion.name,
        battleData.champion.wape
      );
    }
  };

  const handleAnalyzeWithAgent = () => {
    if (!battleData?.champion || !onAskAgent) return;
    const prompt = `Analyze battle tournament results for dataset "${battleData.datasetSummary?.name}": Champion was ${battleData.champion.name} (${(battleData.champion.wape * 100).toFixed(2)}% WAPE, ${battleData.champion.deltaVsNaive}% vs baseline). What architectural reasons explain its win over ETS Holt-Winters and Baselines?`;
    onAskAgent(prompt);
  };

  // SVG Chart Dimensions & Computations
  const points = battleData?.timeSeries || [];
  const svgWidth = 840;
  const svgHeight = 280;
  const padding = { top: 25, right: 35, bottom: 40, left: 50 };

  const allValues: number[] = [];
  points.forEach((p) => {
    allValues.push(p.actual);
    if (p.lightgbm) allValues.push(p.lightgbm);
    if (p.ets) allValues.push(p.ets);
    if (p.s_naive) allValues.push(p.s_naive);
    if (p.naive) allValues.push(p.naive);
    if (p.moving_avg) allValues.push(p.moving_avg);
  });

  const maxVal = allValues.length ? Math.max(...allValues) * 1.15 : 100;
  const minVal = 0;

  const getX = (idx: number) => {
    if (points.length <= 1) return padding.left;
    return (
      padding.left +
      (idx / (points.length - 1)) * (svgWidth - padding.left - padding.right)
    );
  };

  const getY = (val: number) => {
    const clamped = Math.max(minVal, Math.min(maxVal, val));
    return (
      svgHeight -
      padding.bottom -
      ((clamped - minVal) / (maxVal - minVal || 1)) *
        (svgHeight - padding.top - padding.bottom)
    );
  };

  const createLinePath = (getter: (p: BattleTimeSeriesPoint) => number | undefined) => {
    const valid = points
      .map((p, idx) => ({ x: getX(idx), y: getter(p) }))
      .filter((d) => d.y !== undefined);
    if (valid.length === 0) return "";
    return valid
      .map((d, i) => `${i === 0 ? "M" : "L"} ${d.x.toFixed(1)} ${getY(d.y!).toFixed(1)}`)
      .join(" ");
  };

  return (
    <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
      {/* 1. Datadog Live Observability Header */}
      <div
        className="glass-panel"
        style={{
          padding: "16px 20px",
          background: "linear-gradient(135deg, rgba(17, 24, 39, 0.95), rgba(30, 27, 75, 0.6))",
          border: "1px solid rgba(99, 102, 241, 0.3)",
          boxShadow: "0 0 25px rgba(99, 102, 241, 0.15)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <div
              style={{
                width: "40px",
                height: "40px",
                borderRadius: "8px",
                background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                boxShadow: "0 0 15px rgba(99, 102, 241, 0.5)",
              }}
            >
              <Swords size={22} color="#fff" />
            </div>
            <div>
              <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                <h2
                  style={{
                    fontSize: "17px",
                    fontWeight: "800",
                    letterSpacing: "-0.01em",
                    margin: 0,
                  }}
                >
                  Model Battle Arena <span style={{ color: "#a5b4fc" }}>& Benchmark Studio</span>
                </h2>
                <span
                  style={{
                    fontSize: "10px",
                    padding: "2px 8px",
                    borderRadius: "12px",
                    fontWeight: "700",
                    background: "rgba(99, 102, 241, 0.2)",
                    color: "#c7d2fe",
                    border: "1px solid rgba(99, 102, 241, 0.4)",
                  }}
                >
                  DATADOG TELEMETRY MESH
                </span>
              </div>
              <p
                style={{
                  fontSize: "12px",
                  color: "var(--text-muted)",
                  margin: "3px 0 0 0",
                }}
              >
                Bulk upload custom CSV datasets, configure hyperparameters, and launch real-time classical model battles.
              </p>
            </div>
          </div>

          {/* Quick status badges */}
          <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
            <span
              style={{
                fontSize: "11px",
                padding: "4px 10px",
                borderRadius: "6px",
                background: "rgba(16, 185, 129, 0.15)",
                color: "var(--accent-emerald)",
                border: "1px solid rgba(16, 185, 129, 0.3)",
                display: "flex",
                alignItems: "center",
                gap: "5px",
                fontWeight: "600",
              }}
            >
              <span
                style={{
                  width: "6px",
                  height: "6px",
                  borderRadius: "50%",
                  background: "var(--accent-emerald)",
                  boxShadow: "0 0 8px var(--accent-emerald)",
                }}
              />
              EVAL ENGINE READY
            </span>
            <span
              style={{
                fontSize: "11px",
                padding: "4px 10px",
                borderRadius: "6px",
                background: "rgba(99, 102, 241, 0.15)",
                color: "#c7d2fe",
                border: "1px solid rgba(99, 102, 241, 0.3)",
                fontWeight: "600",
              }}
            >
              📁 {stagedDatasets.length} Datasets
            </span>
            <span
              style={{
                fontSize: "11px",
                padding: "4px 10px",
                borderRadius: "6px",
                background: "rgba(6, 182, 212, 0.15)",
                color: "#67e8f9",
                border: "1px solid rgba(6, 182, 212, 0.3)",
                fontWeight: "600",
              }}
            >
              🤖 {selectedModels.length} Models
            </span>
          </div>
        </div>
      </div>

      {/* 2. Bulk Dataset Upload & Staging Drawer */}
      <div
        className="glass-panel"
        style={{
          padding: "16px 20px",
          display: "flex",
          flexDirection: "column",
          gap: "12px",
          background: "rgba(15, 23, 42, 0.75)",
          border: "1px solid rgba(255, 255, 255, 0.08)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "10px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <FileSpreadsheet size={16} color="var(--accent-cyan)" />
            <span style={{ fontSize: "13px", fontWeight: "700" }}>
              Staged Datasets & Bulk CSV Ingestion ({stagedDatasets.length}):
            </span>
          </div>

          <div style={{ display: "flex", gap: "8px" }}>
            <input
              type="file"
              ref={fileInputRef}
              onChange={handleBulkFileUpload}
              accept=".csv"
              multiple
              style={{ display: "none" }}
            />
            <button
              onClick={() => fileInputRef.current?.click()}
              className="agent-btn"
              style={{
                fontSize: "11px",
                padding: "5px 12px",
                background: "rgba(6, 182, 212, 0.2)",
                color: "#67e8f9",
                border: "1px solid rgba(6, 182, 212, 0.4)",
              }}
            >
              <Upload size={13} />
              <span>Bulk Upload CSVs</span>
            </button>

            <button
              onClick={() => {
                setStagedDatasets([
                  { id: "m5_sample", name: "M5 Retail Demand (Hierarchy)", isPreloaded: true },
                  { id: "grocery_promo", name: "Fast-Moving Grocery (+45% Promo)", isPreloaded: true },
                  { id: "electronics_shock", name: "Consumer Electronics (Inflation Drift)", isPreloaded: true },
                ]);
                addLog("📋 Loaded 3 standard benchmark workloads into queue.");
              }}
              className="agent-btn"
              style={{ fontSize: "11px", padding: "5px 12px" }}
            >
              <FolderPlus size={13} />
              <span>Load 3 Workload Presets</span>
            </button>
          </div>
        </div>

        {/* Dataset Staging Pills */}
        <div
          style={{
            display: "flex",
            gap: "8px",
            flexWrap: "wrap",
            alignItems: "center",
          }}
        >
          {stagedDatasets.map((d) => {
            const isActive = activeDatasetId === d.id;
            return (
              <div
                key={d.id}
                onClick={() => {
                  setActiveDatasetId(d.id);
                  executeBattleTournament(d.id);
                }}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "6px 12px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: "600",
                  cursor: "pointer",
                  background: isActive
                    ? "rgba(6, 182, 212, 0.2)"
                    : "rgba(255, 255, 255, 0.04)",
                  color: isActive ? "#67e8f9" : "var(--text-muted)",
                  border: isActive
                    ? "1px solid rgba(6, 182, 212, 0.5)"
                    : "1px solid rgba(255, 255, 255, 0.08)",
                  transition: "all 0.2s ease",
                }}
              >
                <span
                  style={{
                    width: "7px",
                    height: "7px",
                    borderRadius: "50%",
                    background: isActive ? "var(--accent-cyan)" : "#64748b",
                  }}
                />
                <span>{d.name}</span>
                {d.sizeKb ? (
                  <span style={{ fontSize: "10px", color: "var(--text-muted)" }}>({d.sizeKb} KB)</span>
                ) : null}
                {stagedDatasets.length > 1 && (
                  <button
                    onClick={(e) => removeStagedDataset(d.id, e)}
                    style={{
                      background: "transparent",
                      border: "none",
                      color: "#94a3b8",
                      cursor: "pointer",
                      padding: "0 2px",
                      display: "flex",
                      alignItems: "center",
                    }}
                    title="Remove dataset"
                  >
                    ×
                  </button>
                )}
              </div>
            );
          })}
        </div>

        {/* Current Active Dataset Summary Strip */}
        {battleData?.datasetSummary && (
          <div
            style={{
              display: "grid",
              gridTemplateColumns: "repeat(auto-fit, minmax(130px, 1fr))",
              gap: "8px",
              marginTop: "4px",
              padding: "10px 14px",
              borderRadius: "6px",
              background: "rgba(0, 0, 0, 0.35)",
              border: "1px solid rgba(255, 255, 255, 0.05)",
            }}
          >
            <div>
              <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>Series Window</div>
              <div style={{ fontSize: "13px", fontWeight: "700", fontFamily: "var(--font-mono)" }}>
                {battleData.datasetSummary.totalRows} days
              </div>
            </div>
            <div>
              <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>Date Range</div>
              <div style={{ fontSize: "12px", fontWeight: "700", fontFamily: "var(--font-mono)", color: "#f8fafc" }}>
                {battleData.datasetSummary.dateRange}
              </div>
            </div>
            <div>
              <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>Hierarchy SKUs</div>
              <div style={{ fontSize: "13px", fontWeight: "700", color: "var(--accent-cyan)" }}>
                {battleData.datasetSummary.itemsCount} items / {battleData.datasetSummary.storesCount} stores
              </div>
            </div>
            <div>
              <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>Mean Daily Demand</div>
              <div style={{ fontSize: "13px", fontWeight: "700", color: "var(--accent-emerald)" }}>
                {battleData.datasetSummary.meanDailySales} units/day
              </div>
            </div>
            <div>
              <div style={{ fontSize: "10px", color: "var(--text-muted)", textTransform: "uppercase" }}>Aggregated Volume</div>
              <div style={{ fontSize: "13px", fontWeight: "700", color: "#f8fafc" }}>
                {battleData.datasetSummary.totalVolume} units
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 3. Combatant Selection & Model Configuration Bar */}
      <div
        className="glass-panel"
        style={{
          padding: "16px 20px",
          display: "flex",
          flexDirection: "column",
          gap: "12px",
          background: "rgba(15, 23, 42, 0.75)",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "10px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
            <Cpu size={16} color="var(--accent-violet)" />
            <span style={{ fontSize: "13px", fontWeight: "700" }}>
              Select Combatant Models ({selectedModels.length} Active):
            </span>
          </div>

          <div style={{ display: "flex", gap: "8px" }}>
            <button
              onClick={() => setShowConfigDrawer(!showConfigDrawer)}
              className="agent-btn"
              style={{
                fontSize: "11px",
                padding: "5px 12px",
                background: showConfigDrawer ? "rgba(139, 92, 246, 0.25)" : undefined,
                borderColor: showConfigDrawer ? "rgba(139, 92, 246, 0.6)" : undefined,
              }}
            >
              <Settings size={13} color="var(--accent-violet)" />
              <span>Configure Hyperparameters</span>
              {showConfigDrawer ? <ChevronUp size={13} /> : <ChevronDown size={13} />}
            </button>

            <button
              onClick={() => {
                setSelectedModels(["lightgbm", "ets", "s_naive", "naive", "moving_avg"]);
              }}
              className="agent-btn"
              style={{ fontSize: "11px", padding: "5px 10px" }}
            >
              Select All (5)
            </button>
          </div>
        </div>

        {/* Model Selection Checkbox Pills */}
        <div style={{ display: "flex", gap: "8px", flexWrap: "wrap" }}>
          {[
            { id: "lightgbm", name: "LightGBM (L1 WAPE)", color: "#06b6d4" },
            { id: "ets", name: "ETS Holt-Winters", color: "#8b5cf6" },
            { id: "s_naive", name: "Seasonal Naive (t-7)", color: "#f59e0b" },
            { id: "naive", name: "Naive (t-1)", color: "#94a3b8" },
            { id: "moving_avg", name: "Rolling 7-Day MA", color: "#ec4899" },
          ].map((m) => {
            const isSelected = selectedModels.includes(m.id);
            return (
              <button
                key={m.id}
                onClick={() => toggleModel(m.id)}
                style={{
                  display: "flex",
                  alignItems: "center",
                  gap: "6px",
                  padding: "5px 12px",
                  borderRadius: "6px",
                  fontSize: "12px",
                  fontWeight: "600",
                  cursor: "pointer",
                  background: isSelected
                    ? "rgba(255, 255, 255, 0.08)"
                    : "rgba(255, 255, 255, 0.02)",
                  color: isSelected ? "#f8fafc" : "#64748b",
                  border: isSelected
                    ? `1px solid ${m.color}`
                    : "1px solid rgba(255, 255, 255, 0.06)",
                  boxShadow: isSelected ? `0 0 10px ${m.color}33` : "none",
                  transition: "all 0.2s ease",
                }}
              >
                <span
                  style={{
                    width: "8px",
                    height: "8px",
                    borderRadius: "50%",
                    background: isSelected ? m.color : "#475569",
                  }}
                />
                <span>{m.name}</span>
                {isSelected && <Check size={12} color={m.color} />}
              </button>
            );
          })}
        </div>

        {/* 4. Model Hyperparameters & Configuration Panel (Collapsible) */}
        {showConfigDrawer && (
          <div
            style={{
              padding: "16px",
              borderRadius: "8px",
              background: "rgba(10, 15, 30, 0.8)",
              border: "1px solid rgba(139, 92, 246, 0.3)",
              display: "flex",
              flexDirection: "column",
              gap: "14px",
              marginTop: "4px",
            }}
          >
            <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
              <span style={{ fontSize: "12px", fontWeight: "700", color: "#c4b5fd" }}>
                ⚙️ Hyperparameter Tuning & Architecture Constraints:
              </span>
              <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
                Changes will take effect upon clicking "Launch Model Battle".
              </span>
            </div>

            <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(220px, 1fr))", gap: "14px" }}>
              {/* LightGBM Tuning */}
              <div
                style={{
                  padding: "12px",
                  borderRadius: "6px",
                  background: "rgba(6, 182, 212, 0.05)",
                  border: "1px solid rgba(6, 182, 212, 0.2)",
                }}
              >
                <div style={{ fontSize: "12px", fontWeight: "700", color: "var(--accent-cyan)", marginBottom: "8px" }}>
                  LightGBM Regressor
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  <div>
                    <label style={{ fontSize: "10px", color: "var(--text-muted)", display: "block" }}>Objective Loss:</label>
                    <select
                      value={modelConfigs.lightgbm?.objective || "l1"}
                      onChange={(e) =>
                        setModelConfigs({
                          ...modelConfigs,
                          lightgbm: { ...modelConfigs.lightgbm, objective: e.target.value as any },
                        })
                      }
                      style={{
                        width: "100%",
                        background: "rgba(0, 0, 0, 0.5)",
                        border: "1px solid rgba(255, 255, 255, 0.15)",
                        color: "#fff",
                        padding: "4px 8px",
                        borderRadius: "4px",
                        fontSize: "11px",
                      }}
                    >
                      <option value="l1">L1 Loss (MAE - Minimizes WAPE)</option>
                      <option value="l2">L2 Loss (MSE - Minimizes Variance)</option>
                      <option value="huber">Huber Loss (Outlier Robust)</option>
                    </select>
                  </div>

                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10px", color: "var(--text-muted)" }}>
                      <span>Num Leaves:</span>
                      <span style={{ color: "#fff", fontFamily: "var(--font-mono)" }}>{modelConfigs.lightgbm?.numLeaves || 31}</span>
                    </div>
                    <input
                      type="range"
                      min="15"
                      max="63"
                      step="4"
                      value={modelConfigs.lightgbm?.numLeaves || 31}
                      onChange={(e) =>
                        setModelConfigs({
                          ...modelConfigs,
                          lightgbm: { ...modelConfigs.lightgbm, numLeaves: parseInt(e.target.value) },
                        })
                      }
                      style={{ width: "100%", accentColor: "var(--accent-cyan)" }}
                    />
                  </div>

                  <div>
                    <div style={{ display: "flex", justifyContent: "space-between", fontSize: "10px", color: "var(--text-muted)" }}>
                      <span>Learning Rate:</span>
                      <span style={{ color: "#fff", fontFamily: "var(--font-mono)" }}>{modelConfigs.lightgbm?.learningRate || 0.05}</span>
                    </div>
                    <input
                      type="range"
                      min="0.01"
                      max="0.20"
                      step="0.01"
                      value={modelConfigs.lightgbm?.learningRate || 0.05}
                      onChange={(e) =>
                        setModelConfigs({
                          ...modelConfigs,
                          lightgbm: { ...modelConfigs.lightgbm, learningRate: parseFloat(e.target.value) },
                        })
                      }
                      style={{ width: "100%", accentColor: "var(--accent-cyan)" }}
                    />
                  </div>
                </div>
              </div>

              {/* ETS Holt-Winters Tuning */}
              <div
                style={{
                  padding: "12px",
                  borderRadius: "6px",
                  background: "rgba(139, 92, 246, 0.05)",
                  border: "1px solid rgba(139, 92, 246, 0.2)",
                }}
              >
                <div style={{ fontSize: "12px", fontWeight: "700", color: "#c4b5fd", marginBottom: "8px" }}>
                  ETS Holt-Winters
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  <div>
                    <label style={{ fontSize: "10px", color: "var(--text-muted)", display: "block" }}>Seasonal Cycle ($s$):</label>
                    <select
                      value={modelConfigs.ets?.seasonalPeriod || 7}
                      onChange={(e) =>
                        setModelConfigs({
                          ...modelConfigs,
                          ets: { ...modelConfigs.ets, seasonalPeriod: parseInt(e.target.value) },
                        })
                      }
                      style={{
                        width: "100%",
                        background: "rgba(0, 0, 0, 0.5)",
                        border: "1px solid rgba(255, 255, 255, 0.15)",
                        color: "#fff",
                        padding: "4px 8px",
                        borderRadius: "4px",
                        fontSize: "11px",
                      }}
                    >
                      <option value="7">7 Days (Weekly Retail Pattern)</option>
                      <option value="14">14 Days (Bi-weekly Pay Cycle)</option>
                      <option value="28">28 Days (Monthly Seasonality)</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: "10px", color: "var(--text-muted)", display: "block" }}>Trend Type:</label>
                    <select
                      value={modelConfigs.ets?.trendType || "additive"}
                      onChange={(e) =>
                        setModelConfigs({
                          ...modelConfigs,
                          ets: { ...modelConfigs.ets, trendType: e.target.value as any },
                        })
                      }
                      style={{
                        width: "100%",
                        background: "rgba(0, 0, 0, 0.5)",
                        border: "1px solid rgba(255, 255, 255, 0.15)",
                        color: "#fff",
                        padding: "4px 8px",
                        borderRadius: "4px",
                        fontSize: "11px",
                      }}
                    >
                      <option value="additive">Additive Trend</option>
                      <option value="multiplicative">Multiplicative Trend</option>
                      <option value="none">No Trend (Level Only)</option>
                    </select>
                  </div>

                  <div style={{ display: "flex", alignItems: "center", gap: "6px", marginTop: "4px" }}>
                    <input
                      type="checkbox"
                      id="damped"
                      checked={modelConfigs.ets?.damped || false}
                      onChange={(e) =>
                        setModelConfigs({
                          ...modelConfigs,
                          ets: { ...modelConfigs.ets, damped: e.target.checked },
                        })
                      }
                    />
                    <label htmlFor="damped" style={{ fontSize: "11px", color: "var(--text-muted)", cursor: "pointer" }}>
                      Enable Damped Trend ($\phi \approx 0.98$)
                    </label>
                  </div>
                </div>
              </div>

              {/* Baselines Tuning */}
              <div
                style={{
                  padding: "12px",
                  borderRadius: "6px",
                  background: "rgba(245, 158, 11, 0.05)",
                  border: "1px solid rgba(245, 158, 11, 0.2)",
                }}
              >
                <div style={{ fontSize: "12px", fontWeight: "700", color: "#fcd34d", marginBottom: "8px" }}>
                  Baselines & Primary Metric
                </div>
                <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                  <div>
                    <label style={{ fontSize: "10px", color: "var(--text-muted)", display: "block" }}>Seasonal Naive Lag:</label>
                    <select
                      value={modelConfigs.s_naive?.cycleLag || 7}
                      onChange={(e) =>
                        setModelConfigs({
                          ...modelConfigs,
                          s_naive: { cycleLag: parseInt(e.target.value) },
                        })
                      }
                      style={{
                        width: "100%",
                        background: "rgba(0, 0, 0, 0.5)",
                        border: "1px solid rgba(255, 255, 255, 0.15)",
                        color: "#fff",
                        padding: "4px 8px",
                        borderRadius: "4px",
                        fontSize: "11px",
                      }}
                    >
                      <option value="7">Lag 7 ($t-7$ days)</option>
                      <option value="14">Lag 14 ($t-14$ days)</option>
                      <option value="28">Lag 28 ($t-28$ days)</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: "10px", color: "var(--text-muted)", display: "block" }}>Moving Average Window:</label>
                    <select
                      value={modelConfigs.moving_avg?.windowSize || 7}
                      onChange={(e) =>
                        setModelConfigs({
                          ...modelConfigs,
                          moving_avg: { windowSize: parseInt(e.target.value) },
                        })
                      }
                      style={{
                        width: "100%",
                        background: "rgba(0, 0, 0, 0.5)",
                        border: "1px solid rgba(255, 255, 255, 0.15)",
                        color: "#fff",
                        padding: "4px 8px",
                        borderRadius: "4px",
                        fontSize: "11px",
                      }}
                    >
                      <option value="3">3-Day Window</option>
                      <option value="7">7-Day Window</option>
                      <option value="14">14-Day Window</option>
                      <option value="28">28-Day Window</option>
                    </select>
                  </div>

                  <div>
                    <label style={{ fontSize: "10px", color: "var(--text-muted)", display: "block" }}>Tournament Primary Metric:</label>
                    <select
                      value={modelConfigs.primaryMetric || "wape"}
                      onChange={(e) =>
                        setModelConfigs({
                          ...modelConfigs,
                          primaryMetric: e.target.value as any,
                        })
                      }
                      style={{
                        width: "100%",
                        background: "rgba(0, 0, 0, 0.5)",
                        border: "1px solid rgba(255, 255, 255, 0.15)",
                        color: "#fff",
                        padding: "4px 8px",
                        borderRadius: "4px",
                        fontSize: "11px",
                      }}
                    >
                      <option value="wape">WAPE (Weighted Absolute % Error)</option>
                      <option value="mae">MAE (Mean Absolute Error)</option>
                      <option value="rmse">RMSE (Root Mean Squared Error)</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* 5. EXPLICIT "START MODEL BATTLE" ACTION BAR */}
      <div
        className="glass-panel"
        style={{
          padding: "16px 20px",
          background: "linear-gradient(135deg, rgba(30, 27, 75, 0.8), rgba(15, 23, 42, 0.95))",
          border: "1px solid rgba(99, 102, 241, 0.5)",
          boxShadow: "0 0 20px rgba(99, 102, 241, 0.2)",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          flexWrap: "wrap",
          gap: "14px",
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
          <div
            style={{
              padding: "10px",
              borderRadius: "8px",
              background: "rgba(99, 102, 241, 0.2)",
              color: "#c7d2fe",
            }}
          >
            <Flame size={20} color="#818cf8" />
          </div>
          <div>
            <div style={{ fontSize: "14px", fontWeight: "800", color: "#f8fafc" }}>
              Ready to Battle: {selectedModels.length} Models on {stagedDatasets.length} Dataset(s)
            </div>
            <div style={{ fontSize: "11px", color: "#a5b4fc" }}>
              Active Dataset: <strong style={{ color: "#fff" }}>{battleData?.datasetSummary?.name || stagedDatasets[0]?.name}</strong>
            </div>
          </div>
        </div>

        <button
          onClick={() => executeBattleTournament()}
          disabled={isLoading}
          style={{
            padding: "10px 24px",
            borderRadius: "8px",
            fontSize: "13px",
            fontWeight: "800",
            cursor: isLoading ? "not-allowed" : "pointer",
            background: "linear-gradient(135deg, #6366f1, #8b5cf6)",
            color: "#fff",
            border: "none",
            boxShadow: "0 0 20px rgba(99, 102, 241, 0.6)",
            display: "flex",
            alignItems: "center",
            gap: "8px",
            transition: "all 0.2s ease",
            opacity: isLoading ? 0.7 : 1,
          }}
        >
          {isLoading ? (
            <>
              <RefreshCw size={15} className="spin" />
              <span>Running Tournament...</span>
            </>
          ) : (
            <>
              <Swords size={16} />
              <span>⚔️ Launch Model Battle Tournament</span>
            </>
          )}
        </button>
      </div>

      {/* 6. Datadog Trace Log Console Ticker */}
      <div
        style={{
          padding: "8px 14px",
          borderRadius: "6px",
          background: "rgba(0, 0, 0, 0.6)",
          border: "1px solid rgba(255, 255, 255, 0.06)",
          fontFamily: "var(--font-mono)",
          fontSize: "10px",
          color: "#94a3b8",
          display: "flex",
          justifyContent: "space-between",
          alignItems: "center",
          overflowX: "auto",
        }}
      >
        <div style={{ display: "flex", gap: "8px", alignItems: "center" }}>
          <span style={{ color: "var(--accent-cyan)", fontWeight: "700" }}>DATADOG TRACE:</span>
          <span>{battleLogs[battleLogs.length - 1] || "Listening for tournament execution..."}</span>
        </div>
        <span style={{ color: "#64748b" }}>{battleLogs.length} events logged</span>
      </div>

      {/* 7. Champion Banner */}
      {battleData?.champion && (
        <div
          className="glass-panel"
          style={{
            padding: "16px 20px",
            background: "linear-gradient(135deg, rgba(6, 182, 212, 0.12), rgba(16, 185, 129, 0.08))",
            border: "1px solid rgba(6, 182, 212, 0.4)",
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "12px",
          }}
        >
          <div style={{ display: "flex", alignItems: "center", gap: "14px" }}>
            <div
              style={{
                width: "44px",
                height: "44px",
                borderRadius: "50%",
                background: "rgba(6, 182, 212, 0.2)",
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                border: "1px solid rgba(6, 182, 212, 0.5)",
                boxShadow: "0 0 15px rgba(6, 182, 212, 0.4)",
              }}
            >
              <Trophy size={22} color="var(--accent-cyan)" />
            </div>
            <div>
              <div style={{ fontSize: "11px", color: "var(--accent-cyan)", fontWeight: "700", textTransform: "uppercase" }}>
                🏆 Tournament Winner ({battleData.datasetSummary?.name})
              </div>
              <div style={{ fontSize: "16px", fontWeight: "800", color: "#f8fafc" }}>
                {battleData.champion.name}
              </div>
              <div style={{ fontSize: "12px", color: "var(--text-muted)", marginTop: "2px" }}>
                Achieved <strong style={{ color: "var(--accent-emerald)" }}>{(battleData.champion.wape * 100).toFixed(2)}% WAPE</strong>{" "}
                (Beats Naive baseline by <strong style={{ color: "var(--accent-cyan)" }}>{Math.abs(battleData.champion.deltaVsNaive)}%</strong>) with{" "}
                <strong style={{ color: "#fff" }}>{battleData.champion.latencyP50} ms</strong> p50 inference latency.
              </div>
            </div>
          </div>

          <div style={{ display: "flex", gap: "8px" }}>
            <button
              onClick={handlePromoteChampion}
              className="agent-btn agent-btn-primary"
              style={{ fontSize: "12px", padding: "7px 14px" }}
            >
              <CheckCircle2 size={14} />
              <span>Promote to Champion</span>
            </button>

            <button
              onClick={handleAnalyzeWithAgent}
              className="agent-btn"
              style={{ fontSize: "12px", padding: "7px 14px" }}
            >
              <Sparkles size={14} color="var(--accent-violet)" />
              <span>Ask Sentinel RCA</span>
            </button>
          </div>
        </div>
      )}

      {/* 8. Dense Datadog Telemetry Scorecard Table */}
      <div
        className="glass-panel"
        style={{
          padding: "18px 20px",
          display: "flex",
          flexDirection: "column",
          gap: "12px",
        }}
      >
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center" }}>
          <div>
            <h3 style={{ fontSize: "14px", fontWeight: "700", margin: 0 }}>
              Live Model Leaderboard & Telemetry Matrix
            </h3>
            <p style={{ fontSize: "11px", color: "var(--text-muted)", margin: "2px 0 0 0" }}>
              Ranked by {modelConfigs.primaryMetric?.toUpperCase() || "Test WAPE"} (Weighted Absolute Percentage Error - Lower is Better)
            </p>
          </div>
          <span style={{ fontSize: "11px", color: "var(--text-muted)", fontFamily: "var(--font-mono)" }}>
            Tested Combinations: {battleData?.models?.length || selectedModels.length} Models
          </span>
        </div>

        <div style={{ overflowX: "auto" }}>
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
                  borderBottom: "1px solid rgba(255, 255, 255, 0.1)",
                  color: "var(--text-muted)",
                  fontSize: "10px",
                  textTransform: "uppercase",
                  letterSpacing: "0.05em",
                }}
              >
                <th style={{ padding: "8px 10px" }}>Rank</th>
                <th style={{ padding: "8px 10px" }}>Model Architecture</th>
                <th style={{ padding: "8px 10px" }}>Category</th>
                <th style={{ padding: "8px 10px", textAlign: "right" }}>WAPE (Error)</th>
                <th style={{ padding: "8px 10px", textAlign: "right" }}>Bias</th>
                <th style={{ padding: "8px 10px", textAlign: "right" }}>MAE</th>
                <th style={{ padding: "8px 10px", textAlign: "right" }}>RMSE</th>
                <th style={{ padding: "8px 10px", textAlign: "right" }}>p50 Latency</th>
                <th style={{ padding: "8px 10px", textAlign: "right" }}>Throughput</th>
                <th style={{ padding: "8px 10px", textAlign: "right" }}>vs. Baseline</th>
                <th style={{ padding: "8px 10px", textAlign: "center" }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {battleData?.models.map((m) => (
                <tr
                  key={m.id}
                  style={{
                    borderBottom: "1px solid rgba(255, 255, 255, 0.05)",
                    background: m.isChampion ? "rgba(6, 182, 212, 0.05)" : "transparent",
                  }}
                >
                  <td style={{ padding: "10px", fontWeight: "700" }}>
                    {m.rank === 1 ? (
                      <span style={{ color: "var(--accent-cyan)" }}>🥇 #1</span>
                    ) : m.rank === 2 ? (
                      <span style={{ color: "#94a3b8" }}>🥈 #2</span>
                    ) : m.rank === 3 ? (
                      <span style={{ color: "#f59e0b" }}>🥉 #3</span>
                    ) : (
                      <span style={{ color: "#64748b" }}>#{m.rank}</span>
                    )}
                  </td>
                  <td style={{ padding: "10px" }}>
                    <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
                      <span
                        style={{
                          width: "3px",
                          height: "14px",
                          borderRadius: "2px",
                          background: m.color,
                        }}
                      />
                      <span style={{ fontWeight: m.isChampion ? "700" : "500" }}>{m.name}</span>
                    </div>
                  </td>
                  <td style={{ padding: "10px", color: "var(--text-muted)", fontSize: "11px" }}>
                    {m.category}
                  </td>
                  <td
                    style={{
                      padding: "10px",
                      textAlign: "right",
                      fontFamily: "var(--font-mono)",
                      fontWeight: "700",
                      color: m.isChampion ? "var(--accent-emerald)" : "#f8fafc",
                    }}
                  >
                    {(m.wape * 100).toFixed(2)}%
                  </td>
                  <td
                    style={{
                      padding: "10px",
                      textAlign: "right",
                      fontFamily: "var(--font-mono)",
                      color: Math.abs(m.bias) <= 0.03 ? "var(--accent-emerald)" : "#cbd5e1",
                    }}
                  >
                    {m.bias >= 0 ? `+${(m.bias * 100).toFixed(2)}%` : `${(m.bias * 100).toFixed(2)}%`}
                  </td>
                  <td style={{ padding: "10px", textAlign: "right", fontFamily: "var(--font-mono)" }}>
                    {m.mae}
                  </td>
                  <td style={{ padding: "10px", textAlign: "right", fontFamily: "var(--font-mono)" }}>
                    {m.rmse}
                  </td>
                  <td
                    style={{
                      padding: "10px",
                      textAlign: "right",
                      fontFamily: "var(--font-mono)",
                      fontWeight: "600",
                      color: m.latencyP50 < 10 ? "var(--accent-emerald)" : "var(--text-muted)",
                    }}
                  >
                    {m.latencyP50} ms
                  </td>
                  <td style={{ padding: "10px", textAlign: "right", fontFamily: "var(--font-mono)", fontSize: "11px" }}>
                    {m.throughputRps} RPS
                  </td>
                  <td
                    style={{
                      padding: "10px",
                      textAlign: "right",
                      fontFamily: "var(--font-mono)",
                      fontWeight: "700",
                      color: m.deltaVsNaive < 0 ? "var(--accent-emerald)" : "var(--text-muted)",
                    }}
                  >
                    {m.deltaVsNaive < 0 ? `${m.deltaVsNaive}%` : "Baseline"}
                  </td>
                  <td style={{ padding: "10px", textAlign: "center" }}>
                    {m.isChampion ? (
                      <span
                        style={{
                          fontSize: "10px",
                          fontWeight: "700",
                          padding: "2px 8px",
                          borderRadius: "4px",
                          background: "rgba(6, 182, 212, 0.2)",
                          color: "var(--accent-cyan)",
                          border: "1px solid rgba(6, 182, 212, 0.4)",
                        }}
                      >
                        CHAMPION
                      </span>
                    ) : (
                      <span
                        style={{
                          fontSize: "10px",
                          padding: "2px 6px",
                          borderRadius: "4px",
                          background: "rgba(255, 255, 255, 0.04)",
                          color: "#64748b",
                        }}
                      >
                        COMPARATOR
                      </span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>

      {/* 9. Cross-Dataset Multi-Workload Leaderboard (If > 1 Dataset) */}
      {battleData?.crossDatasetLeaderboard && battleData.crossDatasetLeaderboard.length > 0 && (
        <div
          className="glass-panel"
          style={{
            padding: "18px 20px",
            background: "rgba(15, 23, 42, 0.8)",
            border: "1px solid rgba(255, 255, 255, 0.08)",
          }}
        >
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "12px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <BarChart3 size={16} color="var(--accent-cyan)" />
              <h3 style={{ fontSize: "14px", fontWeight: "700", margin: 0 }}>
                Cross-Dataset Aggregate Matrix ({battleData.datasets.length} Datasets Averaged)
              </h3>
            </div>
            <span style={{ fontSize: "11px", color: "var(--text-muted)" }}>
              Average generalization metric across all uploaded CSVs
            </span>
          </div>

          <div style={{ display: "grid", gridTemplateColumns: "repeat(auto-fit, minmax(180px, 1fr))", gap: "10px" }}>
            {battleData.crossDatasetLeaderboard.map((item, idx) => (
              <div
                key={item.id}
                style={{
                  padding: "12px",
                  borderRadius: "6px",
                  background: idx === 0 ? "rgba(6, 182, 212, 0.1)" : "rgba(255, 255, 255, 0.03)",
                  border: idx === 0 ? "1px solid rgba(6, 182, 212, 0.3)" : "1px solid rgba(255, 255, 255, 0.05)",
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", marginBottom: "4px" }}>
                  <span style={{ fontSize: "11px", fontWeight: "700", color: item.color }}>
                    #{idx + 1} {item.name.split(" ")[0]}
                  </span>
                  {idx === 0 && (
                    <span style={{ fontSize: "9px", padding: "1px 6px", borderRadius: "10px", background: "rgba(6, 182, 212, 0.3)", color: "#fff" }}>
                      TOP
                    </span>
                  )}
                </div>
                <div style={{ fontSize: "16px", fontWeight: "800", fontFamily: "var(--font-mono)", color: "#f8fafc" }}>
                  {(item.avgWape * 100).toFixed(2)}% WAPE
                </div>
                <div style={{ fontSize: "11px", color: "var(--text-muted)", marginTop: "2px" }}>
                  Avg MAE: {item.avgMae} | Bias: {(item.avgBias * 100).toFixed(2)}%
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 10. Multi-Model Curve Overlay SVG Graph */}
      <div
        className="glass-panel"
        style={{
          padding: "18px 20px",
          display: "flex",
          flexDirection: "column",
          gap: "14px",
        }}
      >
        <div
          style={{
            display: "flex",
            justifyContent: "space-between",
            alignItems: "center",
            flexWrap: "wrap",
            gap: "10px",
          }}
        >
          <div>
            <h3 style={{ fontSize: "14px", fontWeight: "700", margin: 0 }}>
              Forecast Horizon Multi-Model Curve Overlay
            </h3>
            <p style={{ fontSize: "11px", color: "var(--text-muted)", margin: "2px 0 0 0" }}>
              Comparing actual observed retail demand against candidate model projections
            </p>
          </div>

          {/* Curve Visibility Toggles */}
          <div style={{ display: "flex", gap: "10px", flexWrap: "wrap", alignItems: "center" }}>
            <label style={{ fontSize: "11px", display: "flex", alignItems: "center", gap: "4px", cursor: "pointer" }}>
              <input
                type="checkbox"
                checked={visibleCurves.actual}
                onChange={() => toggleCurve("actual")}
              />
              <span style={{ color: "#fff", fontWeight: "600" }}>Actual Ground Truth (White)</span>
            </label>

            {selectedModels.includes("lightgbm") && (
              <label style={{ fontSize: "11px", display: "flex", alignItems: "center", gap: "4px", cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={visibleCurves.lightgbm}
                  onChange={() => toggleCurve("lightgbm")}
                />
                <span style={{ color: "#06b6d4", fontWeight: "600" }}>LightGBM (Cyan)</span>
              </label>
            )}

            {selectedModels.includes("ets") && (
              <label style={{ fontSize: "11px", display: "flex", alignItems: "center", gap: "4px", cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={visibleCurves.ets}
                  onChange={() => toggleCurve("ets")}
                />
                <span style={{ color: "#8b5cf6", fontWeight: "600" }}>ETS Holt-Winters (Purple)</span>
              </label>
            )}

            {selectedModels.includes("s_naive") && (
              <label style={{ fontSize: "11px", display: "flex", alignItems: "center", gap: "4px", cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={visibleCurves.s_naive}
                  onChange={() => toggleCurve("s_naive")}
                />
                <span style={{ color: "#f59e0b", fontWeight: "600" }}>Seasonal Naive (Amber)</span>
              </label>
            )}

            {selectedModels.includes("naive") && (
              <label style={{ fontSize: "11px", display: "flex", alignItems: "center", gap: "4px", cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={visibleCurves.naive}
                  onChange={() => toggleCurve("naive")}
                />
                <span style={{ color: "#94a3b8" }}>Naive (Slate)</span>
              </label>
            )}

            {selectedModels.includes("moving_avg") && (
              <label style={{ fontSize: "11px", display: "flex", alignItems: "center", gap: "4px", cursor: "pointer" }}>
                <input
                  type="checkbox"
                  checked={visibleCurves.moving_avg}
                  onChange={() => toggleCurve("moving_avg")}
                />
                <span style={{ color: "#ec4899" }}>Rolling MA (Pink)</span>
              </label>
            )}
          </div>
        </div>

        {/* SVG Container */}
        <div style={{ width: "100%", overflowX: "auto" }}>
          <svg
            viewBox={`0 0 ${svgWidth} ${svgHeight}`}
            style={{ width: "100%", height: "auto", display: "block" }}
          >
            {/* Grid Lines */}
            {[0, 0.25, 0.5, 0.75, 1].map((ratio, i) => {
              const yVal = minVal + ratio * (maxVal - minVal);
              const yPos = getY(yVal);
              return (
                <g key={i}>
                  <line
                    x1={padding.left}
                    y1={yPos}
                    x2={svgWidth - padding.right}
                    y2={yPos}
                    stroke="rgba(255, 255, 255, 0.08)"
                    strokeDasharray="3 3"
                  />
                  <text
                    x={padding.left - 8}
                    y={yPos + 3}
                    textAnchor="end"
                    fontSize="10"
                    fill="#64748b"
                    fontFamily="var(--font-mono)"
                  >
                    {Math.round(yVal)}
                  </text>
                </g>
              );
            })}

            {/* X-Axis Dates */}
            {points.map((p, idx) => {
              if (idx % Math.ceil(points.length / 8) !== 0 && idx !== points.length - 1) return null;
              const xPos = getX(idx);
              return (
                <text
                  key={idx}
                  x={xPos}
                  y={svgHeight - 12}
                  textAnchor="middle"
                  fontSize="9"
                  fill="#64748b"
                  fontFamily="var(--font-mono)"
                >
                  {p.date.slice(5)}
                </text>
              );
            })}

            {/* Moving Average Line */}
            {visibleCurves.moving_avg && (
              <path
                d={createLinePath((p) => p.moving_avg)}
                fill="none"
                stroke="#ec4899"
                strokeWidth="1.5"
                strokeDasharray="2 2"
                opacity="0.8"
              />
            )}

            {/* Naive Line */}
            {visibleCurves.naive && (
              <path
                d={createLinePath((p) => p.naive)}
                fill="none"
                stroke="#94a3b8"
                strokeWidth="1.5"
                strokeDasharray="4 4"
                opacity="0.7"
              />
            )}

            {/* Seasonal Naive Line */}
            {visibleCurves.s_naive && (
              <path
                d={createLinePath((p) => p.s_naive)}
                fill="none"
                stroke="#f59e0b"
                strokeWidth="2"
                strokeDasharray="5 3"
                opacity="0.9"
              />
            )}

            {/* ETS Holt-Winters Line */}
            {visibleCurves.ets && (
              <path
                d={createLinePath((p) => p.ets)}
                fill="none"
                stroke="#8b5cf6"
                strokeWidth="2.2"
                opacity="0.95"
              />
            )}

            {/* LightGBM Champion Line */}
            {visibleCurves.lightgbm && (
              <path
                d={createLinePath((p) => p.lightgbm)}
                fill="none"
                stroke="#06b6d4"
                strokeWidth="2.8"
                style={{ filter: "drop-shadow(0 0 6px rgba(6, 182, 212, 0.6))" }}
              />
            )}

            {/* Ground Truth Actual Observed Line */}
            {visibleCurves.actual && (
              <>
                <path
                  d={createLinePath((p) => p.actual)}
                  fill="none"
                  stroke="#ffffff"
                  strokeWidth="2"
                  opacity="0.9"
                />
                {points.map((p, idx) => (
                  <circle
                    key={idx}
                    cx={getX(idx)}
                    cy={getY(p.actual)}
                    r="3.5"
                    fill="#0f172a"
                    stroke="#ffffff"
                    strokeWidth="1.5"
                  />
                ))}
              </>
            )}
          </svg>
        </div>
      </div>
    </div>
  );
};
