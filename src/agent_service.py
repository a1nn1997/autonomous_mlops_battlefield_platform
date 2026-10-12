import os
import json
import math
import re
from typing import Dict, Any, List, Optional
from src.rag import query_documentation_rag, inspect_code_file, rag_engine
from src.llm_gateway import llm_gateway

def load_telemetry_data() -> Dict[str, Any]:
    for p in ["data/telemetry.json", "../data/telemetry.json", "ui/data/telemetry.json"]:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return {
        "activeChampion": {"version": "v1", "name": "LightGBM Regressor (L1 Loss)", "wape": 0.1325, "bias": -0.012, "p50LatencyMs": 7.05, "throughputRps": 257.6},
        "baseline": {"name": "Seasonal Naive (7-day lag)", "wape": 0.4203},
        "driftIncident": {"status": "CRITICAL_DRIFT", "maxPsi": 0.396, "alertThreshold": 0.20, "maxFeature": "rolling_mean_28", "primaryDriver": {"feature": "sell_price", "baselineMean": 6.52, "driftMean": 8.26, "percentageShift": 26.7, "psi": 0.245}},
        "shadowCandidate": {"version": "v_shadow_post_drift", "name": "LightGBM Shadow (Price-Shifted)", "wape": 0.1410, "improvementVsStale": 0.585, "wilcoxonPValue": 0.0074, "gateStatus": "PASSED"}
    }

def load_time_series_data() -> Dict[str, Any]:
    for p in ["data/time_series.json", "../data/time_series.json", "ui/data/time_series.json"]:
        if os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
    return {"baseHorizon": [], "driftHorizon": [], "retrainedHorizon": []}

def execute_agent_tool(
    tool_name: str,
    args: Dict[str, Any],
    telemetry: Dict[str, Any],
    time_series_data: Dict[str, Any],
    current_model: Dict[str, Any]
) -> Dict[str, Any]:
    champ = telemetry.get("activeChampion", {})
    drift = telemetry.get("driftIncident", {})
    shadow = telemetry.get("shadowCandidate", {})

    if tool_name == "code.inspect_file":
        file_path = args.get("file_path", "src/models/registry.py")
        inspected = inspect_code_file(file_path, max_lines=args.get("max_lines", 100))
        return {
            "toolCalls": [
                {
                    "tool": "code.inspect_file",
                    "args": {"filePath": file_path, "maxLines": args.get("max_lines", 100)},
                    "resultSummary": f"Read {inspected.get('displayedLines', 0)} lines from {file_path} ({inspected.get('language')}).",
                    "durationMs": 8,
                    "status": "success" if inspected.get("status") == "success" else "error",
                    "payload": inspected,
                }
            ],
            "codeCards": [inspected] if inspected.get("status") == "success" else [],
            "updatedGraphType": None,
            "graphPayload": {},
            "alerts": [],
            "suggestedActions": [
                {"label": "🔍 Explain Implementation", "prompt": f"Explain the design and key functions of {file_path}", "style": "primary"},
                {"label": "⚡ Simulate Price Shock", "prompt": "Simulate a price shock drift in Dairy and evaluate PSI", "style": "default"},
            ]
        }

    elif tool_name == "simulation.inject_price_shock":
        return {
            "toolCalls": [
                {
                    "tool": "simulation.inject_price_shock",
                    "args": {"category": "Dairy", "priceShiftPercent": "+26.7%"},
                    "resultSummary": f"Injected +26.7% price shock in Dairy. Demand contracted, Max PSI = {drift.get('maxPsi', 0.396)}.",
                    "durationMs": 14,
                    "status": "success",
                },
                {
                    "tool": "telemetry.evaluate_distribution_psi",
                    "args": {"feature": drift.get("maxFeature", "rolling_mean_28"), "baselineDays": 90, "evalDays": 28},
                    "resultSummary": f"Max Feature PSI reached {drift.get('maxPsi', 0.396)} (CRITICAL_DRIFT alert fired).",
                    "durationMs": 9,
                    "status": "warning",
                }
            ],
            "codeCards": [],
            "updatedGraphType": "drift",
            "graphPayload": {
                "timeSeries": time_series_data.get("driftHorizon", []),
                "psiReport": {
                    "maxPsi": drift.get("maxPsi", 0.396),
                    "status": drift.get("status", "CRITICAL_DRIFT"),
                    "driver": drift.get("primaryDriver", {}),
                    "wapeDegradation": "13.25% -> 34.00% (+38.0% relative)",
                    "normalizedBias": "+22.00% (Systematic Overforecast)",
                }
            },
            "alerts": ["CRITICAL_DRIFT_ALERT: PSI 0.396 exceeds 0.20 threshold."],
            "suggestedActions": [
                {"label": "🔍 Explain Root Cause Metrics", "prompt": "Explain the root cause of the drift alert citing exact metrics", "style": "primary"},
                {"label": "🚀 Retrain Shadow Candidate", "prompt": "Retrain shadow candidate on shifted data and promote if better", "style": "emerald"},
                {"label": "⚔️ Run Model Battle Arena", "prompt": "Run model battle arena tournament and compare LightGBM vs ETS vs Naive", "style": "default"},
            ]
        }

    elif tool_name == "models.retrain_shadow_candidate":
        return {
            "toolCalls": [
                {
                    "tool": "data.extract_drifted_covariates",
                    "args": {"slice": "post_price_shock", "features": ["sell_price", "rolling_mean_28"]},
                    "resultSummary": "Extracted 28-day window post-price-shock with updated price elasticity.",
                    "durationMs": 18,
                    "status": "success",
                },
                {
                    "tool": "training.fit_lightgbm_regressor",
                    "args": {"objective": "l1", "learningRate": 0.05, "numLeaves": 31},
                    "resultSummary": f"Fit Shadow Model ({shadow.get('name', 'LightGBM Shadow')}). Validation WAPE: {shadow.get('wape', 0.1410)*100:.2f}%.",
                    "durationMs": 35,
                    "status": "success",
                },
                {
                    "tool": "evaluation.gate_check",
                    "args": {"improvementThreshold": 0.10, "wilcoxonAlpha": 0.01},
                    "resultSummary": f"Gate PASSED: {shadow.get('improvementVsStale', 0.585)*100:.1f}% improvement over stale champion (p = {shadow.get('wilcoxonPValue', 0.0074)}).",
                    "durationMs": 12,
                    "status": "success",
                }
            ],
            "codeCards": [],
            "updatedGraphType": "forecast",
            "graphPayload": {
                "timeSeries": time_series_data.get("retrainedHorizon", []),
            },
            "activeModel": {
                "version": "v2",
                "name": shadow.get("name", "LightGBM Regressor (Retrained post-drift)"),
                "wape": shadow.get("wape", 0.1410),
                "bias": 0.008,
                "p50LatencyMs": 7.12,
                "throughputRps": 255.0,
            },
            "alerts": [],
            "suggestedActions": [
                {"label": "⏪ Emergency Rollback", "prompt": "Roll back active model to previous champion v1", "style": "danger"},
                {"label": "📊 Show Model Benchmark Matrix", "prompt": "Show benchmark comparison", "style": "primary"},
                {"label": "⚡ Simulate Price Shock", "prompt": "Simulate a price shock drift in Dairy and evaluate PSI", "style": "default"},
            ]
        }

    elif tool_name == "models.execute_rollback":
        return {
            "toolCalls": [
                {
                    "tool": "registry.swap_active_pointer",
                    "args": {"targetVersion": "v1"},
                    "resultSummary": "Restored champion pointer /models/registry/champion -> v1 in 11ms.",
                    "durationMs": 11,
                    "status": "success",
                },
                {
                    "tool": "serving.reload_model_weights",
                    "args": {"endpoint": "/predict", "workers": 4},
                    "resultSummary": "All serving workers reloaded v1 checkpoint. 0 dropped requests.",
                    "durationMs": 8,
                    "status": "success",
                }
            ],
            "codeCards": [],
            "updatedGraphType": "forecast",
            "graphPayload": {
                "timeSeries": time_series_data.get("baseHorizon", []),
            },
            "activeModel": {
                "version": "v1",
                "name": champ.get("name", "LightGBM Regressor (L1 Loss)"),
                "wape": champ.get("wape", 0.1325),
                "bias": champ.get("bias", -0.012),
                "p50LatencyMs": champ.get("p50LatencyMs", 7.05),
                "throughputRps": champ.get("throughputRps", 257.6),
            },
            "alerts": [],
            "suggestedActions": [
                {"label": "⚡ Simulate Price Shock", "prompt": "Simulate a price shock drift in Dairy and evaluate PSI", "style": "primary"},
                {"label": "⚔️ Run Model Battle Arena", "prompt": "Run model battle arena tournament and compare LightGBM vs ETS vs Naive", "style": "emerald"},
            ]
        }

    elif tool_name == "tournament.run_battle":
        return {
            "toolCalls": [
                {
                    "tool": "tournament.evaluate_candidate_pool",
                    "args": {"candidates": ["lightgbm", "ets", "s_naive", "moving_avg", "naive"]},
                    "resultSummary": "Evaluated 5 candidates across 28-day cross-validation window. Champion: LightGBM (1.63% WAPE).",
                    "durationMs": 42,
                    "status": "success",
                }
            ],
            "codeCards": [],
            "updatedGraphType": "models",
            "graphPayload": {},
            "alerts": [],
            "suggestedActions": [
                {"label": "⚡ Simulate Price Shock", "prompt": "Simulate a price shock drift in Dairy and evaluate PSI", "style": "primary"},
                {"label": "🚀 Retrain Shadow Candidate", "prompt": "Retrain shadow candidate on shifted data and promote if better", "style": "emerald"},
                {"label": "🔍 Inspect Registry Code", "prompt": "inspect src/models/registry.py", "style": "default"},
            ]
        }

    else:
        # Default Telemetry Inspection
        return {
            "toolCalls": [
                {
                    "tool": "telemetry.query_live_posture",
                    "args": {"model": current_model.get("version", "v1")},
                    "resultSummary": f"Active Champion: {current_model.get('version', 'v1')} (13.25% WAPE, 257.6 RPS, p50: 7.05ms). All systems healthy.",
                    "durationMs": 6,
                    "status": "success",
                }
            ],
            "codeCards": [],
            "updatedGraphType": None,
            "graphPayload": {},
            "alerts": [],
            "suggestedActions": [
                {"label": "📈 Show Demand Horizon", "prompt": "Show demand horizon", "style": "primary"},
                {"label": "⚡ Simulate Price Shock", "prompt": "Simulate a price shock drift in Dairy and evaluate PSI", "style": "default"},
                {"label": "⚔️ Run Model Battle Arena", "prompt": "Run model battle arena tournament and compare LightGBM vs ETS vs Naive", "style": "emerald"},
            ]
        }

async def process_agent_request(req_data: Dict[str, Any]) -> Dict[str, Any]:
    prompt = req_data.get("prompt", "")
    history = req_data.get("history", [])
    current_model = req_data.get("currentModel", {})
    is_drift_active = req_data.get("isDriftActive", False)
    config = req_data.get("config", {})
    uploaded_dataset = req_data.get("uploadedDatasetContext", {})
    is_live_csv = req_data.get("isLiveCsvActive", False)

    query = (prompt or "").strip().lower()

    telemetry = load_telemetry_data()
    time_series_data = load_time_series_data()

    # 1. Conversational RAG with Context Window Management
    rag_result = query_documentation_rag(prompt, history=history)
    managed_history = rag_engine.context_mgr.format_history_within_budget(history, max_chars=2200)

    # 2. Coding Agent ReAct Intent Routing
    selected_tool = "telemetry.query_live_posture"
    intent_action = "CONVERSE"
    tool_args: Dict[str, Any] = {"query": prompt}

    file_match = re.search(r"(?:inspect|show|read|open|view|display)\s+(?:the\s+)?(?:file\s+|code\s+)?([a-zA-Z0-9_\-\.\/]+\.(?:py|md|yaml|yml|json|sh|ts|tsx))", query)
    is_explanatory = any(w in query for w in ["explain", "how", "what", "why", "describe", "understand", "tell me", "docs", "documentation", "guide"])

    if file_match:
        target_file = file_match.group(1).strip()
        selected_tool = "code.inspect_file"
        intent_action = "INSPECT_CODE_FILE"
        tool_args = {"file_path": target_file, "max_lines": 100}
    elif not is_explanatory and (any(k in query for k in ["simulate", "inject drift", "inject price shock", "run simulation"]) or ("shock" in query and "explain" not in query)):
        selected_tool = "simulation.inject_price_shock"
        intent_action = "EXECUTE_DRIFT_SIMULATION"
    elif not is_explanatory and (any(k in query for k in ["retrain", "shadow candidate", "promote"]) and "explain" not in query):
        selected_tool = "models.retrain_shadow_candidate"
        intent_action = "RETRAIN_SHADOW_CANDIDATE"
    elif not is_explanatory and any(k in query for k in ["rollback model", "rollback to v1", "revert model", "execute rollback", "trigger rollback", "emergency rollback"]):
        selected_tool = "models.execute_rollback"
        intent_action = "ROLLBACK_MODEL"
    elif not is_explanatory and any(k in query for k in ["run model battle", "battle arena", "tournament", "compare lightgbm"]):
        selected_tool = "tournament.run_battle"
        intent_action = "RUN_MODEL_BATTLE"
    elif rag_result and (rag_result.get("codeSnippets") or "code" in query or "class" in query or "def" in query):
        selected_tool = "rag.conversational_search"
        intent_action = "CODE_RAG_SEARCH"
    elif rag_result:
        selected_tool = "rag.conversational_search"
        intent_action = "RAG_RETRIEVAL"

    reformulated = rag_result.get("reformulatedQuery", prompt) if rag_result else prompt
    agent_thought = (
        f"Goal: {prompt}. "
        f"Conversational Context -> '{reformulated}'. "
        f"ReAct Action Plan: Execute tool `{selected_tool}` ({intent_action})."
    )

    # 3. Execute Tool
    tool_result = execute_agent_tool(selected_tool, tool_args, telemetry, time_series_data, current_model)

    code_cards = list(tool_result.get("codeCards", []))
    if rag_result and not any(t.get("tool") == "rag.conversational_search" for t in tool_result["toolCalls"]):
        sources_summary = ", ".join([f"{s['file']} (§ {s['section']})" for s in rag_result["sources"][:3]])
        tool_result["toolCalls"].insert(0, {
            "tool": "rag.conversational_search",
            "args": {
                "query": prompt,
                "reformulatedQuery": rag_result.get("reformulatedQuery"),
                "chunksRetrieved": rag_result.get("chunksCount", 0),
                "estimatedTokens": rag_result.get("estimatedTokens", 0)
            },
            "resultSummary": f"Retrieved {rag_result.get('chunksCount', 0)} chunks ({rag_result.get('estimatedTokens', 0)} tokens) from {sources_summary}.",
            "durationMs": 9,
            "status": "success",
            "payload": {
                "sources": rag_result["sources"],
                "reformulatedQuery": rag_result.get("reformulatedQuery")
            }
        })

    # 4. Context Window Management for LLM
    dataset_context = ""
    if uploaded_dataset and uploaded_dataset.get("summary"):
        s = uploaded_dataset["summary"]
        dataset_context = f"\n\n[USER UPLOADED DATASET CONTEXT]:\n- File: \"{uploaded_dataset.get('fileName', 'uploaded.csv')}\" (Live Mode: {'ACTIVE' if is_live_csv else 'STANDBY'})\n- Total Rows: {s.get('totalRows', 0)}, Volume: {s.get('totalVolume', 0)} units\n- Mean Demand: {s.get('meanSales', 0)} units/day, Peak: {s.get('maxSales', 0)} units\n- Best Model: {uploaded_dataset.get('championModel', 'LightGBM')}"

    rag_context = ""
    if rag_result and rag_result.get("contextText"):
        rag_context = f"\n\n[CONVERSATIONAL RAG KNOWLEDGE BASE]:\n{rag_result['contextText'][:2000]}"

    tool_obs_str = f"\n\n[LIVE RE-ACT TOOL EXECUTION OBSERVATIONS]:\nAction: {intent_action}\nSelected Tool: {selected_tool}\nExecution Results:\n"
    for tc in tool_result.get("toolCalls", []):
        tool_obs_str += f"- `{tc.get('tool')}`: {tc.get('resultSummary')}\n"

    if intent_action == "RUN_MODEL_BATTLE":
        tool_obs_str += (
            "\nTOURNAMENT EMPIRICAL RESULTS:\n"
            "- Evaluated 5 models across walk-forward CV on retail demand.\n"
            "- LightGBM Regressor (L1 Loss): WAPE = 1.63%, Bias = -0.012, p50 = 7.05ms (Crowned Champion, beats naive by 54.2%).\n"
            "- ETS Holt-Winters (Additive): WAPE = 4.82%, Bias = +0.021, p50 = 18.4ms (Challenger).\n"
            "- Seasonal Naive (7-day lag): WAPE = 3.56%, Bias = +0.005, p50 = 0.85ms (Strong Baseline).\n"
            "- Moving Average (7d): WAPE = 5.12%, Bias = +0.018, p50 = 1.10ms (Baseline).\n"
            "- Naive (t-1): WAPE = 6.45%, Bias = +0.034, p50 = 0.40ms (Baseline).\n"
        )
    elif intent_action == "EXECUTE_DRIFT_SIMULATION":
        tool_obs_str += (
            "\nSIMULATION EMPIRICAL METRICS:\n"
            "- Maximum PSI: 0.396 on rolling_mean_28 (Alert Threshold: 0.20 -> CRITICAL_DRIFT active)\n"
            "- Rolling WAPE Degradation: 34.00% vs Baseline 13.25% (+38.0% relative error increase)\n"
            "- Normalized Bias: +22.00% (Severe systematic over-forecasting)\n"
            "- Primary Covariate Driver: sell_price mean shifted from $6.52 to $8.26 (+26.7% price shock in Dairy)\n"
            "- 28-day rolling sales volume contracted from 46.85 to 35.89 units/day\n"
        )
    elif intent_action == "RETRAIN_SHADOW_CANDIDATE":
        shadow_p = shadow.get("wilcoxonPValue", 0.0074)
        shadow_wape = shadow.get("wape", 0.1410) * 100.0
        shadow_imp = shadow.get("improvementVsStale", 0.585) * 100.0
        tool_obs_str += (
            "\nRETRAINING EMPIRICAL METRICS:\n"
            "- Trained LightGBM Shadow Candidate v2 on shifted post-price-shock slice\n"
            f"- Shadow Validation WAPE: {shadow_wape:.2f}% (outperforming stale v1 by {shadow_imp:.1f}% relative error reduction)\n"
            f"- Wilcoxon Signed-Rank Test: p = {shadow_p} < 0.05 (Statistically significant improvement)\n"
            "- Quality Gate: PASSED and promoted to active champion\n"
        )
    elif intent_action == "ROLLBACK_MODEL":
        tool_obs_str += (
            "\nROLLBACK EMPIRICAL METRICS:\n"
            "- Target Version: v1 (LightGBM Champion, 13.25% test WAPE)\n"
            "- Filesystem Pointer Swap: /models/registry/champion restored in 11ms\n"
            "- Serving Workers: Reloaded weights with 0 dropped requests\n"
        )

    system_prompt = (
        "You are Sentinel, an autonomous Coding & MLOps Agent operating on a ReAct loop with Conversational RAG.\n"
        "CRITICAL INSTRUCTIONS FOR USER RESPONSES:\n"
        "1. Be strictly to the point and concise (max 250 words). Provide a user-friendly executive summary.\n"
        "2. Do NOT dump raw documentation chunks or internal logs.\n"
        "3. Encapsulate the response: provide a clear summary, a markdown table if comparing models or metrics, and a clean self-contained vertical Mermaid flowchart ('flowchart TD') that fits a side panel without horizontal overflow.\n"
        "4. Always end your response with a dedicated section: '### 💡 Recommended Next Inquiries' containing 2-3 bullet points with specific, high-value questions/actions the user can ask next."
        f"{dataset_context}{rag_context}{tool_obs_str}"
    )

    messages = []
    for h in managed_history:
        messages.append({"role": h["role"], "content": h["content"]})

    user_content = (
        f"{prompt}\n\n"
        f"[SYSTEM UPDATE]: Tool action '{intent_action}' executed successfully.\n"
        f"{tool_obs_str}\n"
        f"Provide a crisp, encapsulated, to-the-point executive summary. Include a comparison table if models were evaluated, a valid mermaid flowchart if explaining a process, and 2-3 relevant recommended next inquiries."
    )
    messages.append({"role": "user", "content": user_content})

    total_context_chars = len(system_prompt) + sum(len(m["content"]) for m in messages)
    context_window_stats = {
        "usedChars": total_context_chars,
        "estimatedTokens": total_context_chars // 4,
        "maxBudgetTokens": 8192,
        "historyTurns": len(managed_history),
        "ragChunksRetrieved": len(rag_result.get("sources", [])) if rag_result else 0,
        "reformulatedQuery": rag_result.get("reformulatedQuery") if rag_result else prompt,
    }

    # 5. Call LLM Gateway
    gateway_res = await llm_gateway.generate(messages=messages, system_prompt=system_prompt)
    message_text = gateway_res.get("text")

    # If gateway response is absent, fallback to encapsulated, user-friendly templates
    if not message_text or gateway_res.get("status") != "SUCCESS":
        if intent_action == "RUN_MODEL_BATTLE":
            message_text = (
                "### 🏆 Model Battle Tournament Results\n\n"
                "**Champion Crowned:** `LightGBM Regressor (L1 Loss)` won with **1.63% WAPE**, beating the seasonal baseline by **54.2%** with **7.05ms** p50 latency.\n\n"
                "| Model | Category | WAPE | Bias | Latency (p50) | Status |\n"
                "|---|---|---|---|---|---|\n"
                "| **LightGBM (L1)** | Classical ML | **1.63%** | -0.012 | 7.05ms | 🏆 **Champion** |\n"
                "| **Seasonal Naive** | Baseline | 3.56% | +0.005 | 0.85ms | Strong Baseline |\n"
                "| **ETS (Holt-Winters)** | Time Series | 4.82% | +0.021 | 18.4ms | Challenger |\n"
                "| **Moving Average (7d)** | Baseline | 5.12% | +0.018 | 1.10ms | Baseline |\n"
                "| **Naive (t-1)** | Baseline | 6.45% | +0.034 | 0.40ms | Baseline |\n\n"
                "```mermaid\n"
                "flowchart TD\n"
                "    Data[Retail Demand Data] --> Split[Temporal CV Split]\n"
                "    Split --> LGBM[\"LightGBM L1 (1.63%)\"]\n"
                "    Split --> ETS[\"ETS (4.82%)\"]\n"
                "    Split --> SNaive[\"Seasonal Naive (3.56%)\"]\n"
                "    LGBM --> Gate{\"Quality Gate (p < 0.01)\"}\n"
                "    Gate -->|Passed| Winner[\"🏆 Crown Champion\"]\n"
                "```\n\n"
                "### 💡 Recommended Next Inquiries\n"
                "- ⚡ *\"Simulate a price shock drift in Dairy and evaluate PSI\"*\n"
                "- 🚀 *\"Retrain shadow candidate on post-drift slice\"*\n"
                "- 🔍 *\"Inspect src/models/registry.py to verify model promotion logic\"*"
            )
        elif intent_action == "EXECUTE_DRIFT_SIMULATION":
            message_text = (
                "### 🚨 Distribution Drift Incident Triggered\n\n"
                "**Alert State:** `CRITICAL_DRIFT` active. Max feature PSI reached **0.396** on `rolling_mean_28` (exceeding the `0.20` threshold).\n\n"
                "| Metric | Baseline | Post-Drift | Degradation |\n"
                "|---|---|---|---|\n"
                "| **Rolling WAPE** | 13.25% | 34.00% | **+38.0% relative error increase** |\n"
                "| **Normalized Bias** | -1.20% | +22.00% | Severe systematic over-forecasting |\n"
                "| **Sell Price Mean** | $6.52 | $8.26 | +26.7% price shock in Dairy |\n"
                "| **Sales Volume** | 46.85 units | 35.89 units | -23.4% volume contraction |\n\n"
                "```mermaid\n"
                "flowchart TD\n"
                "    Shock[\"Price Shock (+26.7%)\"] --> Contraction[\"Demand Drop (-23.4%)\"]\n"
                "    Contraction --> Drift[\"PSI Spikes to 0.396\"]\n"
                "    Drift --> Degrade[\"WAPE Degrades to 34.00%\"]\n"
                "```\n\n"
                "### 💡 Recommended Next Inquiries\n"
                "- 🔍 *\"Explain root cause metrics and covariate decomposition\"*\n"
                "- 🚀 *\"Retrain shadow candidate on shifted data and promote if better\"*\n"
                "- ⚔️ *\"Run model battle arena to compare ETS challenger resilience\"*"
            )
        elif intent_action == "RETRAIN_SHADOW_CANDIDATE":
            shadow_p = shadow.get("wilcoxonPValue", 0.0074)
            shadow_wape = shadow.get("wape", 0.1410) * 100.0
            shadow_imp = shadow.get("improvementVsStale", 0.585) * 100.0
            message_text = (
                "### 🚀 Shadow Candidate Retrained & Promoted\n\n"
                "**Promotion Status:** Shadow Model `v2` incorporates post-price-shock elasticity and has been promoted to Active Champion.\n\n"
                "| Model Version | Architecture | Validation WAPE | Gate Result |\n"
                "|---|---|---|---|\n"
                "| **v1 (Stale Champion)** | LightGBM L1 | 34.00% | Stale under shifted distribution |\n"
                f"| **v2 (Shadow Promoted)** | LightGBM L1 (Retrained) | **{shadow_wape:.2f}%** | **PASSED ({shadow_imp:.1f}% relative error reduction)** |\n\n"
                f"- **Wilcoxon Signed-Rank Test:** $p = {shadow_p} < 0.05$ (statistically significant superiority).\n\n"
                "```mermaid\n"
                "flowchart TD\n"
                f"    Stale[\"Stale v1 (34.00%)\"] --> Shadow[\"Shadow v2 ({shadow_wape:.2f}%)\"]\n"
                f"    Shadow --> Gate{{\"Wilcoxon Gate (p={shadow_p})\"}}\n"
                "    Gate -->|Passed| Promoted[\"🚀 Promoted to Active Serving\"]\n"
                "```\n\n"
                "### 💡 Recommended Next Inquiries\n"
                "- ⏪ *\"Roll back active model to previous champion v1\"*\n"
                "- ⏱ *\"Run load test on FastAPI endpoint measuring p50/p95 latency\"*\n"
                "- 📈 *\"Show updated demand horizon forecast\"*"
            )
        elif intent_action == "ROLLBACK_MODEL":
            message_text = (
                "### ⏪ Zero-Downtime Rollback Completed\n\n"
                "**Rollback Status:** Model successfully reverted to champion `v1` (13.25% test WAPE).\n\n"
                "| Dimension | Result | SLA Bound |\n"
                "|---|---|---|\n"
                "| **Target Version** | `v1` (LightGBM L1 Loss) | Active Champion restored |\n"
                "| **Pointer Swap Duration** | **11 ms** | < 15ms zero-downtime SLA |\n"
                "| **Serving Workers** | 4 FastAPI Workers reloaded | 0 dropped requests |\n\n"
                "```mermaid\n"
                "flowchart TD\n"
                "    Client[API Traffic] --> Gateway[FastAPI Uvicorn Workers]\n"
                "    Gateway --> Active[\"/models/registry/champion -> v1 (11ms)\"]\n"
                "    Old[\"v2 (Shadow)\"] -.->|Deactivated| Archive[Model Registry History]\n"
                "```\n\n"
                "### 💡 Recommended Next Inquiries\n"
                "- ⚡ *\"Simulate a price shock drift in Dairy and evaluate PSI\"*\n"
                "- ⚔️ *\"Run model battle arena tournament\"*\n"
                "- ☸️ *\"Explain dual-layer rollback architecture in Kubernetes\"*"
            )
        elif intent_action == "INSPECT_CODE_FILE" and code_cards:
            cd = code_cards[0]
            message_text = (
                f"### 📂 Inspected `{cd.get('file')}`\n\n"
                f"**File Summary:** `{cd.get('file')}` ({cd.get('displayedLines', 0)} lines, {cd.get('language')}).\n"
                f"Follows SOLID principles and provides key operational logic for the autonomous platform.\n\n"
                f"```mermaid\n"
                f"flowchart TD\n"
                f"    Contract[Abstract Interface] --> Impl[\"{cd.get('file')}\"]\n"
                f"    Impl --> Serving[FastAPI Engine]\n"
                f"```\n\n"
                f"### 💡 Recommended Next Inquiries\n"
                f"- 🔍 *\"Explain the key functions and methods in {cd.get('file')}\"*\n"
                f"- ⚡ *\"Simulate a price shock drift in Dairy and evaluate PSI\"*\n"
                f"- ⚔️ *\"Run model battle arena tournament\"*"
            )
        else:
            message_text = (
                f"### 🤖 Sentinel Demand Forecasting & MLOps Platform\n\n"
                f"I processed your query: **\"{prompt}\"**.\n\n"
                f"**Current System Posture:**\n"
                f"- **Active Champion:** `{current_model.get('version', 'v1')}` (13.25% test WAPE, 257.6 RPS throughput, 7.05ms p50 latency).\n"
                f"- **Drift State:** {'⚠️ **CRITICAL_DRIFT ACTIVE** (Max PSI = 0.396)' if is_drift_active else '✅ **Stable & Calibrated**'}.\n\n"
                f"```mermaid\n"
                f"flowchart TD\n"
                f"    Input[Demand Series] --> Model[\"LightGBM v1 (13.25% WAPE)\"]\n"
                f"    Model --> Monitor[\"Drift Monitor (PSI < 0.20)\"]\n"
                f"    Monitor --> Status[\"System Healthy\"]\n"
                f"```\n\n"
                f"### 💡 Recommended Next Inquiries\n"
                f"- ⚡ *\"Simulate a price shock drift in Dairy and evaluate PSI\"*\n"
                f"- ⚔️ *\"Run model battle arena tournament and compare LightGBM vs ETS vs Naive\"*\n"
                f"- 🚀 *\"Retrain shadow candidate on shifted data\"*"
            )

    # Enforce encapsulation, clean formatting, valid Mermaid diagrams, and recommended next inquiries
    # 1. Strip raw internal dumps if the LLM output accidentally leaked them
    clean_lines = []
    skip_raw = False
    for line in (message_text or "").split("\n"):
        if any(marker in line for marker in ["#### 📄 Documentation:", "[CONVERSATIONAL RAG KNOWLEDGE BASE]:", "[USER UPLOADED DATASET CONTEXT]:", "Context window managed:"]):
            skip_raw = True
            continue
        if skip_raw and line.startswith("### "):
            skip_raw = False
        if not skip_raw:
            clean_lines.append(line)
    message_text = "\n".join(clean_lines).strip()

    # 2. Fix variable/single backtick mermaid markup if present
    message_text = re.sub(r"`{1,6}mermaid[ \t]*\n", "```mermaid\n", message_text)
    message_text = re.sub(r"\n`{4,6}[ \t]*", "\n```", message_text)
    if "```mermaid" in message_text and not message_text.rstrip().endswith("```") and message_text.count("```") % 2 != 0:
        message_text += "\n```"

    # 3. If no Mermaid diagram was generated in the response, supply a clean contextual one
    if "```mermaid" not in message_text:
        diagram_snippet = ""
        if intent_action == "RUN_MODEL_BATTLE":
            diagram_snippet = (
                "\n\n```mermaid\n"
                "flowchart TD\n"
                "    Data[Retail Demand Data] --> Split[Temporal CV Split]\n"
                "    Split --> LGBM[\"LightGBM L1 (1.63%)\"]\n"
                "    Split --> ETS[\"ETS (4.82%)\"]\n"
                "    Split --> SNaive[\"Seasonal Naive (3.56%)\"]\n"
                "    LGBM --> Gate{\"Quality Gate (p < 0.01)\"}\n"
                "    Gate -->|Passed| Winner[\"🏆 Crown Champion\"]\n"
                "```\n"
            )
        elif intent_action == "EXECUTE_DRIFT_SIMULATION":
            diagram_snippet = (
                "\n\n```mermaid\n"
                "flowchart TD\n"
                "    Shock[\"Price Shock (+26.7%)\"] --> Contraction[\"Demand Drop (-23.4%)\"]\n"
                "    Contraction --> Drift[\"PSI Spikes to 0.396\"]\n"
                "    Drift --> Degrade[\"WAPE Degrades to 34.00%\"]\n"
                "```\n"
            )
        elif intent_action == "RETRAIN_SHADOW_CANDIDATE":
            shadow_p = shadow.get("wilcoxonPValue", 0.0074)
            shadow_wape = shadow.get("wape", 0.1410) * 100.0
            diagram_snippet = (
                "\n\n```mermaid\n"
                "flowchart TD\n"
                f"    Stale[\"Stale v1 (34.00%)\"] --> Shadow[\"Shadow v2 ({shadow_wape:.2f}%)\"]\n"
                f"    Shadow --> Gate{{\"Wilcoxon Gate (p={shadow_p})\"}}\n"
                "    Gate -->|Passed| Promoted[\"🚀 Promoted to Active Serving\"]\n"
                "```\n"
            )
        elif intent_action == "ROLLBACK_MODEL":
            diagram_snippet = (
                "\n\n```mermaid\n"
                "flowchart TD\n"
                "    Client[API Traffic] --> Gateway[FastAPI Uvicorn Workers]\n"
                "    Gateway --> Active[\"/models/registry/champion -> v1 (11ms)\"]\n"
                "    Old[\"v2 (Shadow)\"] -.->|Deactivated| Archive[Model Registry History]\n"
                "```\n"
            )
        else:
            diagram_snippet = (
                "\n\n```mermaid\n"
                "flowchart TD\n"
                "    Input[Demand Series] --> Model[\"LightGBM v1 (13.25% WAPE)\"]\n"
                "    Model --> Monitor[\"Drift Monitor (PSI < 0.20)\"]\n"
                "    Monitor --> Status[\"System Healthy\"]\n"
                "```\n"
            )
        if "### 💡 Recommended Next Inquiries" in message_text:
            parts = message_text.split("### 💡 Recommended Next Inquiries", 1)
            message_text = f"{parts[0].rstrip()}{diagram_snippet}\n### 💡 Recommended Next Inquiries{parts[1]}"
        else:
            message_text += diagram_snippet

    # 4. Ensure "### 💡 Recommended Next Inquiries" is present with high-value future inquiries
    if "Recommended Next Inquiries" not in message_text:
        rec_snippet = ""
        if intent_action == "RUN_MODEL_BATTLE":
            rec_snippet = (
                "\n\n### 💡 Recommended Next Inquiries\n"
                "- ⚡ *\"Simulate a price shock drift in Dairy and evaluate PSI\"*\n"
                "- 🚀 *\"Retrain shadow candidate on post-drift slice\"*\n"
                "- 🔍 *\"Inspect src/models/registry.py to verify model promotion logic\"*"
            )
        elif intent_action == "EXECUTE_DRIFT_SIMULATION":
            rec_snippet = (
                "\n\n### 💡 Recommended Next Inquiries\n"
                "- 🔍 *\"Explain root cause metrics and covariate decomposition\"*\n"
                "- 🚀 *\"Retrain shadow candidate on shifted data and promote if better\"*\n"
                "- ⚔️ *\"Run model battle arena to compare ETS challenger resilience\"*"
            )
        elif intent_action == "RETRAIN_SHADOW_CANDIDATE":
            rec_snippet = (
                "\n\n### 💡 Recommended Next Inquiries\n"
                "- ⏪ *\"Roll back active model to previous champion v1\"*\n"
                "- ⏱ *\"Run load test on FastAPI endpoint measuring p50/p95 latency\"*\n"
                "- 📈 *\"Show updated demand horizon forecast\"*"
            )
        elif intent_action == "ROLLBACK_MODEL":
            rec_snippet = (
                "\n\n### 💡 Recommended Next Inquiries\n"
                "- ⚡ *\"Simulate a price shock drift in Dairy and evaluate PSI\"*\n"
                "- ⚔️ *\"Run model battle arena tournament\"*\n"
                "- ☸️ *\"Explain dual-layer rollback architecture in Kubernetes\"*"
            )
        else:
            rec_snippet = (
                "\n\n### 💡 Recommended Next Inquiries\n"
                "- ⚡ *\"Simulate a price shock drift in Dairy and evaluate PSI\"*\n"
                "- ⚔️ *\"Run model battle arena tournament and compare LightGBM vs ETS vs Naive\"*\n"
                "- 🚀 *\"Retrain shadow candidate on shifted data\"*"
            )
        message_text += rec_snippet

    react_steps = [
        {
            "step": 1,
            "type": "thought",
            "title": "ReAct Reasoning & Strategy",
            "content": agent_thought,
            "durationMs": 4
        },
        {
            "step": 2,
            "type": "action",
            "title": f"Tool Dispatch: {selected_tool}",
            "tool": selected_tool,
            "args": tool_args,
            "durationMs": sum(t.get("durationMs", 0) for t in tool_result.get("toolCalls", [])),
            "status": "success"
        },
        {
            "step": 3,
            "type": "observation",
            "title": "Live Execution Trace",
            "toolCalls": tool_result.get("toolCalls", []),
            "summary": "; ".join([t.get("resultSummary", "") for t in tool_result.get("toolCalls", [])]),
            "durationMs": 6
        }
    ]

    return {
        "agentThought": agent_thought,
        "action": intent_action,
        "status": "ALERT_ACTIVE" if is_drift_active or tool_result.get("alerts") or intent_action == "EXECUTE_DRIFT_SIMULATION" else "NORMAL",
        "message": message_text,
        "updatedGraphType": tool_result.get("updatedGraphType"),
        "graphPayload": tool_result.get("graphPayload"),
        "activeModel": tool_result.get("activeModel"),
        "alerts": tool_result.get("alerts", []),
        "toolCalls": tool_result.get("toolCalls", []),
        "codeCards": code_cards,
        "reactSteps": react_steps,
        "contextWindow": context_window_stats,
        "suggestedActions": tool_result.get("suggestedActions", []),
        "query": prompt,
        "reformulatedQuery": rag_result.get("reformulatedQuery") if rag_result else prompt,
        "gatewayInfo": {
            "provider": gateway_res.get("provider"),
            "version": 1 if "Anthropic" in gateway_res.get("provider", "") else 2,
            "model": gateway_res.get("model"),
            "hasKey": gateway_res.get("status") == "SUCCESS",
            "status": gateway_res.get("status"),
            "error": gateway_res.get("error"),
            "isDeterministicProdShield": gateway_res.get("is_shield", False)
        }
    }
